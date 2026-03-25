"""
领域事件处理器 - 处理各类领域事件
"""
from sqlmodel import Session
from app.core.events import ScoreUpdated, event_bus
from app.models import ScoreLog


def handle_score_updated(event: ScoreUpdated) -> None:
    """
    处理分数更新事件 - 记录分数日志
    
    注意：此处理器在事务提交后执行，使用新会话写入日志
    使用延迟导入确保获取正确的数据库引擎（特别是在测试中）
    """
    # 延迟导入 engine，确保获取当前有效的引擎（支持测试中的引擎替换）
    from app.core.db import engine
    with Session(engine) as session:
        score_log = ScoreLog(
            student_id=event.student_id,
            old_score=event.old_score,
            new_score=event.new_score,
            delta=event.delta,
            reason=event.reason,
            operator=event.operator
        )
        session.add(score_log)
        session.commit()


# 注册事件处理器
event_bus.subscribe(ScoreUpdated, handle_score_updated)
