"""
用户 CRUD 单元测试 - SEC-003: 移除 salt 参数
"""
import pytest
from datetime import datetime
from sqlmodel import Session
from app.crud import (
    get_user, get_user_by_username, get_users, create_user,
    update_user, record_login_success, record_login_failure,
    reset_password, delete_user
)
from app.models import User
from app.core.security import hash_password, verify_password


class TestUserCRUD:
    """测试用户 CRUD 操作"""
    
    def test_create_user(self, session: Session):
        """测试创建用户 - SEC-003: 简化密码哈希接口"""
        password_hash = hash_password("password123")
        
        user = create_user(
            session,
            username="new_teacher",
            name="新教师",
            password_hash=password_hash,
            role="teacher",
            assigned_classes=["软件1班"]
        )
        
        assert user.username == "new_teacher"
        assert user.name == "新教师"
        assert user.role == "teacher"
        assert user.get_assigned_classes() == ["软件1班"]
    
    def test_get_user_by_id(self, session: Session):
        """测试根据ID获取用户"""
        password_hash = hash_password("password123")
        user = create_user(session, "teacher1", "教师1", password_hash)
        
        found = get_user(session, user.id)
        assert found is not None
        assert found.username == "teacher1"
    
    def test_get_user_by_username(self, session: Session):
        """测试根据用户名获取用户"""
        password_hash = hash_password("password123")
        create_user(session, "teacher2", "教师2", password_hash)
        
        found = get_user_by_username(session, "teacher2")
        assert found is not None
        assert found.name == "教师2"
    
    def test_get_user_not_found(self, session: Session):
        """测试获取不存在的用户"""
        user = get_user_by_username(session, "not_exist")
        assert user is None
    
    def test_get_users(self, session: Session):
        """测试获取所有用户"""
        password_hash = hash_password("password123")
        create_user(session, "admin1", "管理员", password_hash, role="admin")
        create_user(session, "teacher3", "教师3", password_hash, role="teacher")
        
        users = get_users(session)
        assert len(users) == 2
    
    def test_get_users_by_role(self, session: Session):
        """测试按角色获取用户"""
        password_hash = hash_password("password123")
        create_user(session, "admin2", "管理员", password_hash, role="admin")
        create_user(session, "teacher4", "教师4", password_hash, role="teacher")
        
        admins = get_users(session, role="admin")
        assert len(admins) == 1
        assert admins[0].role == "admin"
    
    def test_record_login_success(self, session: Session):
        """测试记录登录成功"""
        password_hash = hash_password("password123")
        user = create_user(session, "teacher5", "教师5", password_hash)
        user.login_fail_count = 3  # 设置一些失败次数
        
        record_login_success(session, user, "127.0.0.1")
        
        assert user.login_fail_count == 0
        assert user.last_login_ip == "127.0.0.1"
        assert user.last_login is not None
    
    def test_record_login_failure(self, session: Session):
        """测试记录登录失败"""
        password_hash = hash_password("password123")
        user = create_user(session, "teacher6", "教师6", password_hash)
        
        # 连续失败9次
        for i in range(9):
            is_locked = record_login_failure(session, user)
            assert is_locked is False
        
        assert user.login_fail_count == 9
        
        # 第10次失败应该锁定
        is_locked = record_login_failure(session, user)
        assert is_locked is True
        assert user.locked_until is not None
    
    def test_reset_password(self, session: Session):
        """测试重置密码 - SEC-003: 简化密码哈希接口"""
        password_hash = hash_password("password123")
        user = create_user(session, "teacher7", "教师7", password_hash)
        user.login_fail_count = 5
        user.locked_until = datetime.now()
        
        new_hash = hash_password("newpassword")
        reset_password(session, user, new_hash)
        
        assert user.password_hash == new_hash
        assert user.login_fail_count == 0
        assert user.locked_until is None
    
    def test_delete_user(self, session: Session):
        """测试删除用户"""
        password_hash = hash_password("password123")
        user = create_user(session, "teacher8", "教师8", password_hash)
        
        success = delete_user(session, user.id)
        assert success is True
        
        # 确认已删除
        found = get_user(session, user.id)
        assert found is None
    
    def test_delete_user_not_found(self, session: Session):
        """测试删除不存在的用户"""
        success = delete_user(session, 99999)
        assert success is False
    
    def test_update_user(self, session: Session):
        """测试更新用户信息 - SEC-003: 简化密码哈希接口"""
        password_hash = hash_password("password123")
        user = create_user(
            session, 
            "teacher9", 
            "教师9", 
            password_hash,
            role="teacher",
            assigned_classes=["软件1班"]
        )
        
        # 修改用户信息
        user.name = "修改后的教师名"
        user.role = "admin"
        user.set_assigned_classes(["软件1班", "软件2班"])
        
        updated = update_user(session, user)
        
        assert updated.name == "修改后的教师名"
        assert updated.role == "admin"
        assert updated.get_assigned_classes() == ["软件1班", "软件2班"]
    
    def test_record_login_failure_not_locked(self, session: Session):
        """测试登录失败但未达到锁定阈值"""
        password_hash = hash_password("password123")
        user = create_user(session, "teacher10", "教师10", password_hash)
        
        # 失败1次
        is_locked = record_login_failure(session, user)
        
        assert is_locked is False
        assert user.login_fail_count == 1
        assert user.locked_until is None

    def test_update_user_info(self, session: Session):
        """测试 update_user_info - 架构分层修复"""
        from app.crud import update_user_info
        
        password_hash = hash_password("password123")
        user = create_user(
            session, 
            "teacher_update", 
            "原始姓名", 
            password_hash,
            role="teacher",
            assigned_classes=["软件1班"]
        )
        
        # 使用 update_user_info 更新用户信息
        updated = update_user_info(
            session=session,
            user=user,
            name="更新后的姓名",
            role="admin",
            assigned_classes=["软件1班", "软件2班"],
            is_account_enabled=False
        )
        
        assert updated.name == "更新后的姓名"
        assert updated.role == "admin"
        assert updated.get_assigned_classes() == ["软件1班", "软件2班"]
        assert updated.is_account_enabled is False

    def test_update_user_password(self, session: Session):
        """测试 update_user_password - 架构分层修复"""
        from app.crud import update_user_password
        from app.core.security import verify_password
        
        password_hash = hash_password("old_password")
        user = create_user(session, "teacher_pwd", "教师密码", password_hash)
        
        # 更新密码
        update_user_password(session, user, "new_password123")
        
        # 验证新密码有效
        assert verify_password("new_password123", user.password_hash) is True
        assert verify_password("old_password", user.password_hash) is False

    def test_update_user_info_partial(self, session: Session):
        """测试 update_user_info 部分更新 - 架构分层修复"""
        from app.crud import update_user_info
        
        password_hash = hash_password("password123")
        user = create_user(
            session, 
            "teacher_partial", 
            "原始姓名", 
            password_hash,
            role="teacher",
            assigned_classes=["软件1班"]
        )
        original_role = user.role
        
        # 只更新 name，其他字段为 None（不应被修改）
        updated = update_user_info(
            session=session,
            user=user,
            name="仅更新姓名",
            role=None,  # 不更新
            assigned_classes=None,  # 不更新
            is_account_enabled=None  # 不更新
        )
        
        assert updated.name == "仅更新姓名"
        assert updated.role == original_role  # 保持不变
        assert updated.get_assigned_classes() == ["软件1班"]  # 保持不变


