"""
Session中间件 - FastAPI版本
基于Starlette的SessionMiddleware封装
"""
from typing import Optional, Any, Dict
from fastapi import Request


class SessionManager:
    """Session管理器"""
    
    @staticmethod
    def get(request: Request, key: str, default: Any = None) -> Any:
        """获取session值"""
        return request.session.get(key, default)
    
    @staticmethod
    def set(request: Request, key: str, value: Any) -> None:
        """设置session值"""
        request.session[key] = value
    
    @staticmethod
    def delete(request: Request, key: str) -> None:
        """删除session值"""
        request.session.pop(key, None)
    
    @staticmethod
    def clear(request: Request) -> None:
        """清空session"""
        request.session.clear()


# 快捷函数
def get_session_user_id(request: Request) -> Optional[int]:
    """获取当前登录用户ID"""
    return request.session.get('user_id')


def get_session_username(request: Request) -> Optional[str]:
    """获取当前登录用户名"""
    return request.session.get('username')


def is_admin(request: Request) -> bool:
    """检查是否是管理员"""
    return request.session.get('is_admin', False)


def require_login(request: Request) -> int:
    """
    要求登录，返回用户ID
    未登录抛出401异常
    """
    user_id = request.session.get('user_id')
    if not user_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail='请先登录')
    return user_id


def require_admin(request: Request) -> int:
    """
    要求管理员权限，返回用户ID
    无权限抛出403异常
    """
    user_id = require_login(request)
    if not request.session.get('is_admin'):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail='需要管理员权限')
    return user_id


def get_session_role(request: Request) -> Optional[str]:
    """获取当前用户角色"""
    return request.session.get('role')


def require_role(request: Request, role: str) -> int:
    """
    要求指定角色权限，返回用户ID
    无权限抛出403异常
    """
    user_id = require_login(request)
    user_role = request.session.get('role')
    if user_role != role:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail=f'需要{role}权限')
    return user_id
