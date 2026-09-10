"""压力测试夹具：复用集成测试的测试库夹具

压力测试跑在进程内 ASGI + 独立测试库（classhub_test_N）上，
既不依赖外部服务，也不会触碰开发库数据。
"""
from tests.integration.conftest import (  # noqa: F401
    admin_client,
    admin_user,
    ensure_class,
    ensure_current_semester,
    seed_refs,
    teacher_user,
    test_engine,
)
