#!/usr/bin/env python3
"""
迁移 SQLite 数据到 PostgreSQL
在 backend 容器内运行：
    python scripts/migrate_sqlite_to_postgres.py /app/sqlite_backup/class_system.db postgresql+psycopg2://classhub:classhub_secret@postgres:5432/classhub
"""
import sys
from sqlalchemy import create_engine, MetaData, inspect, text
from sqlalchemy.orm import sessionmaker


def migrate(sqlite_path: str, pg_url: str):
    sqlite_url = f"sqlite:///{sqlite_path}"
    src_engine = create_engine(sqlite_url)
    tgt_engine = create_engine(pg_url)

    src_inspector = inspect(src_engine)
    tgt_inspector = inspect(tgt_engine)

    # 获取 SQLite 中所有表（排除 alembic_version）
    src_tables = [t for t in src_inspector.get_table_names() if t != "alembic_version"]
    tgt_tables = set(tgt_inspector.get_table_names())

    print(f"[源] SQLite 表: {src_tables}")
    print(f"[目标] PostgreSQL 现有表: {list(tgt_tables)}")

    Session = sessionmaker(bind=tgt_engine)
    session = Session()

    # 关闭 PostgreSQL 外键检查以加速导入
    session.execute(text("SET session_replication_role = 'replica'"))
    session.commit()

    for table_name in src_tables:
        if table_name not in tgt_tables:
            print(f"[跳过] 目标库中不存在表: {table_name}")
            continue

        print(f"[迁移] 表 {table_name} ...")

        # 读取 SQLite 数据
        with src_engine.connect() as conn:
            result = conn.execute(text(f"SELECT * FROM {table_name}"))
            rows = result.mappings().all()

        if not rows:
            print(f"  -> 空表，跳过")
            continue

        # 构建批量插入
        columns = list(rows[0].keys())
        col_str = ", ".join([f'"{c}"' for c in columns])
        placeholders = ", ".join([f":{c}" for c in columns])
        insert_stmt = text(f"INSERT INTO \"{table_name}\" ({col_str}) VALUES ({placeholders})")

        # 获取目标表的列类型信息，用于类型转换
        tgt_cols = {c["name"]: c["type"] for c in tgt_inspector.get_columns(table_name)}
        boolean_cols = [c for c, t in tgt_cols.items() if "BOOLEAN" in str(t).upper()]

        # 转换数据为字典列表，并处理布尔值
        dict_rows = []
        for row in rows:
            d = dict(row)
            for col in boolean_cols:
                if col in d and d[col] is not None:
                    d[col] = bool(d[col])
            dict_rows.append(d)

        with tgt_engine.begin() as conn:
            conn.execute(insert_stmt, dict_rows)

        print(f"  -> 迁移 {len(dict_rows)} 条记录")

    # 恢复外键检查
    session.execute(text("SET session_replication_role = 'origin'"))
    session.commit()
    session.close()

    # 重置所有自增序列
    print("[重置] 更新 PostgreSQL 序列...")
    for table_name in tgt_tables:
        if table_name == "alembic_version":
            continue
        columns = tgt_inspector.get_columns(table_name)
        for col in columns:
            if col.get("autoincrement") or (col["name"] == "id" and "INTEGER" in str(col["type"])):
                seq_name = f"{table_name}_id_seq"
                try:
                    with tgt_engine.begin() as conn:
                        conn.execute(text(f"SELECT setval('{seq_name}', COALESCE((SELECT MAX(id) FROM \"{table_name}\"), 1), true)"))
                    print(f"  -> {seq_name} 已重置")
                except Exception as e:
                    print(f"  -> {seq_name} 重置失败（可能不存在）: {e}")
                break

    print("[完成] 数据迁移成功！")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python migrate_sqlite_to_postgres.py <sqlite_db_path> <postgresql_url>")
        sys.exit(1)
    migrate(sys.argv[1], sys.argv[2])
