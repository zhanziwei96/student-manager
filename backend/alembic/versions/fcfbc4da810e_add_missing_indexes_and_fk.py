"""add_missing_indexes_and_fk

Revision ID: fcfbc4da810e
Revises: 2026_04_09_add_schedule_adjustment_unique_constraint
Create Date: 2026-04-10 10:51:42.078168

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fcfbc4da810e'
down_revision: Union[str, Sequence[str], None] = '2026_04_09_add_schedule_adjustment_unique_constraint'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # course_schedules 查询性能优化索引
    op.create_index('ix_course_schedules_teacher_id', 'course_schedules', ['teacher_id'], unique=False)
    op.create_index('ix_course_schedules_class_name', 'course_schedules', ['class_name'], unique=False)
    op.create_index('ix_course_schedules_day_of_week', 'course_schedules', ['day_of_week'], unique=False)

    # course_sessions 索引
    # uix_active_class_name 已在 initial migration 中创建，此处不再重复
    op.create_index('ix_sessions_schedule_week', 'course_sessions', ['schedule_id', 'week_number'], unique=False)
    op.create_index('ix_sessions_teacher_id', 'course_sessions', ['teacher_id'], unique=False)

    # checkin_records 外键约束（SQLite 需使用 batch_alter_table）
    with op.batch_alter_table('checkin_records', schema=None) as batch_op:
        batch_op.create_foreign_key(
            'fk_checkin_records_session_id',
            'course_sessions',
            ['session_id'],
            ['id']
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('checkin_records', schema=None) as batch_op:
        batch_op.drop_constraint('fk_checkin_records_session_id', type_='foreignkey')

    op.drop_index('ix_sessions_teacher_id', table_name='course_sessions')
    op.drop_index('ix_sessions_schedule_week', table_name='course_sessions')
    op.drop_index('ix_course_schedules_day_of_week', table_name='course_schedules')
    op.drop_index('ix_course_schedules_class_name', table_name='course_schedules')
    op.drop_index('ix_course_schedules_teacher_id', table_name='course_schedules')
