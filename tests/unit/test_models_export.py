"""模型导出契约测试：app.models.__all__ 必须与实际导出名称一致

历史问题：删除模型（如 ScoreLog、StudentSubjectScore）时漏删 __all__ 条目，
`from app.models import *` 会抛 AttributeError。本测试防止再次发生。
"""
import importlib

import pytest


@pytest.fixture(scope="module")
def models_module():
    return importlib.import_module("app.models")


def test_all_names_are_importable(models_module):
    """__all__ 中的每个名称都必须真实存在"""
    missing = [name for name in models_module.__all__ if not hasattr(models_module, name)]
    assert missing == [], f"__all__ 中以下名称不存在（删除模型时漏删）: {missing}"


def test_all_has_no_duplicates(models_module):
    """__all__ 不应有重复条目"""
    duplicated = {n for n in models_module.__all__ if models_module.__all__.count(n) > 1}
    assert duplicated == set(), f"__all__ 存在重复条目: {sorted(duplicated)}"


def test_star_import_works(models_module):
    """`from app.models import *` 可以正常执行（__all__ 全部可解析）"""
    namespace: dict = {}
    exec("from app.models import *", namespace)  # noqa: S102 - 验证模块导出契约
    exported = {k for k in namespace if not k.startswith("__")}
    assert set(models_module.__all__) <= exported
