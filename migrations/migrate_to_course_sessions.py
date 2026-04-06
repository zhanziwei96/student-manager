#!/usr/bin/env python3
"""CourseSession 迁移脚本 - 安全执行并自动备份"""
import os
import sqlite3
import shutil
import sys
from datetime import datetime
from pathlib import Path

# 默认数据库路径（相对于脚本位置）
DEFAULT_DB_PATH = Path(__file__).parent.parent / "backend" / "app" / "data" / "class_system.db"
SQL_FILE = Path(__file__).parent / "migrate_to_course_sessions.sql"


def get_db_path() -> Path:
    """获取数据库路径：支持命令行参数或环境变量覆盖"""
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).resolve()
    env_path = os.getenv("DATABASE_PATH")
    if env_path:
        return Path(env_path).resolve()
    return DEFAULT_DB_PATH.resolve()


def backup_db(db_path: Path) -> Path:
    """自动备份数据库，返回备份路径"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.parent / f"{db_path.name}.backup.{timestamp}"
    shutil.copy2(db_path, backup_path)
    print(f"[备份] 数据库已备份到: {backup_path}")
    return backup_path


def read_sql_script(sql_path: Path) -> str:
    """读取 SQL 脚本内容"""
    with open(sql_path, "r", encoding="utf-8") as f:
        return f.read()


def run_migration(db_path: Path, sql_text: str) -> None:
    """在事务中执行迁移 SQL"""
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    # 将脚本按分号拆分为多个语句块（简单拆分）
    statements = []
    current = []
    for line in sql_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        current.append(line)
        if stripped.endswith(";"):
            statements.append("\n".join(current))
            current = []
    if current:
        statements.append("\n".join(current))

    try:
        for idx, stmt in enumerate(statements, start=1):
            stmt = stmt.strip()
            if not stmt:
                continue
            print(f"[步骤 {idx}] 执行 SQL...")
            try:
                cursor.executescript(stmt)
            except sqlite3.OperationalError as e:
                # 忽略 "duplicate column name" 和 "table already exists"
                msg = str(e).lower()
                if "duplicate column name" in msg or "already exists" in msg:
                    print(f"  [跳过] {e}")
                else:
                    raise
        conn.commit()
        print("[成功] 迁移执行完成，事务已提交。")
    except Exception as e:
        conn.rollback()
        print(f"[失败] 迁移出错，事务已回滚: {e}")
        raise
    finally:
        conn.close()


def main() -> int:
    db_path = get_db_path()
    print(f"[目标数据库] {db_path}")

    if not db_path.exists():
        print(f"[错误] 数据库文件不存在: {db_path}")
        return 1

    if not SQL_FILE.exists():
        print(f"[错误] SQL 脚本不存在: {SQL_FILE}")
        return 1

    backup_db(db_path)
    sql_text = read_sql_script(SQL_FILE)
    run_migration(db_path, sql_text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
