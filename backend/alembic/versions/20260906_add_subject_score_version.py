"""add version column to student_subject_scores

为 student_subject_scores 表添加乐观锁版本号列（与 students 表一致），
替代分数 CAS，解决 ABA 问题（80→90→80 会丢失更新）。

Revision ID: 20260906_subject_score_version
Revises: 20260906_subject_tables
Create Date: 2026-09-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260906_subject_score_version'
down_revision: Union[str, Sequence[str], None] = '20260906_subject_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加 version 列（默认 1）"""
    op.add_column(
        'student_subject_scores',
        sa.Column('version', sa.Integer(), nullable=False, server_default='1')
    )


def downgrade() -> None:
    """回滚：删除 version 列"""
    op.drop_column('student_subject_scores', 'version')
