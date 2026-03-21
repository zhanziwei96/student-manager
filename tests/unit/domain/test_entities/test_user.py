"""
用户实体测试
纯内存测试，无需数据库
"""
import pytest
from datetime import datetime, timedelta
from domain.entities.user import User, UserRole, UserStatus
from domain.value_objects.password import Password


class TestUser:
    """用户实体测试类"""
    
    @pytest.fixture
    def admin_user(self):
        """管理员用户"""
        return User(
            username="admin",
            name="管理员",
            password=Password.create_from_plain("admin123"),
            role=UserRole.ADMIN
        )
    
    @pytest.fixture
    def teacher_user(self):
        """教师用户"""
        return User(
            username="teacher1",
            name="王老师",
            password=Password.create_from_plain("teacher123"),
            role=UserRole.TEACHER,
            assigned_classes=["软件1班", "软件2班"]
        )
    
    # ========== 构造测试 ==========
    
    def test_create_admin_user(self):
        """创建管理员用户"""
        user = User(
            username="admin",
            name="管理员",
            password=Password.create_from_plain("admin123"),
            role=UserRole.ADMIN
        )
        
        assert user.username == "admin"
        assert user.name == "管理员"
        assert user.role == UserRole.ADMIN
        assert user.status == UserStatus.ACTIVE  # 默认状态
        assert user.assigned_classes == []  # 默认空列表
    
    def test_create_teacher_user(self):
        """创建教师用户"""
        user = User(
            username="teacher1",
            name="王老师",
            password=Password.create_from_plain("teacher123"),
            role=UserRole.TEACHER,
            assigned_classes=["软件1班"]
        )
        
        assert user.role == UserRole.TEACHER
        assert user.assigned_classes == ["软件1班"]
    
    def test_default_status_is_active(self):
        """默认状态为激活"""
        user = User(
            username="user1",
            name="用户1",
            password=Password.create_from_plain("pass123"),
            role=UserRole.TEACHER
        )
        
        assert user.status == UserStatus.ACTIVE
    
    def test_default_login_fail_count_is_zero(self):
        """默认登录失败次数为0"""
        user = User(
            username="user1",
            name="用户1",
            password=Password.create_from_plain("pass123"),
            role=UserRole.TEACHER
        )
        
        assert user.login_fail_count == 0
    
    # ========== 角色测试 ==========
    
    def test_is_admin_true(self, admin_user):
        """管理员判断为True"""
        assert admin_user.is_admin() is True
    
    def test_is_admin_false(self, teacher_user):
        """非管理员判断为False"""
        assert teacher_user.is_admin() is False
    
    # ========== 状态测试 ==========
    
    def test_is_active_true(self, admin_user):
        """激活状态返回True"""
        assert admin_user.is_active() is True
    
    def test_is_active_false(self, admin_user):
        """非激活状态返回False"""
        admin_user.status = UserStatus.INACTIVE
        assert admin_user.is_active() is False
    
    def test_is_active_when_locked(self, admin_user):
        """锁定状态返回False"""
        admin_user.status = UserStatus.LOCKED
        assert admin_user.is_active() is False
    
    # ========== 班级访问权限测试 ==========
    
    def test_admin_can_access_any_class(self, admin_user):
        """管理员可访问任意班级"""
        assert admin_user.can_access_class("软件1班") is True
        assert admin_user.can_access_class("计算机1班") is True
        assert admin_user.can_access_class("任意班级") is True
    
    def test_teacher_can_access_assigned_class(self, teacher_user):
        """教师可访问分配的班级"""
        assert teacher_user.can_access_class("软件1班") is True
        assert teacher_user.can_access_class("软件2班") is True
    
    def test_teacher_cannot_access_other_class(self, teacher_user):
        """教师不可访问未分配的班级"""
        assert teacher_user.can_access_class("计算机1班") is False
    
    def test_teacher_no_assigned_classes(self):
        """无分配班级的教师"""
        user = User(
            username="teacher2",
            name="李老师",
            password=Password.create_from_plain("teacher123"),
            role=UserRole.TEACHER,
            assigned_classes=[]
        )
        
        assert user.can_access_class("软件1班") is False
    
    # ========== 登录失败和锁定测试 ==========
    
    def test_record_login_failure_increments_count(self, admin_user):
        """记录登录失败增加计数"""
        admin_user.record_login_failure()
        
        assert admin_user.login_fail_count == 1
    
    def test_record_login_failure_multiple_times(self, admin_user):
        """多次记录登录失败"""
        for i in range(3):
            admin_user.record_login_failure()
        
        assert admin_user.login_fail_count == 3
    
    def test_lock_after_5_failures(self, admin_user):
        """5次失败后锁定账号"""
        for i in range(5):
            admin_user.record_login_failure()
        
        assert admin_user.status == UserStatus.LOCKED
        assert admin_user.locked_until is not None
    
    def test_is_locked_true_when_locked(self, admin_user):
        """锁定状态返回True"""
        admin_user.lock()
        
        assert admin_user.is_locked() is True
    
    def test_is_locked_false_when_active(self, admin_user):
        """激活状态返回False"""
        assert admin_user.is_locked() is False
    
    def test_is_locked_auto_unlock_when_expired(self, admin_user):
        """锁定过期自动解锁"""
        # 锁定15分钟
        admin_user.lock(minutes=15)
        assert admin_user.is_locked() is True
        
        # 修改锁定时间为过去（模拟过期）
        admin_user.locked_until = datetime.now() - timedelta(minutes=1)
        
        # 检查锁定时自动解锁
        assert admin_user.is_locked() is False
        assert admin_user.status == UserStatus.ACTIVE
    
    def test_unlock_resets_count_and_status(self, admin_user):
        """解锁重置计数和状态"""
        # 先锁定
        for i in range(5):
            admin_user.record_login_failure()
        assert admin_user.login_fail_count == 5
        assert admin_user.status == UserStatus.LOCKED
        
        # 解锁
        admin_user.unlock()
        
        assert admin_user.status == UserStatus.ACTIVE
        assert admin_user.login_fail_count == 0
        assert admin_user.locked_until is None
    
    def test_record_login_success_resets_count(self, admin_user):
        """登录成功重置失败计数"""
        # 先失败几次
        admin_user.record_login_failure()
        admin_user.record_login_failure()
        assert admin_user.login_fail_count == 2
        
        # 登录成功
        admin_user.record_login_success("192.168.1.1")
        
        assert admin_user.login_fail_count == 0
        assert admin_user.last_login_ip == "192.168.1.1"
        assert admin_user.last_login_at is not None
    
    # ========== 班级分配测试 ==========
    
    def test_assign_class_adds_new_class(self, teacher_user):
        """绑定新班级"""
        teacher_user.assign_class("计算机1班")
        
        assert "计算机1班" in teacher_user.assigned_classes
        assert len(teacher_user.assigned_classes) == 3
    
    def test_assign_class_no_duplicate(self, teacher_user):
        """绑定已有班级不重复添加"""
        teacher_user.assign_class("软件1班")  # 已存在
        
        assert teacher_user.assigned_classes.count("软件1班") == 1
        assert len(teacher_user.assigned_classes) == 2
    
    # ========== to_dict 测试 ==========
    
    def test_to_dict(self, teacher_user):
        """转换为字典"""
        data = teacher_user.to_dict()
        
        assert data['id'] == teacher_user.id
        assert data['username'] == "teacher1"
        assert data['name'] == "王老师"
        assert data['role'] == "teacher"
        assert data['assigned_classes'] == ["软件1班", "软件2班"]
        assert data['status'] == "active"
        assert data['last_login_ip'] is None
        assert data['last_login_at'] is None
        assert 'created_at' in data
    
    def test_to_dict_with_login_info(self, teacher_user):
        """有登录信息的to_dict"""
        teacher_user.record_login_success("192.168.1.1")
        
        data = teacher_user.to_dict()
        
        assert data['last_login_ip'] == "192.168.1.1"
        assert data['last_login_at'] is not None
    
    def test_to_dict_datetime_format(self, teacher_user):
        """to_dict中datetime为ISO格式字符串"""
        teacher_user.record_login_success("192.168.1.1")
        
        data = teacher_user.to_dict()
        
        # 验证是字符串格式
        assert isinstance(data['last_login_at'], str)
        assert isinstance(data['created_at'], str)
    
    # ========== 锁定时间测试 ==========
    
    def test_lock_duration_default_15_minutes(self, admin_user):
        """默认锁定15分钟"""
        before = datetime.now()
        admin_user.lock()
        after = datetime.now()
        
        expected_min = before + timedelta(minutes=15)
        expected_max = after + timedelta(minutes=15)
        
        assert expected_min <= admin_user.locked_until <= expected_max
    
    def test_lock_duration_custom(self, admin_user):
        """自定义锁定时间"""
        admin_user.lock(minutes=30)
        
        expected = datetime.now() + timedelta(minutes=30)
        # 允许1秒误差
        assert abs((admin_user.locked_until - expected).total_seconds()) < 1
