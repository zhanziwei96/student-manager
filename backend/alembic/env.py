"""
Alembic 迁移环境配置
使用项目的数据库配置和 SQLModel 模型
"""
import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool, create_engine
from alembic import context

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入项目配置
from app.core.config import get_settings

# 导入所有 SQLModel 模型以支持 autogenerate
from sqlmodel import SQLModel
from app.models.user import User
from app.models.student import Student
from app.models.checkin import CheckinRecord, ScoreLog
from app.models.audit import AuditLog
from app.models.course_schedule import CourseSchedule
from app.models.course_session import CourseSession, ScheduleAdjustment
from app.models.group import (
    Group, GroupMember, GroupMembershipRequest,
    GroupTask, GroupTaskDimension, EvaluationAssignment,
    GroupEvaluationScore, GroupDissolutionRequest,
    ClassGroupSettings,
)

# Alembic 配置对象
config = context.config

# 获取应用配置
settings = get_settings()
database_url = settings.get_database_url()

# 设置 sqlalchemy.url
config.set_main_option("sqlalchemy.url", database_url)

# 配置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 目标元数据 - 用于 autogenerate
target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """
    离线模式运行迁移（生成 SQL 脚本）
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    在线模式运行迁移（直接操作数据库）
    """
    # 创建独立的数据库引擎（不使用项目的 WAL 模式设置）
    connectable = create_engine(
        database_url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # SQLite 特定配置
            render_as_batch=True,  # 支持 SQLite 的 ALTER 操作
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
