"""
限流保护模块 - FastAPI-Limiter + 内存存储版本
使用 fakeredis 实现内存中的 Redis 兼容存储
"""
from fastapi import Request
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import fakeredis.aioredis as fake_redis


# 限流规则配置（次数/时间窗口）
RATE_LIMITS = {
    'login': '5/minute',           # 登录接口: 5次/分钟
    'checkin': '10/minute',        # 签到接口: 10次/分钟
    'score_change': '10/minute',   # 分数修改: 10次/分钟
    'user_search': '10/minute',    # 用户查询: 10次/分钟
    'default': '60/minute',        # 默认: 60次/分钟
}

# 全局内存 Redis 实例
_memory_redis = None


async def init_rate_limiter():
    """
    初始化 FastAPI-Limiter（使用内存存储）
    
    使用 fakeredis 实现纯内存存储，无需安装 Redis
    """
    global _memory_redis
    
    # 创建内存 Redis 实例
    _memory_redis = fake_redis.FakeRedis()
    
    # 初始化 FastAPI-Limiter
    await FastAPILimiter.init(_memory_redis)
    
    print("✅ 内存限流器已启用（无需 Redis）")


def rate_limit(limit_type: str = 'default'):
    """
    限流装饰器
    
    Usage:
        @app.post("/api/login", dependencies=[Depends(rate_limit('login'))])
        async def login(...):
            ...
    
    Args:
        limit_type: 限流类型，对应 RATE_LIMITS 中的key
        
    Returns:
        RateLimiter依赖
    """
    limit_string = RATE_LIMITS.get(limit_type, RATE_LIMITS['default'])
    times, seconds = parse_limit_string(limit_string)
    return RateLimiter(times=times, seconds=seconds)


def parse_limit_string(limit_string: str) -> tuple:
    """
    解析限流字符串
    
    Args:
        limit_string: 如 "5/minute", "10/hour"
        
    Returns:
        (次数, 秒数)
    """
    parts = limit_string.split('/')
    times = int(parts[0])
    period = parts[1]
    
    # 转换为秒数
    period_seconds = {
        'second': 1,
        'minute': 60,
        'hour': 3600,
        'day': 86400,
    }
    
    seconds = period_seconds.get(period.rstrip('s'), 60)  # 默认分钟
    return times, seconds


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
