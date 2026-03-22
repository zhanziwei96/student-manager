"""
班级管理系统 - FastAPI + SQLModel 架构主入口
前后端完全分离，后端只提供API
"""
import os

# 根据环境变量加载对应配置
ENV = os.getenv('ENV', 'production').lower()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if ENV == 'testing':
    os.environ['ENV_FILE'] = os.path.join(BASE_DIR, '.env.testing')
elif ENV == 'development':
    os.environ['ENV_FILE'] = os.path.join(BASE_DIR, '.env.development')

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import get_settings
from app.core.db import init_db
from app.core.logging import logger
from app.core.exceptions import http_exception_handler

# 获取应用配置
settings = get_settings()

# 静态文件目录
STATIC_DIR = os.path.join(os.path.dirname(__file__), "../frontend/dist")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    # 启动时执行
    logger.info("=" * 50)
    logger.info("班级管理系统 FastAPI + SQLModel 架构")
    logger.info("=" * 50)
    logger.info(f"数据库路径: {settings.get_database_path()}")
    
    # 初始化数据库
    init_db()
    
    # 初始化限流（如果启用）
    if settings.rate_limit.enabled:
        try:
            from pyrate_limiter import Limiter, Rate, InMemoryBucket
            
            # 创建内存限流器
            rate = Rate(settings.rate_limit.login_max_requests, 
                       settings.rate_limit.login_window_seconds * 1000)  # 转换为毫秒
            bucket = InMemoryBucket([rate])
            limiter = Limiter(bucket)
            
            # 存储到 app state
            app.state.limiter = limiter
            app.state.rate_limit_config = settings.rate_limit
            
            logger.info("限流功能已启用（内存存储）")
            logger.info(f"  登录限流: {settings.rate_limit.login_max_requests}次/{settings.rate_limit.login_window_seconds}秒")
        except Exception as e:
            logger.warning(f"限流初始化失败: {e}")
            logger.warning("继续运行，限流功能将不可用")
    
    logger.info(f"后端API: http://localhost:{settings.app.port}")
    logger.info(f"API文档: http://localhost:{settings.app.port}/docs")
    logger.info(f"前端页面: http://localhost:3000 (开发服务器)")
    logger.info("=" * 50)
    
    yield
    
    # 关闭时执行
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
    
    # Session配置
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.security.secret_key,
        max_age=settings.security.session_max_age,
    )
    
    # CORS配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.security.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册HTTPException处理器（统一错误响应格式）
    app.add_exception_handler(HTTPException, http_exception_handler)
    
    # 独立健康检查端点（用于监控，无需认证）
    from datetime import datetime
    
    @app.get("/health", include_in_schema=False)
    async def health_check():
        return {"status": "healthy", "timestamp": datetime.now().isoformat(), "version": "2.0.0"}
    
    # 注册API路由（必须在静态文件之前）
    from app.api.routes import (
        login_router, students_router, users_router,
        checkin_router, system_router
    )
    
    app.include_router(login_router)
    app.include_router(system_router)
    app.include_router(students_router)
    app.include_router(users_router)
    app.include_router(checkin_router)
    
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
            """前端路由处理"""
            if path.startswith("api/"):
                return JSONResponse(
                    status_code=404,
                    content={'success': False, 'message': 'API接口不存在'}
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
        """全局异常处理"""
        logger.error(f"全局异常: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={'success': False, 'message': f'服务器错误: {str(exc)}'}
        )
    
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
