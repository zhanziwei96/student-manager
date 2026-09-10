"""
API 路由导出
"""
from app.api.routes.login import router as login_router
from app.api.routes.students import router as students_router
from app.api.routes.users import router as users_router
from app.api.routes.checkin import router as checkin_router
from app.api.routes.system import router as system_router
from app.api.routes.schedules import router as schedules_router
from app.api.routes.course_sessions import router as course_sessions_router
from app.api.routes.schedule_adjustments import router as schedule_adjustments_router
from app.api.routes.groups import router as groups_router
from app.api.routes.questions import router as questions_router
from app.api.routes.lost_found import router as lost_found_router
from app.api.routes.term import router as term_router
from app.api.routes.group_scores import router as group_scores_router
from app.api.routes.enrollments import router as enrollments_router
from app.api.routes.semesters import router as semesters_router
from app.api.routes.cohorts import router as cohorts_router
from app.api.routes.classes import router as classes_router
from app.api.routes.courses import router as courses_router
from app.api.routes.course_offerings import router as course_offerings_router
from app.api.routes.rankings import router as rankings_router

__all__ = [
    "login_router",
    "students_router",
    "users_router",
    "checkin_router",
    "system_router",
    "schedules_router",
    "course_sessions_router",
    "schedule_adjustments_router",
    "groups_router",
    "questions_router",
    "lost_found_router",
    "term_router",
    "group_scores_router",
    "enrollments_router",
    "semesters_router",
    "cohorts_router",
    "classes_router",
    "courses_router",
    "course_offerings_router",
    "rankings_router",
]
