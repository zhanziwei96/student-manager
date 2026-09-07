"""add group subject score

为 groups 表添加 subject_id、score、version 字段，并新建 group_score_logs 表（小组分数变更日志）。

Revision ID: 20260907_add_group_subject_score
Revises: 20260906_subject_score_version
Create Date: 2026-09-07 20:00:07.028636

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260907_add_group_subject_score'
down_revision: Union[str, Sequence[str], None] = '20260906_subject_score_version'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """groups 表加科目/分数字段，并创建小组分数变更日志表"""
    # groups 表新增字段
    op.add_column(
        'groups',
        sa.Column('subject_id', sa.Integer(), nullable=True)
    )
    op.add_column(
        'groups',
        sa.Column('score', sa.Float(), nullable=False, server_default='0')
    )
    op.add_column(
        'groups',
        sa.Column('version', sa.Integer(), nullable=False, server_default='1')
    )
    op.create_index('ix_groups_subject_id', 'groups', ['subject_id'], unique=False)
    op.create_index('ix_groups_score', 'groups', ['score'], unique=False)
    op.create_foreign_key(
        'fk_groups_subject_id_subjects',
        'groups', 'subjects',
        ['subject_id'], ['id']
    )

    # group_score_logs 表
    op.create_table(
        'group_score_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=True),
        sa.Column('old_score', sa.Float(), nullable=True),
        sa.Column('new_score', sa.Float(), nullable=True),
        sa.Column('delta', sa.Float(), nullable=True),
        sa.Column('reason', sa.String(), nullable=True),
        sa.Column('operator', sa.String(), nullable=True),
        sa.Column('semester', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_group_score_logs_group_id', 'group_score_logs', ['group_id'], unique=False)
    op.create_index('idx_group_score_logs_group_created_at', 'group_score_logs', ['group_id', sa.text('created_at DESC')], unique=False)


def downgrade() -> None:
    """回滚：删除日志表及 groups 新增字段"""
    op.drop_index('idx_group_score_logs_group_created_at', table_name='group_score_logs')
    op.drop_index('ix_group_score_logs_group_id', table_name='group_score_logs')
    op.drop_table('group_score_logs')

    op.drop_constraint('fk_groups_subject_id_subjects', 'groups', type_='foreignkey')
    op.drop_index('ix_groups_score', table_name='groups')
    op.drop_index('ix_groups_subject_id', table_name='groups')
    op.drop_column('groups', 'version')
    op.drop_column('groups', 'score')
    op.drop_column('groups', 'subject_id')
