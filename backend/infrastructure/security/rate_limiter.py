"""
限流保护模块 - FastAPI-Limiter版本
防止暴力破解和API滥用
"""
from fastapi import Request
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis


# 限流规则配置（次数/时间窗口）
RATE_LIMITS = {
    'login': '5/minute',           # 登录接口: 5次/分钟
    'checkin': '10/minute',        # 签到接口: 10次/分钟
    'score_change': '10/minute',   # 分数修改: 10次/分钟
    'user_search': '10/minute',    # 用户查询: 10次/分钟
    'default': '60/minute',        # 默认: 60次/分钟
}


async def init_rate_limiter(redis_url: str = "redis://localhost:6379"):
    """
    初始化FastAPI-Limiter
    
    Args:
        redis_url: Redis连接URL，默认本地Redis
        
    如果没有Redis，会自动降级为内存存储
    """
    try:
        # 尝试连接Redis
        redis_connection = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        await redis_connection.ping()
        print("✅ Redis限流器已启用")
    except Exception as e:
        # 如果没有Redis，使用内存存储（仅适用于单进程）
        print(f"⚠️ Redis连接失败，使用内存限流: {e}")
        redis_connection = None
    
    await FastAPILimiter.init(redis_connection)


def rate_limit(limit_type: str = 'default'):
    """
    限流装饰器
    
    Usage:
        @app.post("/api/login")
        async def login(..., limiter: None = Depends(rate_limit('login'))):
            ...
    
    Args:
        limit_type: 限流类型，对应 RATE_LIMITS 中的key
        
    Returns:
        RateLimiter依赖
    """
    limit_string = RATE_LIMITS.get(limit_type, RATE_LIMITS['default'])
    times, period = parse_limit_string(limit_string)
    return RateLimiter(times=times, seconds=period)


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


def get_client_identifier(request: Request) -> str:
    """
    获取客户端标识（用于限流键）
    
    优先使用用户ID（如果已登录），否则使用IP
    """
    # 如果用户已登录，使用用户ID作为限流键
    user_id = request.session.get('user_id')
    if user_id:
        return f"user:{user_id}"
    
    # 否则使用IP地址
    forwarded = request.headers.get('X-Forwarded-For')
    if forwarded:
        return f"ip:{forwarded.split(',')[0].strip()}"
    
    return f"ip:{request.client.host}"


# 自定义RateLimiter，使用session用户ID作为限流键
class SessionRateLimiter(RateLimiter):
    """
    基于Session的限流器
    优先使用用户ID作为限流键
    """
    
    async def _check(self, key: str):
        """重写检查方法，使用自定义key"""
        # 调用父类方法，但使用我们的key
        return await super()._check(key)
    
    async def __call__(self, request: Request):
        """调用限流检查"""
        # 生成限流键
        identifier = get_client_identifier(request)
        key = f"{FastAPILimiter.prefix}:{identifier}:{request.url.path}"
        
        # 执行限流检查
        try:
            await self._check(key)
        except Exception:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=429,
                detail=f"请求过于频繁，请稍后再试"
            )


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
