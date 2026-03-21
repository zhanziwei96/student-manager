"""
缓存管理API控制器
提供缓存监控和管理功能（管理员）
"""
from typing import Optional, List
from fastapi import APIRouter, Request, HTTPException, Query
from pydantic import BaseModel

from infrastructure.cache import get_cache_client, CacheKeyBuilder
from infrastructure.security.session import require_admin
from infrastructure.logging import logger
from infrastructure.config import HttpStatus, PaginationConfig

router = APIRouter(prefix="/api/admin/cache", tags=["cache-admin"])


class CacheStats(BaseModel):
    """缓存统计"""
    connected: bool
    key_count: int
    memory_used: Optional[str] = None
    hit_rate: Optional[float] = None


class CacheEntry(BaseModel):
    """缓存条目"""
    key: str
    ttl: int
    type: Optional[str] = None


class ClearCacheRequest(BaseModel):
    """清除缓存请求"""
    pattern: Optional[str] = "app:*"
    confirm: bool = False


@router.get("/stats", response_model=dict)
async def get_cache_stats(request: Request):
    """获取缓存统计信息"""
    require_admin(request)
    
    cache = get_cache_client()
    
    if not cache.is_connected:
        return {
            'success': True,
            'data': {
                'connected': False,
                'message': 'Redis 未连接'
            }
        }
    
    try:
        # 获取 Redis 信息
        info = await cache.info()
        
        # 统计 app: 开头的键数量
        keys = await cache.keys("app:*")
        
        # 提取关键指标
        memory_used = info.get('used_memory_human', 'N/A')
        keyspace_hits = int(info.get('keyspace_hits', 0))
        keyspace_misses = int(info.get('keyspace_misses', 0))
        
        total_ops = keyspace_hits + keyspace_misses
        hit_rate = keyspace_hits / total_ops if total_ops > 0 else None
        
        return {
            'success': True,
            'data': {
                'connected': True,
                'key_count': len(keys),
                'app_keys': len(keys),
                'memory_used': memory_used,
                'hit_rate': round(hit_rate, 4) if hit_rate is not None else None,
                'total_commands_processed': info.get('total_commands_processed', 'N/A'),
                'connected_clients': info.get('connected_clients', 'N/A'),
                'uptime_in_seconds': info.get('uptime_in_seconds', 'N/A')
            }
        }
        
    except Exception as e:
        logger.error(f"获取缓存统计失败: {e}")
        raise HTTPException(status_code=HttpStatus.INTERNAL_ERROR, detail=str(e))


@router.get("/keys", response_model=dict)
async def list_cache_keys(
    request: Request,
    pattern: str = Query("app:*", description="匹配模式"),
    limit: int = Query(PaginationConfig.DEFAULT_PAGE_SIZE, ge=1, le=PaginationConfig.MAX_STUDENT_LIST, description="最大返回数量")
):
    """列出缓存键"""
    require_admin(request)
    
    cache = get_cache_client()
    
    if not cache.is_connected:
        raise HTTPException(status_code=HttpStatus.SERVICE_UNAVAILABLE, detail="Redis 未连接")
    
    try:
        keys = await cache.keys(pattern)
        keys = keys[:limit]  # 限制数量
        
        # 获取每个键的 TTL
        entries = []
        for key in keys:
            ttl = await cache.ttl(key)
            entries.append({
                'key': key,
                'ttl': ttl if ttl > 0 else -1  # -1 表示永不过期，-2 表示不存在
            })
        
        return {
            'success': True,
            'data': {
                'pattern': pattern,
                'total': len(keys),
                'keys': entries
            }
        }
        
    except Exception as e:
        logger.error(f"列出缓存键失败: {e}")
        raise HTTPException(status_code=HttpStatus.INTERNAL_ERROR, detail=str(e))


