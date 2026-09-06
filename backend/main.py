"""
班级管理系统 - FastAPI + SQLModel 架构主入口
前后端完全分离，后端只提供API
"""
import os

# 配置环境 - 必须在导入应用代码前执行
# 将配置加载逻辑集中到 config.py，避免逻辑分散
from app.core.config import configure_environment
configure_environment()

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings
from app.core.db import init_db
from app.core.logging import logger
from app.core.exceptions import http_exception_handler, validation_exception_handler
from fastapi.exceptions import RequestValidationError

# 获取应用配置
settings = get_settings()

# 静态文件目录
STATIC_DIR = os.path.join(os.path.dirname(__file__), "../frontend/dist")
# Docker 环境中前端文件在 /var/www/html
if not os.path.exists(STATIC_DIR):
    STATIC_DIR = "/var/www/html"


class CacheControlMiddleware(BaseHTTPMiddleware):
    """
    缓存控制中间件
    - index.html: 禁止缓存（确保总是获取最新版本）
    - 静态资源（CSS/JS）: 允许缓存1小时
    """
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        path = request.url.path

        # index.html 和根路径：完全禁止缓存
        if path == "/" or path.endswith("index.html"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        # API 请求：禁止缓存
        elif path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        # 其他静态资源（CSS/JS/图片）：允许缓存1小时
        else:
            response.headers["Cache-Control"] = "public, max-age=3600"

        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    # 启动时执行
    logger.info("=" * 50)
    logger.info("班级管理系统 FastAPI + SQLModel 架构")
    logger.info("=" * 50)
    logger.info(f"数据库: {settings.get_database_url()}")
    
    # 初始化数据库
    init_db()
    
    # 导入并注册领域事件处理器
    # 这会触发 handlers.py 中的事件处理器注册
    from app.events import handlers  # noqa: F401
    logger.info("领域事件处理器已注册")
    
    # 初始化限流（如果启用）
    if settings.rate_limit.enabled:
        try:
            from pyrate_limiter import Limiter, Rate
            from app.core.rate_limit import PerKeyBucketFactory

            # 创建内存限流器（按 key 隔离，避免全局共享计数器）
            login_rate = Rate(settings.rate_limit.login_max_requests,
                             settings.rate_limit.login_window_seconds * 1000)
            login_limiter = Limiter(PerKeyBucketFactory([login_rate]))

            checkin_rate = Rate(settings.rate_limit.checkin_max_requests,
                               settings.rate_limit.checkin_window_seconds * 1000)
            checkin_limiter = Limiter(PerKeyBucketFactory([checkin_rate]))

            # 存储到 app state
            app.state.limiter = login_limiter
            app.state.checkin_limiter = checkin_limiter
            app.state.rate_limit_config = settings.rate_limit

            logger.info("限流功能已启用（按 key 隔离）")
            logger.info(f"  登录限流: {settings.rate_limit.login_max_requests}次/{settings.rate_limit.login_window_seconds}秒")
            logger.info(f"  签到限流: {settings.rate_limit.checkin_max_requests}次/{settings.rate_limit.checkin_window_seconds}秒")
        except Exception as e:
            logger.warning(f"限流初始化失败: {e}")
            logger.warning("继续运行，限流功能将不可用")
    
    logger.info(f"后端API: http://localhost:{settings.app.port}")
    logger.info(f"API文档: http://localhost:{settings.app.port}/docs")
    logger.info(f"前端页面: http://localhost:3000 (开发服务器)")
    logger.info("=" * 50)
    
    yield

    # 关闭时执行
    # 关闭审计日志线程池，释放线程资源
    from app.core.middleware import shutdown_audit_executor
    shutdown_audit_executor()
    logger.info("审计日志线程池已关闭")

    logger.info("服务已停止")


def create_app() -> FastAPI:
    """
    应用工厂函数
    
    Returns:
        FastAPI应用实例
    """
    # 创建FastAPI应用
    app = FastAPI(
        title=settings.app.name,
        description="FastAPI + SQLModel 架构",
        version=settings.app.version,
        debug=settings.app.debug,
        lifespan=lifespan
    )
    
    # 缓存控制中间件（必须在 CORS 之前）
    app.add_middleware(CacheControlMiddleware)

    # CORS配置 - SEC-005: 收紧CORS策略，使用明确白名单
    # 注意：allow_credentials=True 配合通配符存在安全风险，必须明确指定
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.security.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
        expose_headers=["X-Request-ID"],  # 允许前端读取的响应头
        max_age=600,  # 预检请求缓存10分钟
    )
    
    # 审计日志中间件（记录敏感操作）
    from app.core.middleware import AuditLogMiddleware
    app.add_middleware(AuditLogMiddleware)
    
    # 注册异常处理器（统一错误响应格式）
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # 独立健康检查端点（用于监控，无需认证）
    from datetime import datetime
    
    @app.get("/health", include_in_schema=False)
    async def health_check():
        return {"status": "healthy", "timestamp": datetime.now().isoformat(), "version": "2.0.0"}
    
    # 注册API路由（必须在静态文件之前）
    from app.api.routes import (
        login_router, students_router, users_router,
        checkin_router, system_router, schedules_router, leaderboard_router,
        course_sessions_router, schedule_adjustments_router, groups_router,
        questions_router, lost_found_router, term_router, subjects_router
    )

    # API v1 版本前缀
    API_V1_PREFIX = "/api/v1"

    app.include_router(login_router, prefix=API_V1_PREFIX)
    app.include_router(system_router, prefix=API_V1_PREFIX)
    # 注意：leaderboard_router 必须在 students_router 之前注册
    # 否则 /students/{student_id} 会匹配 /students/leaderboard
    app.include_router(leaderboard_router, prefix=API_V1_PREFIX)
    app.include_router(students_router, prefix=API_V1_PREFIX)
    app.include_router(users_router, prefix=API_V1_PREFIX)
    app.include_router(checkin_router, prefix=API_V1_PREFIX)
    app.include_router(schedules_router, prefix=API_V1_PREFIX)
    app.include_router(course_sessions_router, prefix=API_V1_PREFIX)
    app.include_router(schedule_adjustments_router, prefix=API_V1_PREFIX)
    app.include_router(groups_router, prefix=API_V1_PREFIX)
    app.include_router(questions_router, prefix=API_V1_PREFIX)
    app.include_router(lost_found_router, prefix=API_V1_PREFIX)
    app.include_router(term_router, prefix=API_V1_PREFIX)
    app.include_router(subjects_router, prefix=API_V1_PREFIX)

    # 挂载上传文件目录（必须在 catch-all 路由之前）
    uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
    os.makedirs(uploads_dir, exist_ok=True)

    # 静态文件服务（生产环境）
    if os.path.exists(STATIC_DIR):
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
        
        @app.get("/", include_in_schema=False)
        async def root():
            """首页"""
            index_file = os.path.join(STATIC_DIR, "index.html")
            if os.path.exists(index_file):
                return FileResponse(index_file)
            return {"message": "班级管理系统 API"}
        
        @app.get("/{path:path}", include_in_schema=False)
        async def catch_all(request: Request, path: str):
            """前端路由处理（仅开发环境使用，生产环境由 nginx 处理）"""
            # API 路径
            if path.startswith("api/"):
                return JSONResponse(
                    status_code=404,
                    content={'success': False, 'message': 'API接口不存在'}
                )
            
            # uploads 路径 - 由 StaticFiles Mount 处理
            # （Starlette APIRoute 优先级高于 Mount，所以这里需要特殊处理）
            if path.startswith("uploads/"):
                import mimetypes
                file_path = os.path.join(uploads_dir, path[len("uploads/"):])
                if os.path.isfile(file_path):
                    mime_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
                    return FileResponse(file_path, media_type=mime_type)
                return JSONResponse(
                    status_code=404,
                    content={'success': False, 'message': '文件不存在'}
                )
            
            file_path = os.path.join(STATIC_DIR, path)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                return FileResponse(file_path)
            
            index_file = os.path.join(STATIC_DIR, "index.html")
            if os.path.exists(index_file):
                return FileResponse(index_file)
            
            return {"message": "班级管理系统 API"}
    else:
        @app.get("/", include_in_schema=False)
        async def root():
            """首页"""
            return {"message": "班级管理系统 API", "docs": "/docs"}
    
    # 全局异常处理
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """全局异常处理 - 生产环境隐藏内部错误详情"""
        logger.error(f"全局异常: {exc}", exc_info=True)
        from app.core.exceptions import generic_exception_handler
        return await generic_exception_handler(request, exc)
    
    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    # 获取环境
    env = os.environ.get('FASTAPI_ENV', 'production')
    is_dev = env == 'development'
    
    # 启动服务
    uvicorn.run(
        "main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=is_dev,
        workers=1 if is_dev else None
    )
