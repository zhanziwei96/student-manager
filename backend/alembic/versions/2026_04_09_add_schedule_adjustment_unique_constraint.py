"""添加 ScheduleAdjustment 唯一约束

Revision ID: 2026_04_09_add_schedule_adjustment_unique_constraint
Revises: 5bc3d1e6b181
Create Date: 2026-04-09 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = '2026_04_09_add_schedule_adjustment_unique_constraint'
down_revision: Union[str, None] = '5bc3d1e6b181'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite 需要使用 batch_alter_table 来添加约束（copy-and-move 策略）
    with op.batch_alter_table('schedule_adjustments', schema=None) as batch_op:
        batch_op.create_unique_constraint(
            'uix_schedule_week',
            ['schedule_id', 'week_number']
        )


def downgrade() -> None:
    with op.batch_alter_table('schedule_adjustments', schema=None) as batch_op:
        batch_op.drop_constraint('uix_schedule_week', type_='unique')