@router.get("/value/{key:path}", response_model=dict)
async def get_cache_value(
    request: Request,
    key: str
):
    """获取特定缓存值（调试用）"""
    require_admin(request)
    
    cache = get_cache_client()
    
    if not cache.is_connected:
        raise HTTPException(status_code=HttpStatus.SERVICE_UNAVAILABLE, detail="Redis 未连接")
    
    try:
        value = await cache.get(key)
        ttl = await cache.ttl(key)
        
        if value is None:
            raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="键不存在")
        
        # 尝试解析为 JSON
        import json
        try:
            parsed_value = json.loads(value)
            value_type = 'json'
        except json.JSONDecodeError:
            parsed_value = value
            value_type = 'string'
        
        return {
            'success': True,
            'data': {
                'key': key,
                'value': parsed_value,
                'type': value_type,
                'ttl': ttl if ttl > 0 else -1,
                'size_bytes': len(value.encode('utf-8')) if isinstance(value, str) else len(value)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取缓存值失败: {e}")
        raise HTTPException(status_code=HttpStatus.INTERNAL_ERROR, detail=str(e))


@router.delete("/clear", response_model=dict)
async def clear_cache(
    request: Request,
    pattern: str = Query("app:*", description="匹配模式"),
    confirm: bool = Query(False, description="确认清除")
):
    """清除缓存"""
    require_admin(request)
    
    if not confirm:
        raise HTTPException(
            status_code=HttpStatus.BAD_REQUEST, 
            detail="请设置 confirm=true 确认清除操作"
        )
    
    cache = get_cache_client()
    
    if not cache.is_connected:
        raise HTTPException(status_code=HttpStatus.SERVICE_UNAVAILABLE, detail="Redis 未连接")
    
    try:
        # 先统计要删除的数量
        keys = await cache.keys(pattern)
        count = len(keys)
        
        # 执行删除
        deleted = await cache.delete_pattern(pattern)
        
        logger.info(f"Cache cleared by admin: pattern={pattern}, count={deleted}")
        
        return {
            'success': True,
            'message': f'已清除 {deleted} 个缓存条目',
            'data': {
                'pattern': pattern,
                'matched': count,
                'deleted': deleted
            }
        }
        
    except Exception as e:
        logger.error(f"清除缓存失败: {e}")
        raise HTTPException(status_code=HttpStatus.INTERNAL_ERROR, detail=str(e))


@router.post("/warmup", response_model=dict)
async def warmup_cache(request: Request):
    """手动触发缓存预热"""
    require_admin(request)
    
    cache = get_cache_client()
    
    if not cache.is_connected:
        raise HTTPException(status_code=HttpStatus.SERVICE_UNAVAILABLE, detail="Redis 未连接")
    
    try:
        from infrastructure.cache.cache_warmup import CacheWarmupService
        
        service = CacheWarmupService(cache)
        await service.warmup_all()
        
        return {
            'success': True,
            'message': '缓存预热完成'
        }
        
    except Exception as e:
        logger.error(f"缓存预热失败: {e}")
        raise HTTPException(status_code=HttpStatus.INTERNAL_ERROR, detail=str(e))


@router.delete("/key/{key:path}", response_model=dict)
async def delete_cache_key(
    request: Request,
    key: str
):
    """删除特定缓存键"""
    require_admin(request)
    
    cache = get_cache_client()
    
    if not cache.is_connected:
        raise HTTPException(status_code=HttpStatus.SERVICE_UNAVAILABLE, detail="Redis 未连接")
    
    try:
        existed = await cache.exists(key)
        await cache.delete(key)
        
        logger.info(f"Cache key deleted by admin: {key}")
        
        return {
            'success': True,
            'message': '缓存键已删除' if existed else '缓存键不存在',
            'data': {
                'key': key,
                'existed': existed
            }
        }
        
    except Exception as e:
        logger.error(f"删除缓存键失败: {e}")
        raise HTTPException(status_code=HttpStatus.INTERNAL_ERROR, detail=str(e))
