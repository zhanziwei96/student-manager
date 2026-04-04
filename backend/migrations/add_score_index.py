#!/usr/bin/env python3
"""
迁移脚本：为学生表 score 字段添加索引
用于优化排行榜查询性能
"""
import sqlite3
import sys
import os

# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.config import get_settings

def add_score_index():
    """添加 score 字段索引"""
    settings = get_settings()
    db_path = settings.get_database_path()

    print(f"数据库路径: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 检查索引是否已存在
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_students_score'"
    )
    if cursor.fetchone():
        print("索引 idx_students_score 已存在，跳过")
        conn.close()
        return

    # 创建索引
    print("创建索引 idx_students_score...")
    cursor.execute("CREATE INDEX idx_students_score ON students(score DESC)")
    conn.commit()

    # 验证
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='students'"
    )
    indexes = [r[0] for r in cursor.fetchall()]
    print(f"创建完成。现有索引: {indexes}")

    conn.close()
    print("✅ 迁移完成")


if __name__ == "__main__":
    add_score_index()
