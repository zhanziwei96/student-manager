"""
密码哈希迁移脚本
扫描现有密码，报告需要升级的账号（SHA256 -> bcrypt）
"""
import sys
import os

# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlmodel import Session, select, create_engine
from app.core.config import get_settings
from app.models import User, Student


def check_password_type(password_hash: str) -> str:
    """检查密码哈希类型"""
    if not password_hash:
        return "empty"
    if password_hash.startswith('$2'):
        return "bcrypt"
    return "sha256"


def migrate():
    settings = get_settings()
    engine = create_engine(f"sqlite:///{settings.get_database_path()}")
    
    print("=" * 60)
    print("密码哈希迁移检查报告")
    print("=" * 60)
    
    with Session(engine) as session:
        # 检查用户表
        users = session.exec(select(User)).all()
        user_stats = {"bcrypt": 0, "sha256": 0, "empty": 0}
        sha256_users = []
        
        for user in users:
            ptype = check_password_type(user.password_hash)
            user_stats[ptype] += 1
            if ptype == "sha256":
                sha256_users.append(f"  - {user.username} ({user.name})")
        
        print(f"\n【用户表 (users)】")
        print(f"  总数: {len(users)}")
        print(f"  bcrypt: {user_stats['bcrypt']}")
        print(f"  SHA256 (需升级): {user_stats['sha256']}")
        print(f"  空密码: {user_stats['empty']}")
        
        if sha256_users:
            print(f"\n  需要升级的用户:")
            for u in sha256_users:
                print(u)
        
        # 检查学生表
        students = session.exec(select(Student)).all()
        student_stats = {"bcrypt": 0, "sha256": 0, "empty": 0}
        sha256_students = []
        
        for student in students:
            ptype = check_password_type(student.password_hash)
            student_stats[ptype] += 1
            if ptype == "sha256":
                sha256_students.append(f"  - {student.student_id} ({student.name})")
        
        print(f"\n【学生表 (students)】")
        print(f"  总数: {len(students)}")
        print(f"  bcrypt: {student_stats['bcrypt']}")
        print(f"  SHA256 (需升级): {student_stats['sha256']}")
        print(f"  空密码: {student_stats['empty']}")
        
        if sha256_students[:10]:  # 只显示前10个
            print(f"\n  需要升级的学生 (前10个):")
            for s in sha256_students[:10]:
                print(s)
            if len(sha256_students) > 10:
                print(f"  ... 还有 {len(sha256_students) - 10} 个")
        
        total_sha256 = user_stats['sha256'] + student_stats['sha256']
        
        print("\n" + "=" * 60)
        if total_sha256 == 0:
            print("✅ 所有密码已使用 bcrypt，无需升级")
        else:
            print(f"⚠️  共有 {total_sha256} 个账号需要升级")
            print("   这些账号将在下次登录时自动升级到 bcrypt")
        print("=" * 60)
        
        return total_sha256


if __name__ == "__main__":
    migrate()
