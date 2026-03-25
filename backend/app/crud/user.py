"""
用户 CRUD 操作
"""
from datetime import datetime
from typing import List, Optional
from sqlmodel import Session, select
from app.models import User, UserRoleConst


def get_user(session: Session, user_id: int) -> Optional[User]:
    """根据ID获取用户"""
    return session.get(User, user_id)


def get_user_by_username(session: Session, username: str) -> Optional[User]:
    """根据用户名获取用户"""
    query = select(User).where(User.username == username)
    return session.exec(query).first()


def get_users(session: Session, role: Optional[str] = None) -> List[User]:
    """获取用户列表"""
    query = select(User)
    if role:
        query = query.where(User.role == role)
    return session.exec(query).all()


def create_user(session: Session, username: str, name: str, password_hash: str, 
                salt: str, role: str = UserRoleConst.TEACHER, assigned_classes: List[str] = None) -> User:
    """创建用户"""
    import json
    user = User(
        username=username,
        name=name,
        password_hash=password_hash,
        salt=salt,
        role=role,
        assigned_classes=json.dumps(assigned_classes) if assigned_classes else "[]"
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def update_user(session: Session, user: User) -> User:
    """更新用户"""
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def record_login_success(session: Session, user: User, ip: str) -> None:
    """
    记录登录成功 - 带乐观锁保护（BE-008 修复）
    
    使用乐观锁确保并发登录状态更新正确。
    如果检测到版本冲突，自动重试最多3次。
    
    Args:
        session: 数据库会话
        user: 用户对象
        ip: 登录 IP 地址
    """
    from sqlalchemy.exc import IntegrityError
    
    max_retries = 3
    
    for attempt in range(max_retries):
        # 刷新用户对象获取最新版本号
        session.refresh(user)
        
        user.login_fail_count = 0
        user.locked_until = None  # 解锁账户
        user.last_login_ip = ip
        user.last_login = datetime.now()
        
        # 乐观锁：递增版本号（BE-008 修复）
        user.version += 1
        session.add(user)
        
        try:
            session.commit()
            return
        except IntegrityError:
            session.rollback()
            if attempt == max_retries - 1:
                # 最后一次重试失败，静默返回（登录已成功，日志不重要）
                return
            # 继续重试
            continue


def record_login_failure(session: Session, user: User) -> bool:
    """
    记录登录失败，返回是否被锁定 - 带乐观锁保护（BE-008 修复）
    
    使用乐观锁确保并发登录失败计数准确。
    如果检测到版本冲突，自动重试最多3次。
    
    Args:
        session: 数据库会话
        user: 用户对象
        
    Returns:
        bool: 如果用户被锁定返回 True，否则返回 False
    """
    from datetime import timedelta
    from sqlalchemy.exc import IntegrityError
    from app.core.config import get_settings
    
    settings = get_settings()
    max_retries = 3
    
    for attempt in range(max_retries):
        # 刷新用户对象获取最新版本号
        session.refresh(user)
        
        user.login_fail_count += 1
        
        if user.login_fail_count >= settings.security.max_login_failures:
            user.locked_until = datetime.now() + timedelta(
                minutes=settings.security.lockout_duration_minutes
            )
        
        # 乐观锁：递增版本号（BE-008 修复）
        user.version += 1
        session.add(user)
        
        try:
            session.commit()
            return user.locked_until is not None
        except IntegrityError:
            session.rollback()
            if attempt == max_retries - 1:
                # 最后一次重试失败，返回保守结果（视为锁定）
                return True
            # 继续重试
            continue
    
    return False


def reset_password(session: Session, user: User, password_hash: str, salt: str) -> None:
    """重置密码"""
    user.password_hash = password_hash
    user.salt = salt
    user.locked_until = None
    user.login_fail_count = 0
    user.locked_until = None
    session.add(user)
    session.commit()


def delete_user(session: Session, user_id: int) -> bool:
    """删除用户"""
    user = get_user(session, user_id)
    if not user:
        return False
    session.delete(user)
    session.commit()
    return True
