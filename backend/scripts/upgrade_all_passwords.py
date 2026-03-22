"""
批量密码哈希升级脚本
将所有 SHA256 密码迁移到 bcrypt，保持原密码不变

密码规则：
- 管理员/教师：用户名 + "123" (如: admin -> admin123, zhanziwei -> zha123)
- 学生：学号作为密码 (如: 2513070101 -> 2513070101)
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlmodel import Session, select, create_engine
from app.core.config import get_settings
from app.core.security import generate_password_hash, needs_password_upgrade
from app.models import User, Student


def get_expected_password(user) -> str:
    """
    根据用户类型和用户名推断原密码
    
    规则：
    - admin 特殊处理: admin123
    - 其他用户: 用户名前6位 + "123"（如果是拼音）
    - 学生: 学号
    """
    username = user.username if hasattr(user, 'username') else user.student_id
    
    # 特殊账号
    special_passwords = {
        'admin': 'admin123',
        'zhanziwei': 'zha123',  # 占孜伟
        'zhangsan': 'zha123',   # 张三
        'lisi': 'li123',        # 李四
    }
    
    if username in special_passwords:
        return special_passwords[username]
    
    # 学生默认密码是学号
    if isinstance(user, Student):
        return username
    
    # 其他教师账号：取用户名前几位 + 123
    # 假设用户名是拼音，取前3-6个字符 + 123
    prefix = username[:6] if len(username) >= 6 else username
    return f"{prefix}123"


def upgrade_user_passwords(session: Session, dry_run: bool = True) -> dict:
    """升级用户密码"""
    users = session.exec(select(User)).all()
    
    stats = {
        'total': len(users),
        'upgraded': 0,
        'skipped': 0,
        'failed': 0,
        'details': []
    }
    
    for user in users:
        # 检查是否需要升级
        if not needs_password_upgrade(user.password_hash):
            stats['skipped'] += 1
            continue
        
        try:
            # 推断原密码
            original_password = get_expected_password(user)
            
            # 生成 bcrypt 哈希
            new_hash, new_salt = generate_password_hash(original_password)
            
            if not dry_run:
                # 更新数据库
                user.password_hash = new_hash
                user.salt = new_salt
                session.add(user)
            
            stats['upgraded'] += 1
            stats['details'].append({
                'username': user.username,
                'name': user.name,
                'password': original_password,
                'hash_preview': new_hash[:30] + '...'
            })
            
        except Exception as e:
            stats['failed'] += 1
            stats['details'].append({
                'username': user.username,
                'error': str(e)
            })
    
    if not dry_run:
        session.commit()
    
    return stats


def upgrade_student_passwords(session: Session, dry_run: bool = True, limit: int = None) -> dict:
    """升级学生密码"""
    query = select(Student)
    if limit:
        query = query.limit(limit)
    
    students = session.exec(query).all()
    
    stats = {
        'total': len(students),
        'upgraded': 0,
        'skipped': 0,
        'failed': 0,
        'details': []
    }
    
    for student in students:
        # 跳过空密码
        if not student.password_hash:
            stats['skipped'] += 1
            continue
        
        # 检查是否需要升级
        if not needs_password_upgrade(student.password_hash):
            stats['skipped'] += 1
            continue
        
        try:
            # 学生默认密码是学号
            original_password = student.student_id
            
            # 生成 bcrypt 哈希
            new_hash, new_salt = generate_password_hash(original_password)
            
            if not dry_run:
                # 更新数据库
                student.password_hash = new_hash
                student.salt = new_salt
                session.add(student)
            
            stats['upgraded'] += 1
            
            # 只记录前5个详情
            if len(stats['details']) < 5:
                stats['details'].append({
                    'student_id': student.student_id,
                    'name': student.name,
                    'hash_preview': new_hash[:30] + '...'
                })
            
        except Exception as e:
            stats['failed'] += 1
            if len(stats['details']) < 5:
                stats['details'].append({
                    'student_id': student.student_id,
                    'error': str(e)
                })
    
    if not dry_run:
        session.commit()
    
    return stats


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='密码哈希批量升级工具')
    parser.add_argument('--apply', action='store_true', 
                        help='真正执行升级（默认只是预览）')
    parser.add_argument('--students-only', action='store_true',
                        help='只升级学生密码')
    parser.add_argument('--users-only', action='store_true',
                        help='只升级用户密码')
    parser.add_argument('--limit', type=int, default=None,
                        help='限制处理的学生数量（用于测试）')
    
    args = parser.parse_args()
    
    dry_run = not args.apply
    
    print("=" * 70)
    print("密码哈希批量升级工具")
    print("=" * 70)
    
    if dry_run:
        print("\n【预览模式】不会真正修改数据库")
        print("如需真正执行，请添加 --apply 参数\n")
    else:
        print("\n【执行模式】将真正修改数据库！")
    
    # 连接数据库
    settings = get_settings()
    engine = create_engine(f"sqlite:///{settings.get_database_path()}")
    
    with Session(engine) as session:
        # 升级用户密码
        if not args.students_only:
            print("\n【用户密码升级】")
            user_stats = upgrade_user_passwords(session, dry_run)
            
            print(f"  总用户数: {user_stats['total']}")
            print(f"  已升级: {user_stats['upgraded']}")
            print(f"  已跳过（已是bcrypt）: {user_stats['skipped']}")
            print(f"  失败: {user_stats['failed']}")
            
            print("\n  升级详情（前5个）:")
            for detail in user_stats['details'][:5]:
                if 'error' in detail:
                    print(f"    ❌ {detail.get('username', 'unknown')}: {detail['error']}")
                else:
                    print(f"    ✅ {detail['username']} ({detail['name']}): {detail['password']} -> {detail['hash_preview']}")
        
        # 升级学生密码
        if not args.users_only:
            print("\n【学生密码升级】")
            if args.limit:
                print(f"  （限制处理 {args.limit} 个学生）")
            
            student_stats = upgrade_student_passwords(session, dry_run, args.limit)
            
            print(f"  总学生数: {student_stats['total']}")
            print(f"  已升级: {student_stats['upgraded']}")
            print(f"  已跳过（已是bcrypt或空密码）: {student_stats['skipped']}")
            print(f"  失败: {student_stats['failed']}")
            
            print("\n  升级详情（前5个）:")
            for detail in student_stats['details'][:5]:
                if 'error' in detail:
                    print(f"    ❌ {detail.get('student_id', 'unknown')}: {detail['error']}")
                else:
                    print(f"    ✅ {detail['student_id']} ({detail['name']}): {detail['hash_preview']}")
    
    print("\n" + "=" * 70)
    if dry_run:
        print("预览完成！如需执行，请运行:")
        print("  python scripts/upgrade_all_passwords.py --apply")
    else:
        print("升级完成！所有密码已迁移到 bcrypt")
    print("=" * 70)


if __name__ == "__main__":
    main()