class TestDeleteUserCascade:
    """测试删除用户级联处理（H-08 修复）"""

    def test_delete_user_with_schedules_blocked(self, session: Session):
        """测试删除有关联课表的教师被阻止"""
        from app.crud.user import delete_user
        from app.models import CourseSchedule
        from fastapi import HTTPException

        # 创建教师
        password_hash = hash_password("password123")
        user = create_user(
            session,
            "teacher_with_schedule",
            "有课表的教师",
            password_hash,
            role="teacher"
        )

        # 创建课表
        schedule = CourseSchedule(
            course_name="测试课程",
            class_name="测试班级",
            teacher_id=user.id,
            teacher_name=user.name,
            day_of_week=1,
            start_time="08:00",
            end_time="09:40"
        )
        session.add(schedule)
        session.commit()

        # 尝试删除教师应失败
        with pytest.raises(HTTPException) as exc_info:
            delete_user(session, user.id)

        assert exc_info.value.status_code == 400
        assert "有关联" in exc_info.value.detail
        assert "1 个课程" in exc_info.value.detail

        # 清理
        session.delete(schedule)
        session.commit()
        delete_user(session, user.id)

    def test_delete_user_without_schedules_success(self, session: Session):
        """测试删除无关联课表的教师成功"""
        from app.crud.user import delete_user

        # 创建教师
        password_hash = hash_password("password123")
        user = create_user(
            session,
            "teacher_no_schedule",
            "无课表的教师",
            password_hash,
            role="teacher"
        )

        # 删除应成功
        result = delete_user(session, user.id)
        assert result is True

        # 验证已删除
        deleted = session.get(User, user.id)
        assert deleted is None
