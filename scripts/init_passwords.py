#!/usr/bin/env python3
"""
初始化生产数据库中的教师和学生密码
- 教师 teacher1: teacher123
- 所有学生: 学号作为密码
"""
import sqlite3
import bcrypt
from pathlib import Path

def generate_password_hash(password: str) -> tuple[str, str]:
    """生成密码哈希（使用 bcrypt）"""
    password_bytes = password.encode('utf-8')[:72]
    password_hash = bcrypt.hashpw(
        password_bytes, 
        bcrypt.gensalt(rounds=12)
    ).decode('utf-8')
    return password_hash, ""

def init_teacher_password(db_path: str):
    """初始化教师密码"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查 teacher1 是否存在
    cursor.execute("SELECT username FROM users WHERE username = 'teacher1'")
    if not cursor.fetchone():
        print("⚠️  teacher1 不存在，跳过")
        conn.close()
        return
    
    # 生成密码哈希
    password_hash, salt = generate_password_hash("teacher123")
    
    # 更新 teacher1 密码
    cursor.execute(
        "UPDATE users SET password_hash = ?, salt = ? WHERE username = 'teacher1'",
        (password_hash, salt)
    )
    conn.commit()
    conn.close()
    print("✅ 教师 teacher1 密码已设置为: teacher123")

def init_student_passwords(db_path: str):
    """初始化所有学生密码（学号作为密码）"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 获取所有没有密码的学生
    cursor.execute("""
        SELECT student_id FROM students 
        WHERE password_hash IS NULL OR password_hash = ''
    """)
    students = cursor.fetchall()
    
    if not students:
        print("⚠️  所有学生已有密码")
        conn.close()
        return
    
    print(f"📝 正在为 {len(students)} 名学生初始化密码...")
    print("  (bcrypt 哈希计算较慢，请耐心等待...)")
    
    updated = 0
    batch_size = 50
    
    for i, (student_id,) in enumerate(students):
        # 使用学号作为密码
        password_hash, salt = generate_password_hash(str(student_id))
        cursor.execute(
            "UPDATE students SET password_hash = ?, salt = ? WHERE student_id = ?",
            (password_hash, salt, student_id)
        )
        updated += 1
        
        # 每 50 个提交一次，减少内存占用
        if updated % batch_size == 0:
            conn.commit()
            print(f"  已处理 {updated}/{len(students)} ({updated * 100 // len(students)}%)...")
    
    conn.commit()
    conn.close()
    print(f"✅ 已初始化 {updated} 名学生的密码（学号作为密码）")

def verify_init(db_path: str):
    """验证初始化结果"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查教师
    cursor.execute("SELECT username, password_hash FROM users WHERE username = 'teacher1'")
    teacher = cursor.fetchone()
    if teacher and teacher[1]:
        print(f"✅ 教师 {teacher[0]} 密码已设置")
    else:
        print(f"❌ 教师 teacher1 密码未设置")
    
    # 检查学生
    cursor.execute("SELECT COUNT(*) FROM students WHERE password_hash IS NOT NULL AND password_hash != ''")
    count = cursor.fetchone()[0]
    print(f"✅ 已有 {count} 名学生设置了密码")
    
    conn.close()

def main():
    # 数据库路径
    db_path = Path(__file__).parent.parent / "backend" / "data" / "class_system.db"
    
    if not db_path.exists():
        print(f"❌ 数据库不存在: {db_path}")
        return
    
    print(f"📁 使用数据库: {db_path}")
    print()
    
    # 初始化教师密码
    print("=" * 40)
    print("初始化教师密码")
    print("=" * 40)
    init_teacher_password(str(db_path))
    print()
    
    # 初始化学生密码
    print("=" * 40)
    print("初始化学生密码")
    print("=" * 40)
    init_student_passwords(str(db_path))
    print()
    
    # 验证
    print("=" * 40)
    print("验证结果")
    print("=" * 40)
    verify_init(str(db_path))
    print()
    
    print("🎉 密码初始化完成！")
    print()
    print("测试账号：")
    print("  教师: teacher1 / teacher123")
    print("  学生: <学号> / <学号>")
    print("  例如: 2513070201 / 2513070201")

if __name__ == "__main__":
    main()
