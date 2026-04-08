"""
限流辅助工具 - 为每个 key 提供独立的 InMemoryBucket
修复 pyrate-limiter 默认 SingleBucketFactory 导致所有 key 共享计数器的问题
"""
from collections import OrderedDict
from typing import Optional
from fastapi import Request
from pyrate_limiter import BucketFactory, RateItem, AbstractBucket, InMemoryBucket, Rate
from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()


async def check_rate_limit(request: Request, identifier: str, key_prefix: str = "default", limiter_attr: str = "limiter") -> bool:
    """
    检查限流

    Args:
        request: FastAPI请求对象
        identifier: 限流标识（如用户名或学号）
        key_prefix: 限流 key 前缀（如 login / checkin）
        limiter_attr: 从 app.state 中获取 limiter 的属性名

    Returns:
        True: 允许请求
        False: 触发限流
    """
    if not settings.rate_limit.enabled:
        return True

    try:
        limiter = getattr(request.app.state, limiter_attr, None)
        if limiter:
            key = f"{key_prefix}:{identifier}"
            success = await limiter.try_acquire_async(key, blocking=False)
            return success
    except Exception as e:
        logger.warning(f"限流检查失败: {e}")

    return True


class PerKeyBucketFactory(BucketFactory):
    """
    按限流 key 隔离的 Bucket 工厂

    pyrate-limiter 默认的 SingleBucketFactory 对所有 key 返回同一个 bucket，
    导致不同用户/学号共享全局计数器。本工厂为每个 item.name 创建独立的
    InMemoryBucket，确保限流按 key 精确隔离。
    """

    def __init__(self, rates: list[Rate], max_buckets: int = 10000):
        self.rates = rates
        self._max_buckets = max_buckets
        self._buckets: OrderedDict[str, InMemoryBucket] = OrderedDict()
        # 占位 bucket，仅用于获取统一的时间戳（MonotonicClock）
        self._prototype = InMemoryBucket(rates)

    def wrap_item(self, name: str, weight: int = 1):
        now = self._prototype.now()
        return RateItem(name, now, weight=weight)

    def get(self, item: RateItem) -> AbstractBucket:
        key = item.name
        if key in self._buckets:
            # LRU: 移动到末尾
            self._buckets.move_to_end(key)
            return self._buckets[key]

        bucket = InMemoryBucket(self.rates)
        self.schedule_leak(bucket)
        self._buckets[key] = bucket

        # 限制总 bucket 数，防止无限增长导致内存泄漏
        if len(self._buckets) > self._max_buckets:
            # 弹出最久未使用的 bucket
            _, old_bucket = self._buckets.popitem(last=False)
            old_bucket.flush()

        return bucket
