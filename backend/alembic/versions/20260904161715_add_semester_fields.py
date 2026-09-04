"""add semester fields

Revision ID: 20260904161715
Revises: 8d7a9e6f9898
Create Date: 2026-09-04 16:17:17.334547

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20260904161715'
down_revision: Union[str, Sequence[str], None] = '8d7a9e6f9898'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 上学期（第一学期）标识，历史数据统一回填
PREVIOUS_TERM = '2025-2026-2'

# 需要加 semester 列的表
SEMESTER_TABLES = [
    'course_schedules',
    'course_sessions',
    'schedule_adjustments',
    'checkin_records',
    'score_logs',
    'groups',
    'group_tasks',
    'group_evaluation_scores',
    'questions',
]


def upgrade() -> None:
    """加 semester 列 + 回填历史数据 + 建索引 + 重建活跃课堂唯一索引"""
    for table in SEMESTER_TABLES:
        op.add_column(table, sa.Column('semester', sa.String(length=20), nullable=True))
        # 历史数据回填上学期
        op.execute(f"UPDATE {table} SET semester = '{PREVIOUS_TERM}'")
        # 学期过滤索引
        op.create_index(f'ix_{table}_semester', table, ['semester'], unique=False)

    # course_sessions 部分唯一索引重建：加入 semester 维度
    # （旧的 uix_active_class_name 不含学期，会卡住新学期开课）
    op.drop_index('uix_active_class_name', table_name='course_sessions')
    op.create_index(
        'uix_active_class_semester',
        'course_sessions',
        ['class_name', 'semester'],
        unique=True,
        sqlite_where=sa.text('status="active"'),
        postgresql_where=sa.text("status='active'"),
    )


def downgrade() -> None:
    """回滚：删索引、删列"""
    op.drop_index('uix_active_class_semester', table_name='course_sessions')
    op.create_index(
        'uix_active_class_name',
        'course_sessions',
        ['class_name'],
        unique=True,
        sqlite_where=sa.text('status="active"'),
        postgresql_where=sa.text("status='active'"),
    )
    for table in reversed(SEMESTER_TABLES):
        op.drop_index(f'ix_{table}_semester', table_name=table)
        op.drop_column(table, 'semester')
