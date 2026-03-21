"""
缓存中间件
自动缓存 GET 请求的响应
"""
import json
import hashlib
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from infrastructure.cache.cache_client import get_cache_client
from infrastructure.config import CacheConfig
from infrastructure.logging import logger


class CacheMiddleware(BaseHTTPMiddleware):
    """
    自动缓存中间件
    
    自动缓存 GET 请求的响应，支持：
    - 可配置的 TTL
    - 排除特定路径
    - 排除特定状态码
    - 响应内容类型过滤
    """
    
    def __init__(
        self,
        app: ASGIApp,
        ttl: int = CacheConfig.CACHE_MIDDLEWARE_TTL,
        exclude_paths: Optional[list] = None,
        exclude_params: Optional[list] = None,
        cache_status_codes: Optional[list] = None,
        enabled: bool = True
    ):
        super().__init__(app)
        self.ttl = ttl
        self.enabled = enabled
        self.exclude_paths = exclude_paths or [
            # 健康检查端点（不需要缓存）
            '/health',
            '/ready',
            '/live',
            '/api/health',
            '/api/ready',
            '/api/live',
            # 敏感数据接口（需要认证，不应缓存）
            '/api/students',           # 学生列表（敏感）
            '/api/stats',              # 统计数据（敏感）
            '/api/me',                 # 当前用户信息（敏感）
            '/api/admin',              # 管理员接口（敏感）
            '/api/logs',               # 审计日志（敏感）
            '/api/backup',             # 备份管理（敏感）
            '/api/database',           # 数据库管理（敏感）
            '/api/cache',              # 缓存管理（敏感）
            '/api/checkin/records',    # 签到记录（敏感）
            '/api/checkin/stats',      # 签到统计（敏感）
            '/api/checkin/today',      # 今日签到（敏感）
            '/api/score/logs',         # 分数日志（敏感）
            '/api/class-session',      # 课堂会话（实时数据，不缓存）
            '/api/class-session/students',  # 课堂学生列表（实时数据）
        ]
        self.exclude_params = exclude_params or ['nocache', 'refresh']
        self.cache_status_codes = cache_status_codes or [200]
    
    def _should_cache(self, request: Request, response: Response) -> bool:
        """判断是否应该缓存此请求/响应"""
        if not self.enabled:
            return False
        
        # 只缓存 GET 请求
        if request.method != 'GET':
            return False
        
        # 排除特定路径
        path = request.url.path
        for exclude in self.exclude_paths:
            if path.startswith(exclude):
                return False
        
        # 检查排除参数
        for param in self.exclude_params:
            if param in request.query_params:
                return False
        
        # 检查状态码
        if response.status_code not in self.cache_status_codes:
            return False
        
        # 检查内容类型（只缓存 JSON）
        content_type = response.headers.get('content-type', '')
        if 'application/json' not in content_type:
            return False
        
        return True
    
    def _build_cache_key(self, request: Request) -> str:
        """构建缓存键"""
        # 包含路径和查询参数
        key_parts = [request.method, request.url.path]
        
        # 添加查询参数（排序确保一致性）
        if request.query_params:
            sorted_params = sorted(request.query_params.multi_items())
            # 排除排除参数
            filtered_params = [
                (k, v) for k, v in sorted_params 
                if k not in self.exclude_params
            ]
            if filtered_params:
                key_parts.append(str(filtered_params))
        
        # 添加用户角色（不同角色看到不同内容）
        # 从 session 获取用户角色（安全地检查 session 是否存在）
        try:
            is_admin = request.session.get('is_admin', False)
            key_parts.append(f"admin:{is_admin}")
        except (AssertionError, AttributeError):
            # SessionMiddleware 未安装或未启用
            pass
        
        key_str = ':'.join(key_parts)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        
        return f"app:api:{key_hash}"
    
    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        cache = get_cache_client()
        
        # 只在启用缓存且已连接 Redis 时尝试缓存
        if not self.enabled or not cache.is_connected or request.method != 'GET':
            return await call_next(request)
        
        # 检查排除路径
        path = request.url.path
        for exclude in self.exclude_paths:
            if path.startswith(exclude):
                return await call_next(request)
        
        # 检查排除参数
        for param in self.exclude_params:
            if param in request.query_params:
                return await call_next(request)
        
        # 构建缓存键
        cache_key = self._build_cache_key(request)
        
        # 尝试从缓存获取
        try:
            cached_body = await cache.get(cache_key)
            if cached_body:
                logger.debug(f"API cache hit: {cache_key}")
                return Response(
                    content=cached_body,
                    media_type="application/json",
                    headers={"X-Cache": "HIT"}
                )
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
        
        # 执行请求
        response = await call_next(request)
        
        # 尝试缓存响应
        if self._should_cache(request, response):
            try:
                # 读取响应体
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk
                
                # 缓存响应
                await cache.set(cache_key, body.decode('utf-8'), self.ttl)
                logger.debug(f"API cache set: {cache_key}, ttl={self.ttl}")
                
                # 返回新的响应
                return Response(
                    content=body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type
                )
            except Exception as e:
                logger.warning(f"Cache write error: {e}")
        
        return response
