"""
用户应用服务单元测试
使用 Mock Repository 验证用例编排逻辑
"""
import pytest
from datetime import datetime, timedelta

from domain.entities.user import User, UserRole, UserStatus
from domain.value_objects.password import Password
from application.dto.user_dto import CreateUserDTO, UpdateUserDTO


class TestUserAppService:
    """用户应用服务测试类"""
    
    def test_create_user_success(self, user_app_service, mock_user_repo):
        """测试成功创建用户"""
        # Arrange
        dto = CreateUserDTO(
            username="teacher1",
            password="password123",
            name="王老师",
            role="teacher",
            assigned_classes=["软件1班", "软件2班"]
        )
        
        # Act
        result = user_app_service.create_user(dto)
        
        # Assert
        assert result is not None
        assert result.username == "teacher1"
        assert result.name == "王老师"
        assert result.role == "teacher"
        assert result.assigned_classes == ["软件1班", "软件2班"]
        assert result.status == "active"
        
        # 验证仓储中保存了实体
        saved = mock_user_repo.find_by_username("teacher1")
        assert saved is not None
        assert saved.username == "teacher1"
        assert saved.password.verify("password123")  # 密码正确加密
    
    def test_create_user_duplicate_username(self, user_app_service, mock_user_repo):
        """测试创建重复用户名失败"""
        # Arrange - 先创建一个用户
        dto = CreateUserDTO(username="teacher1", password="pass123", name="王老师", role="teacher")
        user_app_service.create_user(dto)
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            user_app_service.create_user(dto)
        assert "已存在" in str(exc_info.value)
    
    def test_create_user_invalid_role(self, user_app_service):
        """测试创建用户时无效角色"""
        # Arrange
        dto = CreateUserDTO(
            username="user1",
            password="pass123",
            name="用户1",
            role="invalid_role"
        )
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            user_app_service.create_user(dto)
        assert "无效的角色" in str(exc_info.value)
    
    def test_authenticate_user_success(self, user_app_service, mock_user_repo):
        """测试用户认证成功"""
        # Arrange
        user = User(
            username="teacher1",
            name="王老师",
            password=Password.create_from_plain("password123"),
            role=UserRole.TEACHER
        )
        mock_user_repo.save(user)
        
        # Act
        result = user_app_service.authenticate_user("teacher1", "password123", "192.168.1.1")
        
        # Assert
        assert result is not None
        assert result.username == "teacher1"
        assert result.last_login_ip == "192.168.1.1"
        assert result.login_fail_count == 0
    
    def test_authenticate_user_wrong_password(self, user_app_service, mock_user_repo):
        """测试用户认证密码错误"""
        # Arrange
        user = User(
            username="teacher1",
            name="王老师",
            password=Password.create_from_plain("password123"),
            role=UserRole.TEACHER
        )
        mock_user_repo.save(user)
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            user_app_service.authenticate_user("teacher1", "wrong_password", "192.168.1.1")
        assert "密码错误" in str(exc_info.value)
        
        # 验证登录失败次数增加
        saved = mock_user_repo.find_by_username("teacher1")
        assert saved.login_fail_count == 1
    
    def test_authenticate_user_not_found(self, user_app_service):
        """测试认证不存在的用户"""
        # Act
        result = user_app_service.authenticate_user("nonexistent", "password", "192.168.1.1")
        
        # Assert
        assert result is None
    
    def test_authenticate_user_inactive(self, user_app_service, mock_user_repo):
        """测试认证已禁用的用户"""
        # Arrange
        user = User(
            username="teacher1",
            name="王老师",
            password=Password.create_from_plain("password123"),
            role=UserRole.TEACHER,
            status=UserStatus.INACTIVE
        )
        mock_user_repo.save(user)
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            user_app_service.authenticate_user("teacher1", "password123", "192.168.1.1")
        assert "已被禁用" in str(exc_info.value)
    
    def test_authenticate_user_locked(self, user_app_service, mock_user_repo):
        """测试认证已锁定的用户"""
        # Arrange
        user = User(
            username="teacher1",
            name="王老师",
            password=Password.create_from_plain("password123"),
            role=UserRole.TEACHER,
            status=UserStatus.LOCKED,
            locked_until=datetime.now() + timedelta(minutes=30)
        )
        mock_user_repo.save(user)
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            user_app_service.authenticate_user("teacher1", "password123", "192.168.1.1")
        assert "已被锁定" in str(exc_info.value)
    
    def test_authenticate_user_lock_after_max_failures(self, user_app_service, mock_user_repo):
        """测试多次失败后被锁定"""
        # Arrange
        user = User(
            username="teacher1",
            name="王老师",
            password=Password.create_from_plain("password123"),
            role=UserRole.TEACHER
        )
        mock_user_repo.save(user)
        
        # Act - 连续错误5次
        for i in range(4):
            with pytest.raises(ValueError):
                user_app_service.authenticate_user("teacher1", "wrong", "192.168.1.1")
        
        # 第5次错误应该触发锁定
        with pytest.raises(ValueError) as exc_info:
            user_app_service.authenticate_user("teacher1", "wrong", "192.168.1.1")
        assert "已锁定" in str(exc_info.value)
    
    def test_get_user_by_id_exists(self, user_app_service, mock_user_repo):
        """测试获取存在的用户"""
        # Arrange
        user = User(
            id=1,
            username="teacher1",
            name="王老师",
            password=Password.create_from_plain("password123"),
            role=UserRole.TEACHER
        )
        mock_user_repo.save(user)
        
        # Act
        result = user_app_service.get_user_by_id(1)
        
        # Assert
        assert result is not None
        assert result.username == "teacher1"
        assert result.name == "王老师"
    
    def test_get_user_by_id_not_exists(self, user_app_service):
        """测试获取不存在的用户"""
        # Act
        result = user_app_service.get_user_by_id(999)
        
        # Assert
        assert result is None
    
    def test_get_all_users(self, user_app_service, mock_user_repo):
        """测试获取所有用户"""
        # Arrange
        mock_user_repo.save(User(username="teacher1", name="王老师", password=Password.create_from_plain("password1"), role=UserRole.TEACHER))
        mock_user_repo.save(User(username="teacher2", name="李老师", password=Password.create_from_plain("password2"), role=UserRole.TEACHER))
        
        # Act
        results = user_app_service.get_all_users()
        
        # Assert
        assert len(results) == 2
        usernames = [r.username for r in results]
        assert "teacher1" in usernames
        assert "teacher2" in usernames
    
    def test_update_user_success(self, user_app_service, mock_user_repo):
        """测试成功更新用户"""
        # Arrange
        user = User(
            id=1,
            username="teacher1",
            name="王老师",
            password=Password.create_from_plain("password123"),
            role=UserRole.TEACHER,
            assigned_classes=["软件1班"]
        )
        mock_user_repo.save(user)
        
        dto = UpdateUserDTO(
            name="王教授",
            role="admin",
            assigned_classes=["软件1班", "软件2班"],
            status="active"
        )
        
        # Act
        result = user_app_service.update_user(1, dto)
        
        # Assert
        assert result.name == "王教授"
        assert result.role == "admin"
        assert result.assigned_classes == ["软件1班", "软件2班"]
    
    def test_update_user_not_found(self, user_app_service):
        """测试更新不存在的用户"""
        # Arrange
        dto = UpdateUserDTO(name="新名字")
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            user_app_service.update_user(999, dto)
        assert "不存在" in str(exc_info.value)
    
    def test_reset_password(self, user_app_service, mock_user_repo):
        """测试重置密码"""
        # Arrange
        user = User(
            id=1,
            username="teacher1",
            name="王老师",
            password=Password.create_from_plain("old_password"),
            role=UserRole.TEACHER,
            status=UserStatus.LOCKED,
            login_fail_count=5
        )
        mock_user_repo.save(user)
        
        # Act
        user_app_service.reset_password(1, "new_password")
        
        # Assert
        saved = mock_user_repo.find_by_id(1)
        assert saved.password.verify("new_password")
        assert saved.status == UserStatus.ACTIVE  # 解锁
        assert saved.login_fail_count == 0
    
    def test_unlock_user(self, user_app_service, mock_user_repo):
        """测试解锁用户"""
        # Arrange
        user = User(
            id=1,
            username="teacher1",
            name="王老师",
            password=Password.create_from_plain("password123"),
            role=UserRole.TEACHER,
            status=UserStatus.LOCKED,
            login_fail_count=5,
            locked_until=datetime.now() + timedelta(minutes=30)
        )
        mock_user_repo.save(user)
        
        # Act
        user_app_service.unlock_user(1)
        
        # Assert
        saved = mock_user_repo.find_by_id(1)
        assert saved.status == UserStatus.ACTIVE
        assert saved.login_fail_count == 0
        assert saved.locked_until is None
    
    def test_delete_user(self, user_app_service, mock_user_repo):
        """测试删除用户"""
        # Arrange
        user = User(
            id=1,
            username="teacher1",
            name="王老师",
            password=Password.create_from_plain("password123"),
            role=UserRole.TEACHER
        )
        mock_user_repo.save(user)
        assert mock_user_repo.find_by_id(1) is not None
        
        # Act
        user_app_service.delete_user(1)
        
        # Assert
        assert mock_user_repo.find_by_id(1) is None
    
    def test_change_password_success(self, user_app_service, mock_user_repo):
        """测试成功修改密码"""
        # Arrange
        user = User(
            id=1,
            username="teacher1",
            name="王老师",
            password=Password.create_from_plain("old_password"),
            role=UserRole.TEACHER
        )
        mock_user_repo.save(user)
        
        # Act
        result = user_app_service.change_password(1, "old_password", "new_password")
        
        # Assert
        assert result is True
        saved = mock_user_repo.find_by_id(1)
        assert saved.password.verify("new_password")
    
    def test_change_password_wrong_old_password(self, user_app_service, mock_user_repo):
        """测试修改密码时旧密码错误"""
        # Arrange
        user = User(
            id=1,
            username="teacher1",
            name="王老师",
            password=Password.create_from_plain("correct_password"),
            role=UserRole.TEACHER
        )
        mock_user_repo.save(user)
        
        # Act
        result = user_app_service.change_password(1, "wrong_password", "new_password")
        
        # Assert
        assert result is False
        saved = mock_user_repo.find_by_id(1)
        assert saved.password.verify("correct_password")  # 密码未变
    
    def test_change_password_user_not_found(self, user_app_service):
        """测试修改不存在的用户密码"""
        # Act
        result = user_app_service.change_password(999, "old", "new")
        
        # Assert
        assert result is False
