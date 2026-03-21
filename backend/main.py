"""
班级管理系统 - FastAPI + DDD架构主入口
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

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from infrastructure.persistence.database import Database
from infrastructure.security.rate_limiter import init_rate_limiter
from infrastructure.cache import init_cache_client
from infrastructure.cache.cache_warmup import warmup_cache
from infrastructure.config import get_settings, init_settings, AppConfig, AuthConfig, CacheConfig, HttpStatus
from infrastructure.logging import logger
from interface.api import student_controller, user_controller, checkin_controller, class_session_controller, audit_log_controller, health_controller, cache_controller, database_controller, backup_controller

# 获取应用配置（如果是测试/开发环境，加载对应配置）
if ENV == 'testing':
    settings = init_settings(os.path.join(BASE_DIR, '.env.testing'))
elif ENV == 'development':
    settings = init_settings(os.path.join(BASE_DIR, '.env.development'))
else:
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
    logger.info("班级管理系统 FastAPI + DDD架构")
    logger.info("=" * 50)
    
    # 打印数据库路径
    db_path = os.path.abspath(settings.database.path)
    logger.info(f"数据库路径: {db_path}")
    
    # 初始化限流器
    await init_rate_limiter(settings.redis.url)
    
    # 初始化缓存客户端（Redis）
    await init_cache_client(settings.redis.url)
    
    # 缓存预热
    await warmup_cache()
    
    logger.info(f"后端API: http://localhost:8000")
    logger.info(f"API文档: http://localhost:8000/docs")
    logger.info(f"前端页面: http://localhost:3000 (开发服务器)")
    logger.info("架构层次:")
    logger.info("  - Interface (API层)")
    logger.info("  - Application (应用层)")
    logger.info("  - Domain (领域层)")
    logger.info("  - Infrastructure (基础设施层)")
    logger.info("按 Ctrl+C 停止服务")
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
        title=settings.name,
        description="FastAPI + DDD架构",
        version=settings.version,
        debug=settings.debug,
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
        allow_credentials=settings.security.cors_allow_credentials,
        allow_methods=settings.security.cors_allow_methods,
        allow_headers=settings.security.cors_allow_headers,
    )
    
    # 缓存中间件
    from infrastructure.cache import CacheMiddleware
    app.add_middleware(
        CacheMiddleware,
        ttl=settings.cache.ttl,
        enabled=settings.cache.enabled
    )
    
    # 初始化数据库
    db = Database()
    db.init_tables()
    db.run_migrations()  # 运行数据库迁移
    db.init_indexes()  # 创建索引
    
    # 注册API路由
    # 健康检查端点（无需认证，放在第一位）
    app.include_router(health_controller.router)
    
    app.include_router(student_controller.router)
    app.include_router(user_controller.router)
    app.include_router(checkin_controller.router)
    app.include_router(class_session_controller.router)
    app.include_router(audit_log_controller.router)
    app.include_router(cache_controller.router)
    app.include_router(database_controller.router)
    app.include_router(backup_controller.router)
    
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
            """
            前端路由处理
            所有非API请求都返回index.html，由Vue Router处理
            """
            if path.startswith("api/"):
                return JSONResponse(
                    status_code=404,
                    content={'success': False, 'message': 'API接口不存在'}
                )
            
            # 静态文件直接返回
            file_path = os.path.join(STATIC_DIR, path)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                return FileResponse(file_path)
            
            # 其他请求返回index.html
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
        host=settings.host,
        port=settings.port,
        reload=is_dev,
        workers=1 if is_dev else None
    )
