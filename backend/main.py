"""
班级管理系统 - FastAPI + DDD架构主入口
前后端完全分离，后端只提供API
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from infrastructure.persistence.database import Database
from infrastructure.security.rate_limiter import init_rate_limiter, RateLimitMiddleware
from interface.api import student_controller, user_controller, checkin_controller, class_session_controller


# 静态文件目录
STATIC_DIR = os.path.join(os.path.dirname(__file__), "../frontend/dist")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    # 启动时执行
    print("=" * 50)
    print("班级管理系统 FastAPI + DDD架构")
    print("=" * 50)
    
    # 初始化限流器（使用内存存储）
    await init_rate_limiter()
    
    print(f"\n后端API: http://localhost:8000")
    print(f"API文档: http://localhost:8000/docs")
    print(f"前端页面: http://localhost:3000 (开发服务器)")
    print("\n架构层次:")
    print("  - Interface (API层)")
    print("  - Application (应用层)")
    print("  - Domain (领域层)")
    print("  - Infrastructure (基础设施层)")
    print("\n按 Ctrl+C 停止服务")
    print("=" * 50)
    
    yield
    
    # 关闭时执行
    print("\n服务已停止")


def create_app() -> FastAPI:
    """
    应用工厂函数
    
    Returns:
        FastAPI应用实例
    """
    # 创建FastAPI应用
    app = FastAPI(
        title="班级管理系统",
        description="FastAPI + DDD架构",
        version="2.0.0",
        lifespan=lifespan
    )
    
    # Session配置
    secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.add_middleware(
        SessionMiddleware,
        secret_key=secret_key,
        max_age=3600 * 24,  # 24小时
    )
    
    # CORS配置（开发环境）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 限流中间件
    app.add_middleware(RateLimitMiddleware)
    
    # 初始化数据库
    db = Database()
    db.init_tables()
    
    # 注册API路由
    app.include_router(student_controller.router)
    app.include_router(user_controller.router)
    app.include_router(checkin_controller.router)
    app.include_router(class_session_controller.router)
    
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
        host="0.0.0.0",
        port=8000,
        reload=is_dev,
        workers=1 if is_dev else None
    )
