"""
学期切换脚本 - 开学前手动执行一次（幂等可重跑）

用法:
    cd backend
    python scripts/semester_rollover.py [--disable-graduates 名单.txt] [--old-term 2025-2026-2]

流程:
    1. 前置检查（当前学期配置、库内 semester 分布）
    2. 快照备份（pg_dump 到 backups/）
    3. 收敛遗留课堂（旧学期 active/scheduled -> ended）
    4. 收敛小组（is_active=False；遗留 evaluating 任务 -> closed）
    5. 分数归档重置（每生写归档 score_log + score 置 0，单事务）
    6. 可选软禁用毕业/退学学生
    7. 输出验证报告
"""
import argparse
import os
import subprocess
import sys
from datetime import datetime
from typing import Optional, Tuple

# 保证以 backend 为工作目录运行时能 import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, func, select, update

from app.core.config import get_settings
from app.core.db import engine
from app.core.term import get_current_term
from app.models import (
    CourseSchedule,
    CourseSession,
    Group,
    GroupTask,
    ScoreLog,
    Student,
)

ARCHIVE_REASON_PREFIX = "[学期归档]"


def _archive_scores(session: Session, old_term: str) -> Tuple[int, int]:
    """分数归档重置：每生写一条归档 score_log 并把 score 置 0（幂等）

    Returns:
        (归档人数, 跳过人数) - 已存在归档记录的学生跳过
    """
    students = session.exec(select(Student)).all()
    archived = 0
    skipped = 0

    for student in students:
        existing = session.exec(
            select(ScoreLog).where(
                ScoreLog.student_id == student.student_id,
                ScoreLog.reason == f"{ARCHIVE_REASON_PREFIX} {old_term}",
            )
        ).first()
        if existing:
            skipped += 1
            continue

        session.add(ScoreLog(
            student_id=student.student_id,
            old_score=student.score,
            new_score=0.0,
            delta=-student.score,
            reason=f"{ARCHIVE_REASON_PREFIX} {old_term}",
            operator="system",
            semester=old_term,
        ))
        student.score = 0.0
        session.add(student)
        archived += 1

    session.commit()
    return archived, skipped


def _close_legacy_sessions(session: Session, old_term: str) -> int:
    """旧学期遗留 active/scheduled 课堂 -> ended"""
    result = session.exec(
        update(CourseSession)
        .where(
            CourseSession.semester == old_term,
            CourseSession.status.in_(["active", "scheduled"]),
        )
        .values(status="ended")
    )
    session.commit()
    return result.rowcount


def _close_legacy_groups(session: Session, old_term: str) -> Tuple[int, int]:
    """旧学期小组失效；遗留 evaluating 任务 -> closed"""
    groups_result = session.exec(
        update(Group).where(Group.semester == old_term).values(is_active=False)
    )
    tasks_result = session.exec(
        update(GroupTask)
        .where(GroupTask.semester == old_term, GroupTask.status == "evaluating")
        .values(status="closed")
    )
    session.commit()
    return groups_result.rowcount, tasks_result.rowcount


def _disable_graduates(session: Session, names_file: str) -> int:
    """软禁用毕业/退学学生（名单文件每行一个学号）"""
    with open(names_file, encoding="utf-8") as f:
        ids = [line.strip() for line in f if line.strip()]
    result = session.exec(
        update(Student)
        .where(Student.student_id.in_(ids))
        .values(is_account_enabled=False)
    )
    session.commit()
    return result.rowcount


def _preflight_names_file(names_file: str) -> int:
    """交互确认前预检毕业名单文件：打开并读行数，读取失败直接退出"""
    try:
        with open(names_file, encoding="utf-8") as f:
            line_count = len([line.strip() for line in f if line.strip()])
    except (OSError, UnicodeDecodeError) as exc:
        print(f"[错误] 名单文件读取失败: {names_file}: {exc}")
        sys.exit(1)
    return line_count


def _previous_term_label(label: str) -> Optional[str]:
    """由当前学期标识推导上一学期（'2026-2027-1' -> '2025-2026-2'）"""
    parts = label.split("-")
    if (
        len(parts) != 3
        or not parts[0].isdigit()
        or not parts[1].isdigit()
        or parts[2] not in ("1", "2")
    ):
        return None
    start_year, end_year = int(parts[0]), int(parts[1])
    if end_year != start_year + 1:
        return None
    if parts[2] == "2":
        return f"{start_year}-{end_year}-1"
    return f"{start_year - 1}-{start_year}-2"


