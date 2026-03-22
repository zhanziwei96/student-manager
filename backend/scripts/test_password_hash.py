"""
密码哈希功能测试脚本
测试 bcrypt 生成和验证功能
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.security import (
    generate_password_hash, 
    verify_password_hash,
    needs_password_upgrade
)


def test_bcrypt_hash():
    """测试 bcrypt 密码哈希"""
    print("=" * 60)
    print("测试 bcrypt 密码哈希功能")
    print("=" * 60)
    
    # 测试 1: 生成哈希
    print("\n【测试 1】生成密码哈希")
    password = "test123456"
    password_hash, salt = generate_password_hash(password)
    
    print(f"  原始密码: {password}")
    print(f"  生成的哈希: {password_hash[:50]}...")
    print(f"  哈希长度: {len(password_hash)} 字符")
    print(f"  盐值（bcrypt 模式下为空）: '{salt}'")
    
    # 验证是 bcrypt 格式
    assert password_hash.startswith('$2'), "哈希应以 $2 开头"
    assert salt == "", "bcrypt 模式下盐值应为空字符串"
    print("  ✅ 哈希格式正确")
    
    # 测试 2: 验证正确密码
    print("\n【测试 2】验证正确密码")
    result = verify_password_hash(password, password_hash, salt)
    assert result is True, "正确密码应验证通过"
    print(f"  验证结果: {result}")
    print("  ✅ 正确密码验证通过")
    
    # 测试 3: 验证错误密码
    print("\n【测试 3】验证错误密码")
    wrong_password = "wrongpassword"
    result = verify_password_hash(wrong_password, password_hash, salt)
    assert result is False, "错误密码应验证失败"
    print(f"  错误密码: {wrong_password}")
    print(f"  验证结果: {result}")
    print("  ✅ 错误密码验证失败")
    
    # 测试 4: 检查升级需求
    print("\n【测试 4】检查密码升级需求")
    need_upgrade = needs_password_upgrade(password_hash)
    assert need_upgrade is False, "bcrypt 密码不需要升级"
    print(f"  bcrypt 密码需要升级: {need_upgrade}")
    print("  ✅ bcrypt 密码标记为不需要升级")
    
    print("\n" + "=" * 60)
    print("所有 bcrypt 测试通过! ✅")
    print("=" * 60)


def test_backward_compatibility():
    """测试向后兼容性（SHA256）"""
    print("\n" + "=" * 60)
    print("测试 SHA256 向后兼容性")
    print("=" * 60)
    
    # 模拟旧版 SHA256 哈希
    import hashlib
    import secrets
    
    print("\n【测试 5】验证旧版 SHA256 密码")
    password = "oldpassword123"
    salt = secrets.token_hex(16)
    old_hash = hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
    
    print(f"  原始密码: {password}")
    print(f"  SHA256 哈希: {old_hash[:40]}...")
    print(f"  盐值: {salt[:20]}...")
    
    # 验证正确密码
    result = verify_password_hash(password, old_hash, salt)
    assert result is True, "旧版 SHA256 正确密码应验证通过"
    print(f"  验证结果: {result}")
    print("  ✅ 旧版 SHA256 密码验证通过")
    
    # 检查是否需要升级
    print("\n【测试 6】检查旧版密码升级需求")
    need_upgrade = needs_password_upgrade(old_hash)
    assert need_upgrade is True, "SHA256 密码应标记为需要升级"
    print(f"  SHA256 密码需要升级: {need_upgrade}")
    print("  ✅ SHA256 密码正确标记为需要升级")
    
    print("\n" + "=" * 60)
    print("向后兼容性测试通过! ✅")
    print("=" * 60)


def test_edge_cases():
    """测试边界情况"""
    print("\n" + "=" * 60)
    print("测试边界情况")
    print("=" * 60)
    
    # 测试空密码哈希
    print("\n【测试 7】空密码哈希验证")
    result = verify_password_hash("password", None, "salt")
    assert result is False
    print(f"  空哈希验证结果: {result}")
    print("  ✅ 空哈希正确处理")
    
    # 测试空盐值（旧版）
    print("\n【测试 8】空盐值验证（旧版）")
    result = verify_password_hash("password", "somehash", None)
    assert result is False
    print(f"  空盐值验证结果: {result}")
    print("  ✅ 空盐值正确处理")
    
    # 测试特殊字符密码
    print("\n【测试 9】特殊字符密码")
    special_password = "p@ssw0rd!#$%^&*()_+-=[]{}|;':\",./<>?"
    password_hash, salt = generate_password_hash(special_password)
    result = verify_password_hash(special_password, password_hash, salt)
    assert result is True
    print(f"  特殊字符密码验证结果: {result}")
    print("  ✅ 特殊字符密码正确处理")
    
    # 测试长密码
    print("\n【测试 10】长密码（100字符）")
    long_password = "a" * 100
    password_hash, salt = generate_password_hash(long_password)
    result = verify_password_hash(long_password, password_hash, salt)
    assert result is True
    print(f"  长密码验证结果: {result}")
    print("  ✅ 长密码正确处理")
    
    print("\n" + "=" * 60)
    print("边界情况测试通过! ✅")
    print("=" * 60)


def benchmark():
    """性能测试"""
    import time
    
    print("\n" + "=" * 60)
    print("性能测试（bcrypt 12轮）")
    print("=" * 60)
    
    password = "benchmark_password"
    iterations = 10
    
    # 测试哈希生成性能
    print(f"\n【性能测试】生成 {iterations} 个哈希")
    start = time.time()
    hashes = []
    for i in range(iterations):
        h, s = generate_password_hash(password)
        hashes.append((h, s))
    hash_time = time.time() - start
    
    print(f"  总耗时: {hash_time:.3f} 秒")
    print(f"  平均每次: {hash_time/iterations*1000:.1f} 毫秒")
    
    # 测试验证性能
    print(f"\n【性能测试】验证 {iterations} 个哈希")
    start = time.time()
    for h, s in hashes:
        verify_password_hash(password, h, s)
    verify_time = time.time() - start
    
    print(f"  总耗时: {verify_time:.3f} 秒")
    print(f"  平均每次: {verify_time/iterations*1000:.1f} 毫秒")
    
    print("\n" + "=" * 60)
    print("性能测试完成")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_bcrypt_hash()
        test_backward_compatibility()
        test_edge_cases()
        benchmark()
        
        print("\n" + "=" * 60)
        print("🎉 所有测试通过！密码哈希升级准备就绪")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
