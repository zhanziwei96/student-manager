"""
限流保护模块 - 防止暴力破解和API滥用
"""
from flask import request, jsonify
from functools import wraps
import time
from collections import defaultdict


class SimpleRateLimiter:
    """
    简单的内存限流器
    生产环境建议使用Redis后端
    """
    
    def __init__(self):
        # 存储请求记录: {ip: [(timestamp, count), ...]}
        self.requests = defaultdict(list)
        self.blocked = {}  # {ip: unblock_timestamp}
    
    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> tuple:
        """
        检查请求是否允许
        
        Args:
            key: 限流键（通常是IP）
            max_requests: 窗口期内最大请求数
            window_seconds: 时间窗口（秒）
            
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


def rate_limit(limit_name: str = 'default'):
    """
    限流装饰器
    
    Usage:
        @rate_limit('login')
        def login():
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # 获取客户端IP
            ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            if ip and ',' in ip:
                ip = ip.split(',')[0].strip()
            
            # 获取限流配置
            max_req, window = RATE_LIMITS.get(limit_name, RATE_LIMITS['default'])
            
            # 检查限流
            allowed, retry_after = _limiter.is_allowed(f"{ip}:{limit_name}", max_req, window)
            
            if not allowed:
                return jsonify({
                    'success': False,
                    'message': f'请求过于频繁，请{retry_after}秒后再试',
                    'retry_after': retry_after
                }), 429
            
            return f(*args, **kwargs)
        return wrapper
    return decorator


def init_rate_limiter(app):
    """初始化全局限流中间件"""
    
    @app.before_request
    def check_global_rate_limit():
        """全局请求限流检查"""
        # 排除静态文件
        if not request.path.startswith('/api/'):
            return None
        
        ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if ip and ',' in ip:
            ip = ip.split(',')[0].strip()
        
        # 全局限制: 100次/分钟
        allowed, retry_after = _limiter.is_allowed(f"{ip}:global", 100, 60)
        if not allowed:
            return jsonify({
                'success': False,
                'message': '请求过于频繁，请稍后再试'
            }), 429
        
        return None
