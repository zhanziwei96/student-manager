"""
健康检查控制器
用于Docker/Kubernetes健康检查
"""
from fastapi import APIRouter, Depends
from datetime import datetime

from infrastructure.persistence.database import Database
from infrastructure.cache.cache_client import get_cache_client
from infrastructure.config import HttpStatus


router = APIRouter(tags=["health"])


def get_db():
    """获取数据库连接"""
    return Database()


@router.get("/health", response_model=dict)
async def health_check():
    """
    健康检查端点
    
    检查项：
    - 服务运行状态
    - 数据库连接状态
    - Redis连接状态（如果使用）
    
    Returns:
        健康状态信息
    """
    health_info = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "checks": {}
    }
    
    # 检查数据库连接
    try:
        db = Database()
        with db.connection() as conn:
            cursor = conn.execute("SELECT 1")
            cursor.fetchone()
        health_info["checks"]["database"] = {
            "status": "up",
            "message": "数据库连接正常"
        }
    except Exception as e:
        health_info["status"] = "unhealthy"
        health_info["checks"]["database"] = {
            "status": "down",
            "message": f"数据库连接失败: {str(e)}"
        }
    
    # 检查Redis连接
    try:
        cache = get_cache_client()
        if cache.is_connected:
            await cache.ping()
            health_info["checks"]["redis"] = {
                "status": "up",
                "message": "Redis连接正常"
            }
        else:
            health_info["checks"]["redis"] = {
                "status": "skipped",
                "message": "Redis未启用"
            }
    except Exception as e:
        health_info["checks"]["redis"] = {
            "status": "down",
            "message": f"Redis连接失败: {str(e)}"
        }
    
    # 如果有任何检查失败，返回503状态码
    if health_info["status"] == "unhealthy":
        from fastapi import HTTPException
        raise HTTPException(status_code=HttpStatus.SERVICE_UNAVAILABLE, detail=health_info)
    
    return health_info


@router.get("/ready", response_model=dict)
async def readiness_check():
    """
    就绪检查端点（Kubernetes使用）
    
    检查应用是否准备好接收流量
    """
    try:
        db = Database()
        with db.connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM students")
            cursor.fetchone()
        
        return {
            "status": "ready",
            "timestamp": datetime.now().isoformat(),
            "message": "应用已就绪"
        }
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=HttpStatus.SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "timestamp": datetime.now().isoformat(),
                "message": f"应用未就绪: {str(e)}"
            }
        )


@router.get("/live", response_model=dict)
async def liveness_check():
    """
    存活检查端点（Kubernetes使用）
    
    检查应用是否存活，不需要检查依赖服务
    """
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "message": "应用运行中"
    }
