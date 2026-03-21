"""
SQLite 用户仓储测试
使用内存数据库，无需外部依赖
"""
import pytest
from datetime import datetime, timedelta
from domain.entities.user import User, UserRole, UserStatus
from domain.value_objects.password import Password


class TestSQLiteUserRepository:
    """SQLite 用户仓储测试类"""
    
    @pytest.fixture
    def sample_user(self):
        """示例用户"""
        return User(
            username="teacher1",
            name="王老师",
            password=Password.create_from_plain("teacher123"),
            role=UserRole.TEACHER,
            assigned_classes=["软件1班", "软件2班"]
        )
    
    # ========== 保存测试 ==========
    
    def test_save_new_user(self, user_repo):
        """保存新用户"""
        user = User(
            username="teacher1",
            name="王老师",
            password=Password.create_from_plain("teacher123"),
            role=UserRole.TEACHER
        )
        
        user_repo.save(user)
        
        # 验证ID被赋值
        assert user.id is not None
        # 验证能查找到
        found = user_repo.find_by_username("teacher1")
        assert found is not None
    
    def test_save_updates_existing_user(self, user_repo, sample_user):
        """保存已存在的用户（更新）"""
        user_repo.save(sample_user)
        original_id = sample_user.id
        
        # 修改后再次保存
        sample_user.name = "王教授"
        sample_user.role = UserRole.ADMIN
        sample_user.assigned_classes = ["计算机1班"]
        user_repo.save(sample_user)
        
        # 验证更新成功且ID不变
        assert sample_user.id == original_id
        found = user_repo.find_by_username("teacher1")
        assert found.name == "王教授"
        assert found.role == UserRole.ADMIN
        assert found.assigned_classes == ["计算机1班"]
    
    def test_save_preserves_password(self, user_repo):
        """保存保留密码信息"""
        password = Password.create_from_plain("secret123")
        user = User(
            username="teacher1",
            name="王老师",
            password=password,
            role=UserRole.TEACHER
        )
        
        user_repo.save(user)
        
        found = user_repo.find_by_username("teacher1")
        assert found.password.verify("secret123") is True
    
    # ========== 查询测试 ==========
    
    def test_find_by_id_exists(self, user_repo, sample_user):
        """通过ID查找存在的用户"""
        user_repo.save(sample_user)
        user_id = sample_user.id
        
        found = user_repo.find_by_id(user_id)
        
        assert found is not None
        assert found.username == "teacher1"
        assert found.name == "王老师"
    
    def test_find_by_id_not_exists(self, user_repo):
        """通过ID查找不存在的用户"""
        found = user_repo.find_by_id(99999)
        
        assert found is None
    
    def test_find_by_username_exists(self, user_repo, sample_user):
        """通过用户名查找存在的用户"""
        user_repo.save(sample_user)
        
        found = user_repo.find_by_username("teacher1")
        
        assert found is not None
        assert found.username == "teacher1"
        assert found.name == "王老师"
        assert found.role == UserRole.TEACHER
        assert found.assigned_classes == ["软件1班", "软件2班"]
    
    def test_find_by_username_not_exists(self, user_repo):
        """通过用户名查找不存在的用户"""
        found = user_repo.find_by_username("nonexistent")
        
        assert found is None
    
    def test_find_all(self, user_repo):
        """查找所有用户"""
        user_repo.save(User(
            username="admin",
            name="管理员",
            password=Password.create_from_plain("admin123"),
            role=UserRole.ADMIN
        ))
        user_repo.save(User(
            username="teacher1",
            name="王老师",
            password=Password.create_from_plain("teacher123"),
            role=UserRole.TEACHER
        ))
        
        users = user_repo.find_all()
        
        assert len(users) == 2
        usernames = [u.username for u in users]
        assert "admin" in usernames
        assert "teacher1" in usernames
    
    def test_find_by_class(self, user_repo):
        """通过班级查找老师"""
        user_repo.save(User(
            username="teacher1",
            name="王老师",
            password=Password.create_from_plain("teacher123"),
            role=UserRole.TEACHER,
            assigned_classes=["软件1班", "软件2班"]
        ))
        user_repo.save(User(
            username="teacher2",
            name="李老师",
            password=Password.create_from_plain("teacher123"),
            role=UserRole.TEACHER,
            assigned_classes=["软件1班"]
        ))
        
        teachers = user_repo.find_by_class("软件1班")
        
        assert len(teachers) == 2
    
    def test_find_by_class_not_found(self, user_repo):
        """通过班级查找（无结果）"""
        user_repo.save(User(
            username="teacher1",
            name="王老师",
            password=Password.create_from_plain("teacher123"),
            role=UserRole.TEACHER,
            assigned_classes=["软件1班"]
        ))
        
        teachers = user_repo.find_by_class("计算机1班")
        
        assert teachers == []
    
    # ========== 删除测试 ==========
    
    def test_delete_existing_user(self, user_repo, sample_user):
        """删除存在的用户"""
        user_repo.save(sample_user)
        user_id = sample_user.id
        assert user_repo.find_by_id(user_id) is not None
        
        user_repo.delete(user_id)
        
        assert user_repo.find_by_id(user_id) is None
    
    def test_delete_nonexistent_user(self, user_repo):
        """删除不存在的用户（不报错）"""
        user_repo.delete(99999)  # 应该不抛出异常
    
    # ========== 存在性测试 ==========
    
    def test_exists_true(self, user_repo, sample_user):
        """用户存在返回True"""
        user_repo.save(sample_user)
        
        assert user_repo.exists("teacher1") is True
    
    def test_exists_false(self, user_repo):
        """用户不存在返回False"""
        assert user_repo.exists("nonexistent") is False
    
    # ========== 用户状态测试 ==========
    
    def test_save_and_load_user_status(self, user_repo):
        """保存和加载用户状态"""
        user = User(
            username="teacher1",
            name="王老师",
            password=Password.create_from_plain("teacher123"),
            role=UserRole.TEACHER,
            status=UserStatus.INACTIVE
        )
        user_repo.save(user)
        
        found = user_repo.find_by_username("teacher1")
        assert found.status == UserStatus.INACTIVE
    
    def test_save_and_load_locked_user(self, user_repo):
        """保存和加载锁定用户"""
        user = User(
            username="teacher1",
            name="王老师",
            password=Password.create_from_plain("teacher123"),
            role=UserRole.TEACHER,
            status=UserStatus.LOCKED,
            locked_until=datetime.now() + timedelta(minutes=30),
            login_fail_count=5
        )
        user_repo.save(user)
        
        found = user_repo.find_by_username("teacher1")
        assert found.status == UserStatus.LOCKED
        assert found.locked_until is not None
        assert found.login_fail_count == 5
    
    def test_save_and_load_login_info(self, user_repo):
        """保存和加载登录信息"""
        user = User(
            username="teacher1",
            name="王老师",
            password=Password.create_from_plain("teacher123"),
            role=UserRole.TEACHER,
            last_login_ip="192.168.1.1",
            last_login_at=datetime.now()
        )
        user_repo.save(user)
        
        found = user_repo.find_by_username("teacher1")
        assert found.last_login_ip == "192.168.1.1"
        assert found.last_login_at is not None
    
    # ========== 班级分配测试 ==========
    
    def test_save_user_with_multiple_classes(self, user_repo):
        """保存带多个班级的用户"""
        user = User(
            username="teacher1",
            name="王老师",
            password=Password.create_from_plain("teacher123"),
            role=UserRole.TEACHER,
            assigned_classes=["软件1班", "软件2班", "计算机1班"]
        )
        user_repo.save(user)
        
        found = user_repo.find_by_username("teacher1")
        assert len(found.assigned_classes) == 3
        assert "软件1班" in found.assigned_classes
        assert "软件2班" in found.assigned_classes
        assert "计算机1班" in found.assigned_classes
    
    def test_save_user_with_empty_classes(self, user_repo):
        """保存无班级的用户"""
        user = User(
            username="admin",
            name="管理员",
            password=Password.create_from_plain("admin123"),
            role=UserRole.ADMIN,
            assigned_classes=[]
        )
        user_repo.save(user)
        
        found = user_repo.find_by_username("admin")
        assert found.assigned_classes == []
