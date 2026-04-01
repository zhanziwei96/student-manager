#!/usr/bin/env python3
"""
数据库迁移管理脚本

用法:
    python migrate.py upgrade        # 升级到最新版本
    python migrate.py downgrade      # 降级到上一个版本
    python migrate.py history        # 查看迁移历史
    python migrate.py current        # 查看当前版本
    python migrate.py create "描述"   # 创建新迁移
"""
import sys
import os
import subprocess

# 设置环境变量
os.environ.setdefault('ENV', 'development')


def run_alembic_command(args):
    """运行 alembic 命令"""
    cmd = ['conda', 'run', '-n', 'student-manage', 'alembic'] + args
    result = subprocess.run(cmd, capture_output=True, text=True, cwd='/home/yufeng/student-manager/backend')
    if result.returncode != 0:
        print(f"错误: {result.stderr}")
        sys.exit(1)
    return result.stdout


def upgrade():
    """升级到最新版本"""
    print("正在升级数据库到最新版本...")
    output = run_alembic_command(['upgrade', 'head'])
    print(output)
    print("✅ 升级完成")


def downgrade():
    """降级到上一个版本"""
    print("正在降级数据库...")
    output = run_alembic_command(['downgrade', '-1'])
    print(output)
    print("✅ 降级完成")


def history():
    """查看迁移历史"""
    output = run_alembic_command(['history', '--verbose'])
    print(output)


def current():
    """查看当前版本"""
    output = run_alembic_command(['current'])
    print(f"当前数据库版本: {output.strip()}")


def create(message):
    """创建新迁移"""
    print(f"正在创建迁移: {message}...")
    output = run_alembic_command(['revision', '--autogenerate', '-m', message])
    print(output)
    print("✅ 迁移创建完成，请检查生成的文件")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == 'upgrade':
        upgrade()
    elif command == 'downgrade':
        downgrade()
    elif command == 'history':
        history()
    elif command == 'current':
        current()
    elif command == 'create':
        if len(sys.argv) < 3:
            print("错误: 请提供迁移描述")
            print("示例: python migrate.py create 'add user table'")
            sys.exit(1)
        create(sys.argv[2])
    else:
        print(f"未知命令: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()
