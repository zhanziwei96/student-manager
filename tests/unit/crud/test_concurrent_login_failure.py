"""
测试并发登录失败保护（BE-008 修复验证）
"""
import pytest
from datetime import datetime
from sqlmodel import Session
from app.models import User
from app.models.constants import UserRoleConst
from app.crud.user import record_login_failure, record_login_success, create_user


class TestConcurrentLoginFailure:
    """测试并发登录失败乐观锁保护"""
    
    @pytest.fixture
    def test_teacher(self, session):
        """创建测试教师用户 - SEC-003: 简化密码哈希接口"""
        return create_user(
            session=session,
            username="concurrent_teacher",
            name="并发测试教师",
            password_hash="fake_hash",
            role=UserRoleConst.TEACHER,
            assigned_classes=["软件1班"]
        )
    
    def test_user_has_version_field(self, session, test_teacher):
        """测试用户模型有 version 字段"""
        user = session.get(User, test_teacher.id)
        assert hasattr(user, 'version')
        assert user.version == 1
    
    def test_record_login_failure_increments_version(self, session, test_teacher):
        """测试记录登录失败会递增版本号"""
        # 初始版本为 1
        assert test_teacher.version == 1
        assert test_teacher.login_fail_count == 0
        
        # 记录登录失败
        is_locked = record_login_failure(session, test_teacher)
        
        # 刷新获取最新数据
        session.refresh(test_teacher)
        
        # 版本号应该递增到 2
        assert test_teacher.version == 2
        assert test_teacher.login_fail_count == 1
        assert not is_locked
    
    def test_record_login_failure_multiple_times(self, session, test_teacher):
        """测试多次记录登录失败，版本号正确递增"""
        # 记录多次登录失败
        for i in range(5):
            # 每次重新获取用户对象
            user = session.get(User, test_teacher.id)
            record_login_failure(session, user)
            session.refresh(test_teacher)
            assert test_teacher.version == i + 2  # 从 1 开始，每次+1
            assert test_teacher.login_fail_count == i + 1
        
        # 最终版本应该是 6，登录失败次数为 5
        assert test_teacher.version == 6
        assert test_teacher.login_fail_count == 5
    
    def test_record_login_success_increments_version(self, session, test_teacher):
        """测试记录登录成功会递增版本号"""
        # 初始版本为 1
        assert test_teacher.version == 1
        
        # 先记录一些登录失败
        user = session.get(User, test_teacher.id)
        record_login_failure(session, user)
        record_login_failure(session, user)
        session.refresh(test_teacher)
        assert test_teacher.login_fail_count == 2
        assert test_teacher.version == 3
        
        # 记录登录成功
        user = session.get(User, test_teacher.id)
        record_login_success(session, user, "192.168.1.1")
        session.refresh(test_teacher)
        
        # 版本号应该递增到 4，失败次数清零
        assert test_teacher.version == 4
        assert test_teacher.login_fail_count == 0
        assert test_teacher.last_login_ip == "192.168.1.1"
        assert test_teacher.last_login is not None


class TestLoginFailureLockout:
    """测试登录失败锁定功能"""
    
    @pytest.fixture
    def test_teacher_lockout(self, session):
        """创建测试教师用户 - SEC-003: 简化密码哈希接口"""
        return create_user(
            session=session,
            username="lockout_teacher",
            name="锁定测试教师",
            password_hash="fake_hash",
            role=UserRoleConst.TEACHER,
            assigned_classes=["软件1班"]
        )
    
    def test_account_lockout_after_max_failures(self, session, test_teacher_lockout):
        """测试达到最大失败次数后账户被锁定"""
        from app.core.config import get_settings
        settings = get_settings()
        max_failures = settings.security.max_login_failures
        
        # 记录多次登录失败直到达到锁定阈值
        locked = False
        for i in range(max_failures):
            user = session.get(User, test_teacher_lockout.id)
            locked = record_login_failure(session, user)
            if not locked:
                session.refresh(test_teacher_lockout)
        
        # 账户应该被锁定
        assert locked is True
        session.refresh(test_teacher_lockout)
        assert test_teacher_lockout.locked_until is not None
        assert test_teacher_lockout.locked_until > datetime.now()
    
    def test_account_unlock_after_success(self, session, test_teacher_lockout):
        """测试登录成功后解锁账户"""
        from app.core.config import get_settings
        settings = get_settings()
        max_failures = settings.security.max_login_failures
        
        # 先锁定账户
        for i in range(max_failures):
            user = session.get(User, test_teacher_lockout.id)
            record_login_failure(session, user)
            if i < max_failures - 1:
                session.refresh(test_teacher_lockout)
        
        session.refresh(test_teacher_lockout)
        assert test_teacher_lockout.locked_until is not None
        
        # 登录成功应该重置锁定状态
        user = session.get(User, test_teacher_lockout.id)
        record_login_success(session, user, "192.168.1.1")
        session.refresh(test_teacher_lockout)
        
        assert test_teacher_lockout.locked_until is None
        assert test_teacher_lockout.login_fail_count == 0


class TestOptimisticLockRetry:
    """测试乐观锁重试机制"""
    
    @pytest.fixture
    def test_teacher_concurrent(self, session):
        """创建测试教师用户 - SEC-003: 简化密码哈希接口"""
        return create_user(
            session=session,
            username="concurrent_test_teacher",
            name="并发测试教师",
            password_hash="fake_hash",
            role=UserRoleConst.TEACHER,
            assigned_classes=["软件1班"]
        )
    
    def test_login_failure_with_concurrent_access(self, session, test_teacher_concurrent):
        """测试并发访问时登录失败计数仍然准确"""
        engine = session.get_bind()
        
        # 会话 A 读取用户
        user_a = session.get(User, test_teacher_concurrent.id)
        initial_version = user_a.version
        
        # 会话 B 更新用户（模拟并发）
        with Session(engine) as session_b:
            user_b = session_b.get(User, test_teacher_concurrent.id)
            user_b.login_fail_count = 3
            user_b.version += 1
            session_b.add(user_b)
            session_b.commit()
        
        # 会话 A 应该能够检测到新版本并正确处理
        session.refresh(user_a)
        assert user_a.version == initial_version + 1
        assert user_a.login_fail_count == 3
        
        # 继续记录登录失败应该正常工作
        is_locked = record_login_failure(session, user_a)
        session.refresh(test_teacher_concurrent)
        
        # 版本和计数都应该更新
        assert test_teacher_concurrent.version == initial_version + 2
        assert test_teacher_concurrent.login_fail_count == 4
