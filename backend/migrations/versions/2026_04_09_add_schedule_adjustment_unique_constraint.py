"""add schedule_adjustment unique constraint

Revision ID: 2026_04_09_add_schedule_adjustment_unique_constraint
Revises: 2026_04_06_course_session_migration
Create Date: 2026-04-09 20:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = '2026_04_09_add_schedule_adjustment_unique_constraint'
down_revision: Union[str, None] = '2026_04_06_course_session_migration'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 添加 schedule_adjustments 表的唯一约束
    with op.batch_alter_table('schedule_adjustments', schema=None) as batch_op:
        batch_op.create_unique_constraint(
            'uix_schedule_week',
            ['schedule_id', 'week_number']
        )


def downgrade() -> None:
    # 删除唯一约束
    with op.batch_alter_table('schedule_adjustments', schema=None) as batch_op:
        batch_op.drop_constraint('uix_schedule_week', type_='unique')
