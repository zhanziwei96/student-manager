"""
领域事件基础设施 - 内存事件总线实现
参考: Cosmic Python - Chapter 8 Events and Message Bus
"""
from typing import List, Type, Callable, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging


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
    - 限制每种事件类型的最大处理器数，防止内存泄漏
    """

    # 每种事件类型的最大处理器数量
    MAX_HANDLERS_PER_EVENT = 100

    def __init__(self, max_handlers_per_event: int = 100):
        self._handlers: Dict[Type[Event], List[Handler]] = {}
        self._max_handlers = max_handlers_per_event
        self._logger = logging.getLogger(__name__)

    def subscribe(self, event_type: Type[Event], handler: Handler) -> None:
        """
        订阅事件处理器

        Args:
            event_type: 事件类型
            handler: 处理器函数

        Raises:
            RuntimeError: 如果处理器数量超过限制或重复注册
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        handlers = self._handlers[event_type]

        # 检查是否已注册（防止重复注册）
        if handler in handlers:
            self._logger.warning(f"处理器 {handler.__name__} 已注册到 {event_type.__name__}，跳过")
            return

        # 检查处理器数量限制
        if len(handlers) >= self._max_handlers:
            raise RuntimeError(
                f"事件 {event_type.__name__} 的处理器数量已达上限 ({self._max_handlers})"
            )

        handlers.append(handler)

    def unsubscribe(self, event_type: Type[Event], handler: Handler) -> bool:
        """
        取消订阅事件处理器

        Args:
            event_type: 事件类型
            handler: 处理器函数

        Returns:
            bool: 是否成功移除
        """
        handlers = self._handlers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)
            # 如果没有处理器了，清理该事件类型的条目
            if not handlers:
                del self._handlers[event_type]
            return True
        return False

    def publish(self, event: Event) -> None:
        """发布事件"""
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])
        for handler in handlers:
            handler(event)

    def clear(self) -> None:
        """清除所有处理器（用于测试）"""
        self._handlers.clear()

    def clear_event(self, event_type: Type[Event]) -> bool:
        """
        清除指定事件类型的所有处理器

        Args:
            event_type: 事件类型

        Returns:
            bool: 是否存在该事件类型并清除
        """
        if event_type in self._handlers:
            del self._handlers[event_type]
            return True
        return False

    def get_handler_count(self, event_type: Optional[Type[Event]] = None) -> int:
        """
        获取处理器数量

        Args:
            event_type: 事件类型，为 None 时返回所有处理器的总数

        Returns:
            int: 处理器数量
        """
        if event_type:
            return len(self._handlers.get(event_type, []))
        return sum(len(handlers) for handlers in self._handlers.values())


# 全局事件总线实例
event_bus = EventBus()
