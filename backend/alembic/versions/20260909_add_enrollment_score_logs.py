"""add enrollment_score_logs

选课成绩变更日志（个人成绩/期末成绩），结构仿 group_score_logs 挂 enrollments。

Revision ID: 20260909_add_enrollment_score_logs
Revises: 20260908_rekey_class_group_settings
Create Date: 2026-09-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260909_add_enrollment_score_logs'
down_revision: Union[str, Sequence[str], None] = '20260908_rekey_class_group_settings'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建 enrollment_score_logs 表"""
    op.create_table(
        'enrollment_score_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('enrollment_id', sa.Integer(), nullable=False),
        sa.Column('old_score', sa.Float(), nullable=True),
        sa.Column('new_score', sa.Float(), nullable=True),
        sa.Column('delta', sa.Float(), nullable=True),
        sa.Column('reason', sa.String(length=200), nullable=True),
        sa.Column('operator', sa.String(length=50), nullable=True),
        sa.Column('semester_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['enrollment_id'], ['enrollments.id']),
        sa.ForeignKeyConstraint(['semester_id'], ['semesters.id']),
    )
    op.create_index(
        'idx_enrollment_score_logs_enrollment_created', 'enrollment_score_logs',
        ['enrollment_id', 'created_at'], unique=False,
    )


def downgrade() -> None:
    """回滚：删除日志表"""
    op.drop_index('idx_enrollment_score_logs_enrollment_created', table_name='enrollment_score_logs')
    op.drop_table('enrollment_score_logs')
