"""
课堂调度器 - 自动激活 scheduled 状态的课堂
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlmodel import Session, select
from app.core.db import engine
from app.models import CourseSession


def activate_scheduled_sessions():
    """激活已到时间的 scheduled 课堂"""
    with Session(engine) as session:
        now = datetime.now(ZoneInfo("Asia/Shanghai"))

        # 查询所有已到开始时间的 scheduled 课堂
        statement = select(CourseSession).where(
            CourseSession.status == "scheduled",
            CourseSession.start_time <= now
        )
        scheduled_sessions = session.exec(statement).all()

        for cs in scheduled_sessions:
            cs.status = "active"
            session.add(cs)

        if scheduled_sessions:
            session.commit()
            print(f"Activated {len(scheduled_sessions)} scheduled sessions")

        return len(scheduled_sessions)


def setup_scheduler():
    """设置定时任务（在应用启动时调用）"""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler

        scheduler = BackgroundScheduler()
        # 每分钟检查一次
        scheduler.add_job(activate_scheduled_sessions, 'interval', minutes=1)
        scheduler.start()
        return scheduler
    except ImportError:
        print("APScheduler not installed, scheduler disabled")
        return None
