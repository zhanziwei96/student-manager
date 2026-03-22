"""
数据库连接 - SQLModel 版本
"""
from typing import Generator
from sqlmodel import SQLModel, Session, create_engine
from app.core.config import get_settings

settings = get_settings()

# 创建数据库引擎
engine = create_engine(
    f"sqlite:///{settings.get_database_path()}",
    connect_args={"check_same_thread": False},
    echo=settings.app.debug
)


def init_db() -> None:
    """初始化数据库表"""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """获取数据库会话 - 用于依赖注入"""
    with Session(engine) as session:
        yield session
