#!/usr/bin/env python3
"""
为已存在的学生初始化密码
密码 = 学号
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import sqlite3
from domain.value_objects.password import Password


def init_student_passwords(db_path: str):
    """为所有没有密码的学生设置初始密码"""
    
    # 检查密码字段是否存在
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 检查表结构
    cursor.execute("PRAGMA table_info(students)")
    columns = [row['name'] for row in cursor.fetchall()]
    
    if 'password_hash' not in columns:
        print("添加密码字段...")
        cursor.execute("ALTER TABLE students ADD COLUMN password_hash TEXT")
        cursor.execute("ALTER TABLE students ADD COLUMN salt TEXT")
        cursor.execute("ALTER TABLE students ADD COLUMN is_active INTEGER DEFAULT 1")
        cursor.execute("ALTER TABLE students ADD COLUMN last_login TIMESTAMP")
        conn.commit()
        print("密码字段添加完成")
    
    # 查找没有密码的学生
    cursor.execute("""
        SELECT student_id FROM students 
        WHERE password_hash IS NULL OR password_hash = ''
    """)
    
    students = cursor.fetchall()
    
    if not students:
        print("所有学生已有密码，无需更新")
        conn.close()
        return
    
    print(f"找到 {len(students)} 位需要设置密码的学生")
    
    # 为每个学生设置密码
    for row in students:
        student_id = row['student_id']
        
        # 使用学号作为初始密码
        password = Password.create(student_id)
        
        cursor.execute("""
            UPDATE students 
            SET password_hash = ?, salt = ?
            WHERE student_id = ?
        """, (password.hash, password.salt, student_id))
        
        print(f"  - 学生 {student_id}: 密码已设置为 {student_id}")
    
    conn.commit()
    conn.close()
    print(f"\n完成！共为 {len(students)} 位学生设置了初始密码")


if __name__ == '__main__':
    # 默认数据库路径
    db_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'data', 
        'student_manage.db'
    )
    
    # 也可以使用环境变量指定路径
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    print(f"数据库路径: {os.path.abspath(db_path)}")
    init_student_passwords(db_path)
