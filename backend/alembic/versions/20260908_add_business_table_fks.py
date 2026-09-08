"""add class_id/semester_id FK columns to business tables

业务表 FK 改造（方案 Phase 1 步骤 8/11）：加列 + FK + 索引，纯 DDL，
回填由种子脚本负责（幂等，仅当前学期）。旧字符串字段保留（双写过渡期）。

Revision ID: 20260908_add_business_table_fks
Revises: 20260908_backfill_course_schedule_week_type
Create Date: 2026-09-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260908_add_business_table_fks'
down_revision: Union[str, Sequence[str], None] = '20260908_backfill_course_schedule_week_type'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 加 class_id + semester_id 的表（含班名与学期字符串）
CLASS_TABLES = [
    'course_schedules', 'course_sessions', 'checkin_records', 'groups', 'questions',
]
# 仅加 semester_id 的表（无班名字段）
SEMESTER_ONLY_TABLES = [
    'score_logs', 'schedule_adjustments', 'group_score_logs', 'audit_logs',
]


def _add_class_and_semester(table: str) -> None:
    """给表加 class_id/semester_id 可空列 + FK + 索引"""
    op.add_column(table, sa.Column('class_id', sa.Integer(), nullable=True))
    op.add_column(table, sa.Column('semester_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        f'fk_{table}_class_id_classes', table, 'classes', ['class_id'], ['id'],
    )
    op.create_foreign_key(
        f'fk_{table}_semester_id_semesters', table, 'semesters', ['semester_id'], ['id'],
    )
    op.create_index(f'idx_{table}_class_id', table, ['class_id'], unique=False)
    op.create_index(f'idx_{table}_semester_id', table, ['semester_id'], unique=False)


def _add_semester_only(table: str) -> None:
    """给表加 semester_id 可空列 + FK + 索引"""
    op.add_column(table, sa.Column('semester_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        f'fk_{table}_semester_id_semesters', table, 'semesters', ['semester_id'], ['id'],
    )
    op.create_index(f'idx_{table}_semester_id', table, ['semester_id'], unique=False)


def upgrade() -> None:
    """业务表加 FK 列（可空，双写过渡期）"""
    for table in CLASS_TABLES:
        _add_class_and_semester(table)
    for table in SEMESTER_ONLY_TABLES:
        _add_semester_only(table)


def downgrade() -> None:
    """回滚：按逆序删除列/FK/索引"""
    for table in reversed(SEMESTER_ONLY_TABLES):
        op.drop_index(f'idx_{table}_semester_id', table_name=table)
        op.drop_constraint(f'fk_{table}_semester_id_semesters', table, type_='foreignkey')
        op.drop_column(table, 'semester_id')
    for table in reversed(CLASS_TABLES):
        op.drop_index(f'idx_{table}_semester_id', table_name=table)
        op.drop_index(f'idx_{table}_class_id', table_name=table)
        op.drop_constraint(f'fk_{table}_semester_id_semesters', table, type_='foreignkey')
        op.drop_constraint(f'fk_{table}_class_id_classes', table, type_='foreignkey')
        op.drop_column(table, 'semester_id')
        op.drop_column(table, 'class_id')
