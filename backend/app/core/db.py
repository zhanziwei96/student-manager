"""
数据库连接 - SQLModel 版本
支持 SQLite 和 PostgreSQL
"""
from typing import Generator
from sqlalchemy import event
from sqlalchemy.pool import QueuePool, NullPool
from sqlmodel import SQLModel, Session, create_engine
from app.core.config import get_settings

settings = get_settings()
DATABASE_URL = settings.get_database_url()
IS_SQLITE = DATABASE_URL.startswith("sqlite")


def _set_sqlite_pragma(dbapi_conn, connection_record):
    """设置 SQLite 连接参数 - 启用 WAL 模式提升并发性能"""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.execute("PRAGMA cache_size=20000")
    cursor.execute("PRAGMA wal_autocheckpoint=1000")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA mmap_size=33554432")
    cursor.close()


# 创建数据库引擎
if IS_SQLITE:
    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "check_same_thread": False,
            "timeout": 10,
        },
        poolclass=QueuePool,
        pool_size=20,
        max_overflow=30,
        pool_timeout=5,
        pool_recycle=1800,
        pool_pre_ping=True,
        echo=settings.app.debug
    )
    event.listen(engine, "connect", _set_sqlite_pragma)
else:
    # PostgreSQL 使用 NullPool 避免 Gunicorn 多 worker 连接池冲突
    # 或根据负载调整 pool_size
    engine = create_engine(
        DATABASE_URL,
        poolclass=NullPool,
        echo=settings.app.debug
    )


def init_db() -> None:
    """初始化数据库表"""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """获取数据库会话 - 用于依赖注入"""
    with Session(engine) as session:
        yield session
