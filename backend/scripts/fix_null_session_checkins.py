#!/usr/bin/env python3
"""
修复历史幽灵签到记录

问题: migration 后产生了 182 条 session_id 为 NULL 的 checkin_records，
导致教师端课堂签到列表无法看到这些历史签到。

修复策略:
1. 按 class_name + date(checkin_time) 分组
2. 为每组创建一个新的已结束 course_sessions（占位 session）
3. 将该组所有 checkin_records 的 session_id 更新到新 session
"""
import sqlite3
import uuid
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# 数据库路径
DB_PATH = Path(__file__).parent.parent / "app" / "data" / "class_system.db"


def backup_db():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = DB_PATH.parent / f"{DB_PATH.name}.backup.before_fix_null_sessions.{timestamp}"
    shutil.copy2(DB_PATH, backup_path)
    print(f"[备份] 数据库已备份到: {backup_path}")
    return backup_path


def get_course_name_for_class(conn, class_name: str) -> str | None:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT course_name FROM course_schedules WHERE class_name = ? LIMIT 1",
        (class_name,),
    )
    row = cursor.fetchone()
    return row[0] if row else None


def fix_null_session_checkins(dry_run: bool = True):
    if not DB_PATH.exists():
        print(f"[错误] 数据库不存在: {DB_PATH}")
        return 1

    if not dry_run:
        backup_db()

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    # 1. 查询所有需要修复的 NULL session_id 分组
    cursor.execute("""
        SELECT
            class_name,
            date(checkin_time) as dt,
            COUNT(*) as cnt,
            MIN(checkin_time) as first_checkin,
            MAX(checkin_time) as last_checkin
        FROM checkin_records
        WHERE session_id IS NULL
        GROUP BY class_name, date(checkin_time)
        ORDER BY dt, class_name
    """)
    groups = cursor.fetchall()

    if not groups:
        print("[提示] 没有发现 session_id 为 NULL 的记录，无需修复。")
        conn.close()
        return 0

    print(f"[{'预览' if dry_run else '修复'}] 发现 {len(groups)} 个分组，共涉及 {sum(g[2] for g in groups)} 条签到记录\n")

    # teacher 信息统一用系统中唯一教师（从数据观察，所有班级都归属 teacher_id=2）
    teacher_id = 2
    teacher_name = "占孜伟"

    total_fixed = 0

    for class_name, dt, cnt, first_checkin, last_checkin in groups:
        course_name = get_course_name_for_class(conn, class_name)
        session_code = str(uuid.uuid4())[:8].upper()

        # 如果 start_time 和 end_time 相同，end_time 加 1 秒避免 0 长度课堂
        if first_checkin == last_checkin:
            last_checkin = datetime.fromisoformat(last_checkin)
            last_checkin = last_checkin.strftime("%Y-%m-%d %H:%M:%S.%f")
            # 实际上 same string 就可以直接用了

        print(
            f"  班级: {class_name} | 日期: {dt} | 记录数: {cnt} | "
            f"开始: {first_checkin} | 课程: {course_name or '历史课程'}"
        )

        if dry_run:
            total_fixed += cnt
            continue

        # 2. 创建占位 course_session
        cursor.execute("""
            INSERT INTO course_sessions (
                session_code, schedule_id, course_name, class_name, classroom,
                teacher_id, teacher_name, status, start_time, end_time,
                week_number, source_type, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_code,
            None,
            course_name,
            class_name,
            None,
            teacher_id,
            teacher_name,
            "ended",
            first_checkin,
            last_checkin,
            None,
            "manual",
            datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
        ))
        session_id = cursor.lastrowid

        # 3. 更新该组 checkin_records
        cursor.execute("""
            UPDATE checkin_records
            SET session_id = ?
            WHERE session_id IS NULL
              AND class_name = ?
              AND date(checkin_time) = ?
        """, (session_id, class_name, dt))
        updated_rows = cursor.rowcount
        total_fixed += updated_rows

        print(f"    -> 新建 session_id={session_id}, 更新 {updated_rows} 条签到记录")

    if not dry_run:
        conn.commit()
        print(f"\n[成功] 已提交事务，共修复 {total_fixed} 条记录。")
    else:
        print(f"\n[预览结束] 干运行模式，未实际修改。将修复 {total_fixed} 条记录。")
        print("        若确认无误，请传入 --apply 参数执行真正修复。")

    # 4. 验证：检查是否还有 NULL session_id
    cursor.execute("SELECT COUNT(*) FROM checkin_records WHERE session_id IS NULL")
    remaining = cursor.fetchone()[0]
    print(f"[验证] 剩余 NULL session_id 记录数: {remaining}")

    conn.close()
    return 0


if __name__ == "__main__":
    import sys

    dry_run = "--apply" not in sys.argv
    sys.exit(fix_null_session_checkins(dry_run=dry_run))
