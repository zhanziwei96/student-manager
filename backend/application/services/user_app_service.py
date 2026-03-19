"""
用户应用服务
协调用户相关的用例
"""
from typing import List, Optional
from domain.entities.user import User, UserRole, UserStatus
from domain.value_objects.password import Password
from domain.repositories.user_repository import UserRepository
from application.dto.user_dto import (
    CreateUserDTO,
    UpdateUserDTO,
    UserResponseDTO
)


class UserAppService:
    """用户应用服务"""
    
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    def create_user(self, dto: CreateUserDTO) -> UserResponseDTO:
        """
        创建用户用例
        
        Args:
            dto: 创建用户DTO
            
        Returns:
            创建的用户响应DTO
        """
        # 检查用户名是否已存在
        if self.user_repo.exists(dto.username):
            raise ValueError(f"用户名 {dto.username} 已存在")
        
        # 创建密码值对象
        password = Password.create_from_plain(dto.password)
        
        # 解析角色
        try:
            role = UserRole(dto.role)
        except ValueError:
            raise ValueError(f"无效的角色: {dto.role}")
        
        # 创建领域实体
        user = User(
            username=dto.username,
            name=dto.name,
            password=password,
            role=role,
            assigned_classes=dto.assigned_classes or []
        )
        
        # 保存
        self.user_repo.save(user)
        
        return self._to_response_dto(user)
    
    def authenticate_user(self, username: str, password: str, client_ip: str) -> Optional[User]:
        """
        用户认证用例
        
        Args:
            username: 用户名
            password: 明文密码
            client_ip: 客户端IP
            
        Returns:
            认证成功返回用户实体，失败返回None
        """
        user = self.user_repo.find_by_username(username)
        if not user:
            return None
        
        # 检查账号状态
        if not user.is_active():
            raise ValueError("账号已被禁用")
        
        if user.is_locked():
            raise ValueError("账号已被锁定，请稍后再试")
        
        # 验证密码
        if not user.password.verify(password):
            user.record_login_failure()
            self.user_repo.save(user)
            
            if user.is_locked():
                raise ValueError("密码错误次数过多，账号已锁定")
            raise ValueError(f"密码错误（还剩 {5 - user.login_fail_count} 次机会）")
        
        # 登录成功
        user.record_login_success(client_ip)
        self.user_repo.save(user)
        
        return user
    
    def update_user(self, user_id: int, dto: UpdateUserDTO) -> UserResponseDTO:
        """更新用户信息"""
        user = self.user_repo.find_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")
        
        if dto.name:
            user.name = dto.name
        if dto.role:
            user.role = UserRole(dto.role)
        if dto.assigned_classes is not None:
            user.assigned_classes = dto.assigned_classes
        if dto.status:
            user.status = UserStatus(dto.status)
        
        self.user_repo.save(user)
        return self._to_response_dto(user)
    
    def reset_password(self, user_id: int, new_password: str) -> None:
        """重置密码"""
        user = self.user_repo.find_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")
        
        user.password = Password.create_from_plain(new_password)
        user.unlock()  # 同时解锁账号
        self.user_repo.save(user)
    
    def unlock_user(self, user_id: int) -> None:
        """解锁用户"""
        user = self.user_repo.find_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")
        
        user.unlock()
        self.user_repo.save(user)
    
    def delete_user(self, user_id: int) -> None:
        """删除用户"""
        self.user_repo.delete(user_id)
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """
        修改密码
        
        Returns:
            是否修改成功（旧密码是否正确）
        """
        user = self.user_repo.find_by_id(user_id)
        if not user:
            return False
        
        # 验证旧密码
        if not user.password.verify(old_password):
            return False
        
        # 设置新密码
        user.password = Password.create_from_plain(new_password)
        self.user_repo.save(user)
        return True
    
    def get_user_by_id(self, user_id: int) -> Optional[UserResponseDTO]:
        """根据ID获取用户"""
        user = self.user_repo.find_by_id(user_id)
        if user:
            return self._to_response_dto(user)
        return None
    
    def get_all_users(self) -> List[UserResponseDTO]:
        """获取所有用户"""
        users = self.user_repo.find_all()
        return [self._to_response_dto(u) for u in users]
    
    def _to_response_dto(self, user: User) -> UserResponseDTO:
        """将领域实体转换为响应DTO"""
        return UserResponseDTO(
            id=user.id,
            username=user.username,
            name=user.name,
            role=user.role.value,
            assigned_classes=user.assigned_classes,
            status=user.status.value,
            last_login_at=user.last_login_at.isoformat() if user.last_login_at else None
        )
