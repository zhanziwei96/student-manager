"""
限流 BucketFactory 单元测试
验证 PerKeyBucketFactory 按 key 隔离计数器，避免全局共享
"""
import pytest
import asyncio
from pyrate_limiter import Limiter, Rate
from app.core.rate_limit import PerKeyBucketFactory


class TestPerKeyBucketFactory:
    """测试 PerKeyBucketFactory 的 key 隔离特性"""

    @pytest.mark.asyncio
    async def test_different_keys_do_not_share_limit(self):
        """不同 key 的限流计数器应相互独立"""
        rate = Rate(2, 10_000)  # 10 秒内 2 次
        limiter = Limiter(PerKeyBucketFactory([rate]))

        # user1 用掉 2 次配额
        assert await limiter.try_acquire_async("user1", blocking=False) is True
        assert await limiter.try_acquire_async("user1", blocking=False) is True
        # user1 第 3 次应被限流
        assert await limiter.try_acquire_async("user1", blocking=False) is False

        # user2 仍应能正常使用自己的配额，不受 user1 影响
        assert await limiter.try_acquire_async("user2", blocking=False) is True
        assert await limiter.try_acquire_async("user2", blocking=False) is True
        assert await limiter.try_acquire_async("user2", blocking=False) is False

    @pytest.mark.asyncio
    async def test_same_key_shares_limit(self):
        """相同 key 应共享限流计数器"""
        rate = Rate(3, 10_000)
        limiter = Limiter(PerKeyBucketFactory([rate]))

        assert await limiter.try_acquire_async("user1", blocking=False) is True
        assert await limiter.try_acquire_async("user1", blocking=False) is True
        assert await limiter.try_acquire_async("user1", blocking=False) is True
        assert await limiter.try_acquire_async("user1", blocking=False) is False

    def test_factory_creates_separate_buckets(self):
        """factory.get() 对不同 item.name 返回不同 bucket"""
        rate = Rate(2, 10_000)
        factory = PerKeyBucketFactory([rate])

        item_a = factory.wrap_item("a", weight=1)
        item_b = factory.wrap_item("b", weight=1)

        bucket_a = factory.get(item_a)
        bucket_b = factory.get(item_b)

        assert bucket_a is not bucket_b, "不同 key 应返回独立实例"

        item_a2 = factory.wrap_item("a", weight=1)
        bucket_a2 = factory.get(item_a2)
        assert bucket_a is bucket_a2, "相同 key 应返回同一实例"
