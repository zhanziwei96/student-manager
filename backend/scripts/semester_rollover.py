"""
学期切换脚本 - 开学前手动执行一次（幂等可重跑）

用法:
    cd backend
    python scripts/semester_rollover.py [--disable-graduates 名单.txt] [--old-term 2025-2026-2]

流程:
    1. 前置检查（当前学期、库内旧学期数据）
    2. 快照备份（pg_dump 到 backups/）
    3. 收敛遗留课堂（旧学期 active/scheduled -> ended）
    4. 收敛小组（is_active=False）
    5. 可选软禁用毕业/退学学生
    6. 输出验证报告
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
from app.core.term import get_current_semester
from app.models import (
    CourseSchedule,
    CourseSession,
    Group,
    Semester,
    Student,
)


def _semester_id_by_label(session: Session, label: str) -> Optional[int]:
    """按学期标识解析 semester_id（不存在返回 None）"""
    sem = session.exec(select(Semester).where(Semester.label == label)).first()
    return sem.id if sem else None


def _close_legacy_sessions(session: Session, old_term: str) -> int:
    """旧学期遗留 active/scheduled 课堂 -> ended"""
    semester_id = _semester_id_by_label(session, old_term)
    if semester_id is None:
        return 0
    result = session.exec(
        update(CourseSession)
        .where(
            CourseSession.semester_id == semester_id,
            CourseSession.status.in_(["active", "scheduled"]),
        )
        .values(status="ended")
    )
    session.commit()
    return result.rowcount


def _close_legacy_groups(session: Session, old_term: str) -> int:
    """旧学期小组失效"""
    semester_id = _semester_id_by_label(session, old_term)
    if semester_id is None:
        return 0
    groups_result = session.exec(
        update(Group).where(Group.semester_id == semester_id).values(is_active=False)
    )
    session.commit()
    return groups_result.rowcount


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
              "请确认当前学期（semesters.is_current）已切换，或显式传 --old-term")
        sys.exit(1)
    semester_id = _semester_id_by_label(session, old_term)
    schedule_count = 0
    if semester_id is not None:
        schedule_count = session.exec(
            select(func.count())
            .select_from(CourseSchedule)
            .where(CourseSchedule.semester_id == semester_id)
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
    with Session(engine) as session:
        current_sem = get_current_semester(session)
        new_term = current_sem.label if current_sem else None
    if new_term is None:
        print("[错误] 库中不存在当前学期（semesters.is_current=true），请先创建学期")
        sys.exit(1)
    old_term = args.old_term
    if old_term is None:
        old_term = _previous_term_label(new_term)
        if old_term is None:
            print("[错误] 未传 --old-term 且无法从当前学期推导上一学期，"
                  "请显式传 --old-term")
            sys.exit(1)
        print(f"[提示] 未传 --old-term，按当前学期推导旧学期: {old_term}")

    # 前置校验（fail-fast：全部在交互确认与任何写操作之前）
    with Session(engine) as session:
        _validate_term_combination(session, old_term, new_term)
    if args.disable_graduates:
        line_count = _preflight_names_file(args.disable_graduates)
        print(f"[前置检查] 名单文件可读: {args.disable_graduates}（{line_count} 行）")

    print(f"[前置检查] 旧学期={old_term} 新学年={new_term}")

    # 交互确认（非交互环境用 --skip-backup 跳过）
    if not args.skip_backup:
        answer = input(f"确认开始学期切换（旧学期 {old_term} -> 新学年 {new_term}）？[y/N] ")
        if answer.lower() != "y":
            print("已取消")
            return
        _snapshot_backup(old_term)

    with Session(engine) as session:
        sessions_closed = _close_legacy_sessions(session, old_term)
        groups_closed = _close_legacy_groups(session, old_term)
        disabled = 0
        if args.disable_graduates:
            disabled = _disable_graduates(session, args.disable_graduates)

        total_students = session.exec(select(Student)).all()
        print("\n[验证报告]")
        print(f"  遗留课堂收敛: {sessions_closed}")
        print(f"  小组失效: {groups_closed}")
        print(f"  软禁用学生: {disabled}")
        print(f"  库内学生总数: {len(total_students)}")
        print("\n学期切换完成。")


if __name__ == "__main__":
    main()
