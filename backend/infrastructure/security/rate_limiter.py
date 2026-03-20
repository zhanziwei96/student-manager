"""
限流保护模块 - FastAPI-Limiter + Redis版本
支持分布式部署和持久化限流计数
"""
import os
from fastapi import Request
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis


# 限流规则配置（次数/时间窗口）
# 格式: (次数, 秒数)
RATE_LIMITS = {
    'login': (5, 60),        # 登录: 5次/分钟
    'checkin': (10, 60),     # 签到: 10次/分钟
    'score_change': (10, 60), # 分数修改: 10次/分钟
    'user_search': (10, 60), # 用户查询: 10次/分钟
    'default': (60, 60),     # 默认: 60次/分钟
}


async def init_rate_limiter(redis_url: str = None):
    """
    初始化FastAPI-Limiter
    
    Args:
        redis_url: Redis连接URL，默认从环境变量获取或本地Redis
    """
    if redis_url is None:
        redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    
    try:
        # 创建Redis连接
        redis_connection = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        
        # 测试连接
        await redis_connection.ping()
        
        # 初始化FastAPI-Limiter
        await FastAPILimiter.init(redis_connection)
        
        print(f"✅ Redis限流器已启用: {redis_url}")
        
    except Exception as e:
        print(f"❌ Redis连接失败: {e}")
        print("⚠️ 请确保Redis已安装并运行:")
        print("   Ubuntu/Debian: sudo apt-get install redis-server")
        print("   macOS: brew install redis && brew services start redis")
        print("   Docker: docker run -d -p 6379:6379 redis:latest")
        raise


def rate_limit(limit_name: str = 'default'):
    """
    限流装饰器 - FastAPI依赖注入
    
    Usage:
        @app.post("/api/login", dependencies=[Depends(rate_limit('login'))])
        async def login(...):
            ...
    
    Args:
        limit_name: 限流类型，对应 RATE_LIMITS 中的key
        
    Returns:
        RateLimiter依赖
    """
    times, seconds = RATE_LIMITS.get(limit_name, RATE_LIMITS['default'])
    return RateLimiter(times=times, seconds=seconds)


# 便捷函数
def login_limit():
    """登录接口限流: 5次/分钟"""
    return rate_limit('login')


def checkin_limit():
    """签到接口限流: 10次/分钟"""
    return rate_limit('checkin')


def score_limit():
    """分数修改限流: 10次/分钟"""
    return rate_limit('score_change')


def default_limit():
    """默认限流: 60次/分钟"""
    return rate_limit('default')
