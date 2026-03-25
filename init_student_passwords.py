#!/usr/bin/env python3
"""
为所有学生初始化密码
密码 = 学号
"""
import sqlite3
import bcrypt


def hash_password(password: str) -> str:
    """生成 bcrypt 密码哈希"""
    password_bytes = password.encode('utf-8')[:72]
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=12)).decode('utf-8')


def init_student_passwords(db_path: str):
    """为所有没有密码的学生设置初始密码"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
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
    updated = 0
    for row in students:
        student_id = row[0]
        
        # 使用学号作为初始密码
        password_hash = hash_password(student_id)
        
        cursor.execute("""
            UPDATE students 
            SET password_hash = ?, salt = ''
            WHERE student_id = ?
        """, (password_hash, student_id))
        
        updated += 1
        if updated % 50 == 0:
            print(f"  已处理 {updated}/{len(students)} 位学生")
    
    conn.commit()
    conn.close()
    print(f"\n完成！共为 {updated} 位学生设置了初始密码")
    print("初始密码规则：学号即为密码")


if __name__ == '__main__':
    db_path = 'backend/data/class_system.db'
    print(f"数据库路径: {db_path}")
    init_student_passwords(db_path)
