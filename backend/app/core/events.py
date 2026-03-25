"""
领域事件基础设施 - 内存事件总线实现
参考: Cosmic Python - Chapter 8 Events and Message Bus
"""
from typing import List, Type, Callable, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


class Event:
    """领域事件基类"""
    pass


@dataclass
class ScoreUpdated(Event):
    """分数更新事件"""
    student_id: str
    old_score: float
    new_score: float
    delta: float
    reason: str
    operator: str
    occurred_at: datetime = field(default_factory=datetime.now)


@dataclass
class StudentCreated(Event):
    """学生创建事件"""
    student_id: str
    name: str
    class_name: str
    occurred_at: datetime = field(default_factory=datetime.now)


# 事件处理器类型
Handler = Callable[[Event], None]


class EventBus:
    """
    内存事件总线 - 进程内事件分发
    特点:
    - 同步执行处理器
    - 保持与主事务的一致性
    - 处理器异常会向上传播
    """
    
    def __init__(self):
        self._handlers: Dict[Type[Event], List[Handler]] = {}
    
    def subscribe(self, event_type: Type[Event], handler: Handler) -> None:
        """订阅事件处理器"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def publish(self, event: Event) -> None:
        """发布事件"""
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])
        for handler in handlers:
            handler(event)
    
    def clear(self) -> None:
        """清除所有处理器（用于测试）"""
        self._handlers.clear()


# 全局事件总线实例
event_bus = EventBus()
