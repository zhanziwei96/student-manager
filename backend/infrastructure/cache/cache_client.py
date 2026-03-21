"""
Redis 缓存客户端
提供统一的缓存操作接口
"""
import json
import pickle
import hashlib
from typing import Any, Optional, Union, List
from datetime import timedelta

import redis.asyncio as redis
from redis.exceptions import RedisError

from infrastructure.logging import logger


class CacheClient:
    """
    缓存客户端
    
    基于 Redis 的分布式缓存实现，支持：
    - 字符串缓存
    - JSON 对象缓存
    - 二进制对象缓存（pickle）
    - 哈希表操作
    - 列表操作
    - 缓存失效策略
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self._redis = redis_client
        self._enabled = redis_client is not None
    
    @property
    def is_connected(self) -> bool:
        """检查是否已连接到 Redis"""
        return self._redis is not None
    
    async def ping(self) -> bool:
        """测试连接"""
        if not self._redis:
            return False
        try:
            return await self._redis.ping()
        except RedisError:
            return False
    
    # ========== 基础操作 ==========
    
    async def get(self, key: str) -> Optional[str]:
        """获取字符串值"""
        if not self._redis:
            return None
        try:
            value = await self._redis.get(key)
            return value.decode('utf-8') if value else None
        except RedisError as e:
            logger.warning(f"Cache get error: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: str,
        ttl: Optional[int] = None
    ) -> bool:
        """设置字符串值"""
        if not self._redis:
            return False
        try:
            await self._redis.set(key, value, ex=ttl)
            return True
        except RedisError as e:
            logger.warning(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self._redis:
            return False
        try:
            await self._redis.delete(key)
            return True
        except RedisError as e:
            logger.warning(f"Cache delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self._redis:
            return False
        try:
            return await self._redis.exists(key) > 0
        except RedisError as e:
            logger.warning(f"Cache exists error: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """获取剩余生存时间（秒）"""
        if not self._redis:
            return -2
        try:
            return await self._redis.ttl(key)
        except RedisError as e:
            logger.warning(f"Cache ttl error: {e}")
            return -2
    
    async def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间"""
        if not self._redis:
            return False
        try:
            return await self._redis.expire(key, seconds)
        except RedisError as e:
            logger.warning(f"Cache expire error: {e}")
            return False
    
    # ========== JSON 对象操作 ==========
    
    async def get_json(self, key: str) -> Optional[Any]:
        """获取 JSON 对象"""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                logger.warning(f"Cache JSON decode error: {e}")
        return None
    
    async def set_json(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """设置 JSON 对象"""
        try:
            json_str = json.dumps(value, ensure_ascii=False, default=str)
            return await self.set(key, json_str, ttl)
        except (TypeError, ValueError) as e:
            logger.warning(f"Cache JSON encode error: {e}")
            return False
    
    # ========== 二进制对象操作（pickle） ==========
    
    async def get_object(self, key: str) -> Optional[Any]:
        """获取 Python 对象（使用 pickle）"""
        if not self._redis:
            return None
        try:
            data = await self._redis.get(key)
            if data:
                return pickle.loads(data)
            return None
        except (RedisError, pickle.PickleError) as e:
            logger.warning(f"Cache get object error: {e}")
            return None
    
    async def set_object(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """设置 Python 对象（使用 pickle）"""
        if not self._redis:
            return False
        try:
            data = pickle.dumps(value)
            await self._redis.set(key, data, ex=ttl)
            return True
        except (RedisError, pickle.PickleError) as e:
            logger.warning(f"Cache set object error: {e}")
            return False
    
    # ========== 哈希表操作 ==========
    
    async def hget(self, key: str, field: str) -> Optional[str]:
        """获取哈希表字段"""
        if not self._redis:
            return None
        try:
            value = await self._redis.hget(key, field)
            return value.decode('utf-8') if value else None
        except RedisError as e:
            logger.warning(f"Cache hget error: {e}")
            return None
    
    async def hset(
        self,
        key: str,
        field: str,
        value: str
    ) -> bool:
        """设置哈希表字段"""
        if not self._redis:
            return False
        try:
            await self._redis.hset(key, field, value)
            return True
        except RedisError as e:
            logger.warning(f"Cache hset error: {e}")
            return False
    
    async def hgetall(self, key: str) -> Optional[dict]:
        """获取整个哈希表"""
        if not self._redis:
            return None
        try:
            data = await self._redis.hgetall(key)
            return {k.decode('utf-8'): v.decode('utf-8') 
                    for k, v in data.items()} if data else {}
        except RedisError as e:
            logger.warning(f"Cache hgetall error: {e}")
            return None
    
    async def hdel(self, key: str, *fields: str) -> bool:
        """删除哈希表字段"""
        if not self._redis:
            return False
        try:
            await self._redis.hdel(key, *fields)
            return True
        except RedisError as e:
            logger.warning(f"Cache hdel error: {e}")
            return False
    
    # ========== 列表操作 ==========
    
    async def lpush(self, key: str, *values: str) -> int:
        """从左侧推入列表"""
        if not self._redis:
            return 0
        try:
            return await self._redis.lpush(key, *values)
        except RedisError as e:
            logger.warning(f"Cache lpush error: {e}")
            return 0
    
    async def rpop(self, key: str) -> Optional[str]:
        """从右侧弹出列表"""
        if not self._redis:
            return None
        try:
            value = await self._redis.rpop(key)
            return value.decode('utf-8') if value else None
        except RedisError as e:
            logger.warning(f"Cache rpop error: {e}")
            return None
    
    async def lrange(self, key: str, start: int, end: int) -> List[str]:
        """获取列表范围"""
        if not self._redis:
            return []
        try:
            values = await self._redis.lrange(key, start, end)
            return [v.decode('utf-8') for v in values] if values else []
        except RedisError as e:
            logger.warning(f"Cache lrange error: {e}")
            return []
    
    # ========== 批量操作 ==========
    
    async def mget(self, keys: List[str]) -> List[Optional[str]]:
        """批量获取"""
        if not self._redis:
            return [None] * len(keys)
        try:
            values = await self._redis.mget(keys)
            return [v.decode('utf-8') if v else None for v in values]
        except RedisError as e:
            logger.warning(f"Cache mget error: {e}")
            return [None] * len(keys)
    
    async def mset(self, mapping: dict, ttl: Optional[int] = None) -> bool:
        """批量设置"""
        if not self._redis:
            return False
        try:
            await self._redis.mset(mapping)
            if ttl:
                for key in mapping.keys():
                    await self._redis.expire(key, ttl)
            return True
        except RedisError as e:
            logger.warning(f"Cache mset error: {e}")
            return False
    
    # ========== 模式匹配删除 ==========
    
    async def delete_pattern(self, pattern: str) -> int:
        """删除匹配模式的所有键"""
        if not self._redis:
            return 0
        try:
            keys = []
            async for key in self._redis.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                return await self._redis.delete(*keys)
            return 0
        except RedisError as e:
            logger.warning(f"Cache delete_pattern error: {e}")
            return 0
    
    async def keys(self, pattern: str) -> List[str]:
        """查找匹配模式的键"""
        if not self._redis:
            return []
        try:
            keys = []
            async for key in self._redis.scan_iter(match=pattern):
                keys.append(key.decode('utf-8'))
            return keys
        except RedisError as e:
            logger.warning(f"Cache keys error: {e}")
            return []
    
    # ========== 统计信息 ==========
    
    async def info(self) -> dict:
        """获取 Redis 信息"""
        if not self._redis:
            return {}
        try:
            info = await self._redis.info()
            return {k.decode('utf-8') if isinstance(k, bytes) else k: 
                    v.decode('utf-8') if isinstance(v, bytes) else v 
                    for k, v in info.items()}
        except RedisError as e:
            logger.warning(f"Cache info error: {e}")
            return {}


# 全局缓存客户端实例
_cache_client: Optional[CacheClient] = None


def get_cache_client() -> CacheClient:
    """获取全局缓存客户端"""
    global _cache_client
    if _cache_client is None:
        _cache_client = CacheClient()
    return _cache_client


def set_cache_client(redis_client: redis.Redis):
    """设置全局缓存客户端"""
    global _cache_client
    _cache_client = CacheClient(redis_client)


async def init_cache_client(redis_url: str = None):
    """初始化缓存客户端"""
    from infrastructure.config import get_redis_settings
    
    if redis_url is None:
        settings = get_redis_settings()
        redis_url = settings.url
    
    try:
        redis_client = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=False  # 我们需要处理二进制数据
        )
        # 测试连接
        await redis_client.ping()
        set_cache_client(redis_client)
        logger.info(f"Cache client initialized: {redis_url}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize cache client: {e}")
        return False
