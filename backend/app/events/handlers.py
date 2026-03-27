"""
领域事件处理器 - 处理各类领域事件

注意：核心副作用（如ScoreLog记录）应在主事务中完成
事件处理器仅用于非核心副作用（通知、统计、缓存更新等）
"""
from app.core.events import ScoreUpdated, event_bus


def handle_score_updated(event: ScoreUpdated) -> None:
    """
    处理分数更新事件 - 非核心副作用
    
    注意：ScoreLog记录已在主事务中完成（见 student.py update_student_score）
    此处理器仅用于其他副作用，如：
    - 发送实时通知（WebSocket）
    - 更新统计缓存
    - 触发外部系统集成
    
    当前实现为占位，后续可扩展上述功能
    
    Args:
        event: 分数更新事件
    """
    # 核心数据（ScoreLog）已在主事务中记录
    # 此处仅处理扩展副作用
    # TODO: 添加 WebSocket 实时通知
    # TODO: 更新班级平均分缓存
    pass


# 注册事件处理器
event_bus.subscribe(ScoreUpdated, handle_score_updated)
