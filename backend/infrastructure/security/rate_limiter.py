"""
限流保护模块 - 纯内存版本
不依赖 Redis，使用简单的内存字典实现
"""
import time
from typing import Optional, Tuple
from collections import defaultdict
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware


class SimpleRateLimiter:
    """
    简单的内存限流器
    """
    
    def __init__(self):
        # 存储请求记录: {key: [(timestamp, count), ...]}
        self.requests = defaultdict(list)
        self.blocked = {}  # {key: unblock_timestamp}
    
    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int]:
        """
        检查请求是否允许
        
        Returns:
            (allowed: bool, retry_after: int)
        """
        now = time.time()
        
        # 检查是否被封锁
        if key in self.blocked:
            if now < self.blocked[key]:
                return False, int(self.blocked[key] - now)
            else:
                del self.blocked[key]
        
        # 清理过期记录
        cutoff = now - window_seconds
        self.requests[key] = [
            (ts, cnt) for ts, cnt in self.requests[key] 
            if ts > cutoff
        ]
        
        # 计算当前窗口内的请求数
        count = sum(cnt for ts, cnt in self.requests[key])
        
        if count >= max_requests:
            # 封锁一段时间（窗口期的2倍）
            block_until = now + window_seconds * 2
            self.blocked[key] = block_until
            return False, int(window_seconds * 2)
        
        # 记录本次请求
        self.requests[key].append((now, 1))
        return True, 0


# 全局限流器实例
_limiter = SimpleRateLimiter()

# 限流规则: {endpoint: (max_requests, window_seconds)}
RATE_LIMITS = {
    'login': (5, 60),        # 登录: 5次/分钟
    'checkin': (10, 60),     # 签到: 10次/分钟
    'score_change': (10, 60), # 分数修改: 10次/分钟
    'default': (60, 60),     # 默认: 60次/分钟
}


def get_client_ip(request: Request) -> str:
    """获取客户端IP"""
    forwarded = request.headers.get('X-Forwarded-For')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.client.host


class RateLimitMiddleware(BaseHTTPMiddleware):
    """全局限流中间件"""
    
    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith('/api/'):
            return await call_next(request)
        
        ip = get_client_ip(request)
        allowed, retry_after = _limiter.is_allowed(f"{ip}:global", 100, 60)
        
        if not allowed:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={'success': False, 'message': '请求过于频繁，请稍后再试'}
            )
        
        return await call_next(request)


def rate_limit(limit_name: str = 'default'):
    """
    限流装饰器 - 用于FastAPI依赖注入
    
    Usage:
        @app.post("/api/login", dependencies=[Depends(rate_limit('login'))])
    """
    def check_rate_limit(request: Request):
        ip = get_client_ip(request)
        max_req, window = RATE_LIMITS.get(limit_name, RATE_LIMITS['default'])
        
        allowed, retry_after = _limiter.is_allowed(f"{ip}:{limit_name}", max_req, window)
        
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail=f'请求过于频繁，请{retry_after}秒后再试'
            )
    return check_rate_limit


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


async def init_rate_limiter():
    """初始化限流器（无需操作，纯内存）"""
    print("✅ 内存限流器已启用")
