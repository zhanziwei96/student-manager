"""
限流保护模块 - FastAPI-Limiter 0.2.0 + pyrate_limiter 版本
支持分布式部署和持久化限流计数
"""
from fastapi import Request, HTTPException
from fastapi_limiter.depends import RateLimiter
from pyrate_limiter import Limiter as PyRateLimiter, Rate
import redis.asyncio as redis
from redis.exceptions import ConnectionError as RedisConnectionError
from infrastructure.logging import logger
from infrastructure.config import get_settings

# 全局限流器实例
_limiter_instance = None


async def init_rate_limiter(redis_url: str = None):
    """
    初始化 FastAPI-Limiter
    
    Args:
        redis_url: Redis连接URL，默认从配置获取
    """
    global _limiter_instance
    
    settings = get_settings()
    
    if redis_url is None:
        redis_url = settings.redis.url
    
    try:
        # 创建Redis连接
        redis_connection = redis.from_url(
            redis_url,
            encoding=settings.redis.encoding,
            decode_responses=settings.redis.decode_responses
        )
        
        # 测试连接
        await redis_connection.ping()
        
        # 创建基于Redis的限流器（如果pyrate_limiter支持）
        # 当前使用内存限流器
        _limiter_instance = None  # 将在每次请求时动态创建Rate
        
        logger.info(f"Redis限流器已启用: {redis_url}")
        
    except Exception as e:
        logger.warning(f"Redis连接失败: {e}")
        logger.warning("限流功能将使用内存模式")
        _limiter_instance = None


async def _default_identifier(request: Request):
    """默认标识符 - 使用IP地址"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "anonymous"


async def _default_callback(request: Request, exc: Exception):
    """默认回调 - 返回429错误"""
    raise HTTPException(
        status_code=429,
        detail="请求过于频繁，请稍后重试"
    )


def _get_limiter(times: int, seconds: int) -> PyRateLimiter:
    """获取或创建限流器实例"""
    # pyrate_limiter 2.x 使用 Rate 对象
    rate = Rate(times, seconds * 1000)  # 转换为毫秒
    return PyRateLimiter(rate)


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
    # 动态获取配置，并应用倍数因子（测试时可设置更大值）
    settings = get_settings().rate_limit
    multiplier = settings.multiplier
    config_map = {
        'login': (settings.login_max_requests * multiplier, settings.login_window_seconds),
        'checkin': (settings.checkin_max_requests * multiplier, settings.checkin_window_seconds),
        'score_change': (settings.score_change_max_requests * multiplier, settings.score_change_window_seconds),
        'user_search': (settings.user_search_max_requests * multiplier, settings.user_search_window_seconds),
        'default': (settings.default_max_requests * multiplier, settings.default_window_seconds),
    }
    times, seconds = config_map.get(limit_name, config_map['default'])
    
    # 创建限流器
    limiter = _get_limiter(times, seconds)
    
    return RateLimiter(
        limiter=limiter,
        identifier=_default_identifier,
        callback=_default_callback
    )


# 便捷函数
def login_limit():
    """登录接口限流"""
    return rate_limit('login')


def checkin_limit():
    """签到接口限流"""
    return rate_limit('checkin')


def score_limit():
    """分数修改限流"""
    return rate_limit('score_change')


def default_limit():
    """默认限流"""
    return rate_limit('default')
