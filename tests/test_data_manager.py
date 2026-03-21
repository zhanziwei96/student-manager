#!/usr/bin/env python3
"""
测试数据管理脚本

用法:
    python tests/test_data_manager.py setup    # 初始化测试数据
    python tests/test_data_manager.py cleanup  # 清理测试数据
    python tests/test_data_manager.py reset    # 重置测试数据（清理+初始化）
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tests.conftest import TestDataManager


def main():
    if len(sys.argv) < 2:
        print("用法: python tests/test_data_manager.py [setup|cleanup|reset]")
        print("")
        print("  setup    - 初始化测试数据")
        print("  cleanup  - 清理测试数据")
        print("  reset    - 重置测试数据（清理+初始化）")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    manager = TestDataManager()
    
    if command == "setup":
        manager.setup_test_data()
        print("\n✅ 测试数据初始化完成")
        
    elif command == "cleanup":
        # 需要手动设置已创建的数据列表
        manager.created_users = ["test_admin", "test_teacher"]
        manager.created_students = ["TEST001", "TEST002", "TEST003"]
        manager.cleanup_test_data()
        print("\n✅ 测试数据清理完成")
        
    elif command == "reset":
        # 先清理
        manager.created_users = ["test_admin", "test_teacher"]
        manager.created_students = ["TEST001", "TEST002", "TEST003"]
        manager.cleanup_test_data()
        # 再初始化
        manager.setup_test_data()
        print("\n✅ 测试数据重置完成")
        
    else:
        print(f"未知命令: {command}")
        print("用法: python tests/test_data_manager.py [setup|cleanup|reset]")
        sys.exit(1)


if __name__ == "__main__":
    main()
