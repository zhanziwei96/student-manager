"""座位系统迁移测试：建表幂等 + 列幂等。"""
import pytest
from sqlalchemy import create_engine, text
from alembic.config import Config
from alembic import command
import os


def _alembic_cfg(db_url: str) -> Config:
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cfg = Config(os.path.join(root, "backend", "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(root, "backend", "alembic"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def _run_upgrade(db_url: str) -> None:
    """把 alembic 指向迁移测试库并 upgrade 到 head。

    env.py 会用 get_settings().get_database_url() 覆盖 sqlalchemy.url，
    所以必须走 DATABASE__URL 环境变量；get_settings 有双层缓存
    （lru_cache + 模块级 _settings），reload_settings() + cache_clear() 缺一不可。
    """
    from app.core.config import get_settings, reload_settings

    old = os.environ.get("DATABASE__URL")
    os.environ["DATABASE__URL"] = db_url
    reload_settings()
    get_settings.cache_clear()
    try:
        command.upgrade(_alembic_cfg(db_url), "head")
    finally:
        if old is not None:
            os.environ["DATABASE__URL"] = old
        else:
            os.environ.pop("DATABASE__URL", None)
        reload_settings()
        get_settings.cache_clear()


@pytest.fixture()
def scratch_db():
    """独占迁移测试库分片（PYTEST_XDIST_WORKER 决定库名）。"""
    worker = os.environ.get("PYTEST_XDIST_WORKER", "gw0")
    suffix = worker[2:] if worker.startswith("gw") else "0"
    url = f"postgresql+psycopg2://classhub:classhub_dev@localhost:5432/classhub_migration_test_{suffix}"
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
    yield url
    engine.dispose()


def _table_exists(url, table):
    engine = create_engine(url)
    with engine.connect() as conn:
        return conn.execute(
            text("SELECT to_regclass(:t) IS NOT NULL"), {"t": f"public.{table}"}
        ).scalar()


def _column_exists(url, table, column):
    engine = create_engine(url)
    with engine.connect() as conn:
        return conn.execute(
            text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
                "WHERE table_name=:t AND column_name=:c)"
            ),
            {"t": table, "c": column},
        ).scalar()


def _index_exists(url, index):
    engine = create_engine(url)
    with engine.connect() as conn:
        return conn.execute(
            text("SELECT to_regclass(:t) IS NOT NULL"), {"t": f"public.{index}"}
        ).scalar()


def _constraint_exists(url, table, constraint):
    engine = create_engine(url)
    with engine.connect() as conn:
        return conn.execute(
            text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.table_constraints "
                "WHERE table_name=:t AND constraint_name=:c)"
            ),
            {"t": table, "c": constraint},
        ).scalar()


class TestSeatSystemMigration:
    def test_upgrade_creates_seat_tables(self, scratch_db):
        _run_upgrade(scratch_db)
        for table in ("classrooms", "seats", "seat_assignments", "seat_session_overrides"):
            assert _table_exists(scratch_db, table), f"缺表 {table}"
        assert _column_exists(scratch_db, "checkin_records", "seat_id")

    def test_upgrade_creates_concurrency_guards(self, scratch_db):
        _run_upgrade(scratch_db)
        assert _index_exists(scratch_db, "uix_checkin_session_seat")
        assert _constraint_exists(
            scratch_db, "seat_session_overrides", "uix_override_session_seat")

    def test_upgrade_is_idempotent(self, scratch_db):
        _run_upgrade(scratch_db)
        _run_upgrade(scratch_db)  # 第二次不得报错
