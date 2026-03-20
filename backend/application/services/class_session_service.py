"""
课堂会话服务 - 管理当前上课状态
这是一个内存状态服务，不持久化到数据库
"""
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field, asdict
from fastapi import Request


@dataclass
class ClassSession:
    """课堂会话"""
    class_name: str
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_by: Optional[int] = None
    active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


class ClassSessionService:
    """
    课堂会话服务
    使用请求session存储当前课堂状态
    """
    SESSION_KEY = 'current_class_session'
    
    @staticmethod
    def get_session(request: Request) -> Optional[ClassSession]:
        """获取当前课堂会话"""
        data = request.session.get(ClassSessionService.SESSION_KEY)
        if data:
            return ClassSession(**data)
        return None
    
    @staticmethod
    def set_session(request: Request, class_name: str, user_id: int) -> ClassSession:
        """设置当前课堂会话"""
        session_data = {
            'class_name': class_name,
            'started_at': datetime.now().isoformat(),
            'started_by': user_id,
            'active': True
        }
        request.session[ClassSessionService.SESSION_KEY] = session_data
        return ClassSession(**session_data)
    
    @staticmethod
    def clear_session(request: Request):
        """清除课堂会话"""
        request.session.pop(ClassSessionService.SESSION_KEY, None)
    
    @staticmethod
    def is_active(request: Request) -> bool:
        """检查是否有活跃的课堂会话"""
        session = ClassSessionService.get_session(request)
        return session is not None and session.active
