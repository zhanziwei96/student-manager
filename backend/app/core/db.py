"""
数据库连接 - SQLModel 版本
支持 SQLite WAL 模式和连接池，提升并发性能
"""
from typing import Generator
from sqlalchemy import event
from sqlalchemy.pool import QueuePool
from sqlmodel import SQLModel, Session, create_engine
from app.core.config import get_settings
import sqlite3

settings = get_settings()


def _set_sqlite_pragma(dbapi_conn, connection_record):
    """设置 SQLite 连接参数 - 启用 WAL 模式提升并发性能"""
    cursor = dbapi_conn.cursor()
    # 启用 WAL 模式：读写互不阻塞，并发性能提升 10-100 倍
    cursor.execute("PRAGMA journal_mode=WAL")
    # 同步模式设置为 NORMAL：平衡性能和数据安全
    cursor.execute("PRAGMA synchronous=NORMAL")
    # 临时表存储在内存中，提升性能
    cursor.execute("PRAGMA temp_store=MEMORY")
    # 增加缓存大小（页数，每页 4KB）
    cursor.execute("PRAGMA cache_size=10000")
    # 启用外键约束
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# 创建数据库引擎 - 使用连接池管理连接
engine = create_engine(
    f"sqlite:///{settings.get_database_path()}",
    connect_args={
        "check_same_thread": False,
        "timeout": 30,  # 连接超时时间（秒）
    },
    poolclass=QueuePool,
    pool_size=10,          # 连接池大小
    max_overflow=20,       # 超出 pool_size 时的额外连接数
    pool_timeout=30,       # 获取连接的超时时间
    pool_recycle=3600,     # 连接回收时间（秒）
    echo=settings.app.debug
)

# 注册连接创建事件，自动设置 WAL 模式
event.listen(engine, "connect", _set_sqlite_pragma)


def init_db() -> None:
    """初始化数据库表"""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """获取数据库会话 - 用于依赖注入"""
    with Session(engine) as session:
        yield session
