"""
事件模块 - 领域事件和处理器
"""
from app.core.events import Event, ScoreUpdated, StudentCreated, event_bus

__all__ = [
    "Event",
    "ScoreUpdated",
    "StudentCreated",
    "event_bus",
]
