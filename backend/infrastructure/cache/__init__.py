"""
缓存模块
提供分布式缓存支持，基于 Redis
"""
from infrastructure.cache.cache_client import (
    CacheClient, 
    get_cache_client, 
    set_cache_client,
    init_cache_client
)
from infrastructure.cache.cache_decorator import (
    cached, 
    cache_evict,
    cached_student,
    cached_student_list,
    cached_stats,
    cached_audit_stats,
    evict_student_cache,
    evict_checkin_cache
)
from infrastructure.cache.cache_key import CacheKeyBuilder
from infrastructure.cache.cache_middleware import CacheMiddleware

__all__ = [
    # 客户端
    'CacheClient',
    'get_cache_client',
    'set_cache_client',
    'init_cache_client',
    # 装饰器
    'cached',
    'cache_evict',
    'cached_student',
    'cached_student_list',
    'cached_stats',
    'cached_audit_stats',
    'evict_student_cache',
    'evict_checkin_cache',
    # 其他
    'CacheKeyBuilder',
    'CacheMiddleware',
]
