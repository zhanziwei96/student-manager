"""
缓存装饰器
提供 @cached 和 @cache_evict 装饰器
"""
import functools
import inspect
from typing import Any, Callable, Optional, Union
from functools import wraps

from infrastructure.config import CacheConfig

from infrastructure.cache.cache_client import get_cache_client
from infrastructure.cache.cache_key import CacheKeyBuilder
from infrastructure.logging import logger


def cached(
    key: Optional[str] = None,
    key_builder: Optional[Callable] = None,
    ttl: int = CacheConfig.CACHE_DECORATOR_DEFAULT_TTL,
    condition: Optional[Callable] = None,
    unless: Optional[Callable] = None
):
    """
    缓存装饰器
    
    自动缓存函数返回结果，支持自定义缓存键和条件。
    
    Args:
        key: 固定缓存键（如果提供，不使用 key_builder）
        key_builder: 缓存键构建函数，接收函数参数返回键名
        ttl: 缓存生存时间（秒），默认 5 分钟
        condition: 缓存条件函数，返回 True 才缓存
        unless: 排除条件函数，返回 True 不缓存
        
    Usage:
        @cached(ttl=60)
        async def get_student(student_id: str):
            return await fetch_from_db(student_id)
        
        @cached(key_builder=lambda class_name: CacheKeyBuilder.student_list(class_name))
        async def get_students_by_class(class_name: str):
            return await fetch_students(class_name)
    """
    def decorator(func):
        is_async = inspect.iscoroutinefunction(func)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 检查排除条件
            if unless and unless(*args, **kwargs):
                return await func(*args, **kwargs)
            
            # 构建缓存键
            cache_key = _build_cache_key(key, key_builder, func, args, kwargs)
            
            # 尝试从缓存获取
            cache = get_cache_client()
            if cache.is_connected:
                try:
                    cached_value = await cache.get_json(cache_key)
                    if cached_value is not None:
                        logger.debug(f"Cache hit: {cache_key}")
                        return cached_value
                except Exception as e:
                    logger.warning(f"Cache read error: {e}")
            
            # 执行原函数
            result = await func(*args, **kwargs)
            
            # 检查缓存条件
            if condition and not condition(result):
                return result
            
            # 写入缓存
            if cache.is_connected:
                try:
                    await cache.set_json(cache_key, result, ttl)
                    logger.debug(f"Cache set: {cache_key}, ttl={ttl}")
                except Exception as e:
                    logger.warning(f"Cache write error: {e}")
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 检查排除条件
            if unless and unless(*args, **kwargs):
                return func(*args, **kwargs)
            
            # 构建缓存键
            cache_key = _build_cache_key(key, key_builder, func, args, kwargs)
            
            # 同步函数使用同步 Redis 客户端
            # 这里简化处理，实际应用中可能需要同步 Redis 客户端
            result = func(*args, **kwargs)
            
            return result
        
        # 添加缓存操作辅助方法
        wrapper = async_wrapper if is_async else sync_wrapper
        
        async def invalidate(*args, **kwargs):
            """使特定参数对应的缓存失效"""
            cache_key = _build_cache_key(key, key_builder, func, args, kwargs)
            cache = get_cache_client()
            if cache.is_connected:
                await cache.delete(cache_key)
                logger.debug(f"Cache invalidated: {cache_key}")
        
        async def invalidate_all():
            """使所有相关缓存失效（根据模式）"""
            if key:
                cache = get_cache_client()
                if cache.is_connected:
                    await cache.delete(key)
            # 否则无法确定哪些缓存需要失效
        
        wrapper.invalidate = invalidate
        wrapper.invalidate_all = invalidate_all
        wrapper.cache_key = key
        
        return wrapper
    
    return decorator


def cache_evict(
    key: Optional[str] = None,
    key_builder: Optional[Callable] = None,
    pattern: Optional[str] = None,
    before: bool = False
):
    """
    缓存失效装饰器
    
    在函数执行前或执行后清除缓存。
    
    Args:
        key: 要清除的固定缓存键
        key_builder: 缓存键构建函数
        pattern: 模式匹配清除（如 "app:student:*"）
        before: 是否在函数执行前清除（默认之后）
        
    Usage:
        @cache_evict(key="app:student:list:all")
        async def create_student(data):
            return await db.create(data)
        
        @cache_evict(pattern="app:student:*")
        async def update_student(student_id, data):
            return await db.update(student_id, data)
    """
    def decorator(func):
        is_async = inspect.iscoroutinefunction(func)
        
        async def do_evict(*args, **kwargs):
            """执行缓存清除"""
            cache = get_cache_client()
            if not cache.is_connected:
                return
            
            try:
                if key:
                    await cache.delete(key)
                    logger.debug(f"Cache evicted: {key}")
                
                if key_builder:
                    cache_key = key_builder(*args, **kwargs)
                    await cache.delete(cache_key)
                    logger.debug(f"Cache evicted: {cache_key}")
                
                if pattern:
                    count = await cache.delete_pattern(pattern)
                    logger.debug(f"Cache pattern evicted: {pattern}, count={count}")
                    
            except Exception as e:
                logger.warning(f"Cache eviction error: {e}")
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if before:
                await do_evict(*args, **kwargs)
            
            result = await func(*args, **kwargs)
            
            if not before:
                await do_evict(*args, **kwargs)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 同步函数简化处理
            return func(*args, **kwargs)
        
        return async_wrapper if is_async else sync_wrapper
    
    return decorator


def _build_cache_key(
    key: Optional[str],
    key_builder: Optional[Callable],
    func: Callable,
    args: tuple,
    kwargs: dict
) -> str:
    """构建缓存键"""
    if key:
        return key
    
    if key_builder:
        try:
            # 尝试使用 key_builder
            bound_args = inspect.signature(func).bind(*args, **kwargs)
            bound_args.apply_defaults()
            return key_builder(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Key builder error: {e}")
    
    # 默认使用函数名和参数哈希
    func_name = f"{func.__module__}.{func.__name__}"
    args_str = str(args) + str(sorted(kwargs.items()))
    import hashlib
    args_hash = hashlib.md5(args_str.encode()).hexdigest()[:8]
    return f"app:func:{func_name}:{args_hash}"


# ========== 特定场景的装饰器 ==========

def cached_student(ttl: int = CacheConfig.STUDENT_DETAIL_TTL_SECONDS):
    """学生数据缓存"""
    return cached(key_builder=lambda student_id: CacheKeyBuilder.student_detail(student_id), ttl=ttl)

def cached_student_list(ttl: int = CacheConfig.STUDENT_LIST_TTL_SECONDS):
    """学生列表缓存"""
    return cached(
        key_builder=lambda class_name=None: CacheKeyBuilder.student_list(class_name),
        ttl=ttl
    )

def cached_stats(ttl: int = CacheConfig.STATS_TTL_SECONDS):
    """统计数据缓存"""
    return cached(ttl=ttl)

def cached_audit_stats(ttl: int = CacheConfig.AUDIT_STATS_TTL_SECONDS):
    """审计统计缓存"""
    return cached(key_builder=lambda days=7: CacheKeyBuilder.audit_stats(days), ttl=ttl)

def evict_student_cache():
    """清除学生相关缓存"""
    return cache_evict(pattern=CacheKeyBuilder.pattern_student_all())

def evict_checkin_cache():
    """清除签到相关缓存"""
    return cache_evict(pattern=CacheKeyBuilder.pattern_checkin_all())
