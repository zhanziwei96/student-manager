"""add classes.status (归档保留历史，ADM-05)

班级退役方式：归档（status=archived）而非硬删除——历史课堂/签到/成绩仍引用
classes.id（8 张表外键 RESTRICT），归档后不再出现在班级列表与下拉中。

Revision ID: 20260911_add_class_status
Revises: 20260910_remove_redundant_string_columns
"""
from typing import Union, Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260911_add_class_status"
down_revision: Union[str, Sequence[str], None] = "20260910_remove_redundant_string_columns"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('classes', sa.Column(
        'status', sa.String(length=20), nullable=False, server_default='active',
        comment='状态: active|archived（归档保留历史）',
    ))
    op.create_index('ix_classes_status', 'classes', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_classes_status', table_name='classes')
    op.drop_column('classes', 'status')
