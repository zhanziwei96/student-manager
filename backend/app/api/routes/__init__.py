"""
API 路由导出
"""
from app.api.routes.login import router as login_router
from app.api.routes.students import router as students_router
from app.api.routes.users import router as users_router
from app.api.routes.checkin import router as checkin_router
from app.api.routes.system import router as system_router

__all__ = [
    "login_router",
    "students_router", 
    "users_router",
    "checkin_router",
    "system_router",
]
