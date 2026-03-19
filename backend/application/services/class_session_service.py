"""
课堂会话服务 - 管理当前上课状态
这是一个内存状态服务，不持久化到数据库
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class ClassSession:
    """课堂会话"""
    class_name: str
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_by: Optional[int] = None
    active: bool = True


class ClassSessionService:
    """
    课堂会话服务
    使用Flask session存储当前课堂状态
    """
    SESSION_KEY = 'current_class_session'
    
    @staticmethod
    def get_session() -> Optional[ClassSession]:
        """获取当前课堂会话"""
        from flask import session
        data = session.get(ClassSessionService.SESSION_KEY)
        if data:
            return ClassSession(**data)
        return None
    
    @staticmethod
    def set_session(class_name: str, user_id: int) -> ClassSession:
        """设置当前课堂会话"""
        from flask import session
        session_data = {
            'class_name': class_name,
            'started_at': datetime.now().isoformat(),
            'started_by': user_id,
            'active': True
        }
        session[ClassSessionService.SESSION_KEY] = session_data
        return ClassSession(**session_data)
    
    @staticmethod
    def clear_session():
        """清除课堂会话"""
        from flask import session
        session.pop(ClassSessionService.SESSION_KEY, None)
    
    @staticmethod
    def is_active() -> bool:
        """检查是否有活跃的课堂会话"""
        session = ClassSessionService.get_session()
        return session is not None and session.active
