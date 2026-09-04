"""add student login lockout fields

为学生表添加登录锁定机制字段：
- login_fail_count: 登录失败次数（默认 0）
- locked_until: 锁定截止时间（可空）

Revision ID: 20260904_student_lockout
Revises: 20260904161715
Create Date: 2026-09-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20260904_student_lockout'
down_revision: Union[str, Sequence[str], None] = '20260904161715'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加学生登录锁定字段"""
    op.add_column(
        'students',
        sa.Column('login_fail_count', sa.Integer(), nullable=False, server_default='0')
    )
    op.add_column(
        'students',
        sa.Column('locked_until', sa.DateTime(), nullable=True)
    )


def downgrade() -> None:
    """移除学生登录锁定字段"""
    op.drop_column('students', 'locked_until')
    op.drop_column('students', 'login_fail_count')