def _validate_term_combination(session: Session, old_term: str, new_term: str) -> None:
    """学期组合前置校验：old != new，且库内存在 old 学期数据（防打错学期号）"""
    if old_term == new_term:
        print(f"[错误] 旧学期不能等于当前学期（{old_term}）："
              "请确认 TERM_CFG__LABEL 已更新为当前学期，或显式传 --old-term")
        sys.exit(1)
    schedule_count = session.exec(
        select(func.count())
        .select_from(CourseSchedule)
        .where(CourseSchedule.semester == old_term)
    ).one()
    if schedule_count == 0:
        print(f"[错误] 库中不存在学期 {old_term} 的课表数据，请核对 --old-term")
        sys.exit(1)


def _snapshot_backup(old_term: str) -> None:
    """pg_dump 快照备份（软归档的双保险）"""
    settings = get_settings()
    url = settings.database.url or ""
    backup_dir = os.path.join("backups", f"term-{old_term}")
    os.makedirs(backup_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dump_path = os.path.join(backup_dir, f"classhub_{stamp}.sql")

    if url.startswith("postgresql"):
        subprocess.run(["pg_dump", url, "-f", dump_path], check=True)
        print(f"[备份] PostgreSQL 快照已导出: {dump_path}")
    else:
        print("[警告] 未配置 PostgreSQL URL，跳过 pg_dump（请手动备份）")


def main() -> None:
    parser = argparse.ArgumentParser(description="学期切换脚本")
    parser.add_argument("--disable-graduates", default=None, help="毕业/退学学号名单文件")
    parser.add_argument("--skip-backup", action="store_true", help="跳过 pg_dump 备份")
    parser.add_argument("--old-term", default=None, help="要归档的旧学期标识")
    args = parser.parse_args()

    settings = get_settings()
    new_term = get_current_term()
    old_term = args.old_term
    if old_term is None:
        old_term = _previous_term_label(new_term)
        if old_term is None:
            print("[错误] 未传 --old-term 且无法从配置 TERM_CFG__LABEL 推导上一学期，"
                  "请显式传 --old-term")
            sys.exit(1)
        print(f"[提示] 未传 --old-term，按配置推导旧学期: {old_term}")

    # 前置校验（fail-fast：全部在交互确认与任何写操作之前）
    with Session(engine) as session:
        _validate_term_combination(session, old_term, new_term)
    if args.disable_graduates:
        line_count = _preflight_names_file(args.disable_graduates)
        print(f"[前置检查] 名单文件可读: {args.disable_graduates}（{line_count} 行）")

    print(f"[前置检查] 旧学期={old_term} 新学年={new_term}")
    print(f"[前置检查] 配置 TERM_CFG__START_DATE={settings.term.start_date} "
          f"TERM_CFG__TOTAL_WEEKS={settings.term.total_weeks}")

    # 交互确认（非交互环境用 --skip-backup 跳过）
    if not args.skip_backup:
        answer = input(f"确认开始学期切换（旧学期 {old_term} -> 新学年 {new_term}）？[y/N] ")
        if answer.lower() != "y":
            print("已取消")
            return
        _snapshot_backup(old_term)

    with Session(engine) as session:
        sessions_closed = _close_legacy_sessions(session, old_term)
        groups_closed, tasks_closed = _close_legacy_groups(session, old_term)
        archived, skipped = _archive_scores(session, old_term)
        disabled = 0
        if args.disable_graduates:
            disabled = _disable_graduates(session, args.disable_graduates)

        total_students = session.exec(select(Student)).all()
        print("\n[验证报告]")
        print(f"  遗留课堂收敛: {sessions_closed}")
        print(f"  小组失效: {groups_closed}  任务关闭: {tasks_closed}")
        print(f"  分数归档: {archived}  跳过(幂等): {skipped}")
        print(f"  软禁用学生: {disabled}")
        print(f"  库内学生总数: {len(total_students)}")
        print("\n学期切换完成。")


if __name__ == "__main__":
    main()
