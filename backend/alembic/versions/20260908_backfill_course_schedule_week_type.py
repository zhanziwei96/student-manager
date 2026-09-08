"""backfill missing column: course_schedules.week_type

week_type（周类型 all|odd|even|custom）历史上由 create_all 建列、从未进迁移链，
导致干净库上的 course_schedules 缺列（产品代码按模型读写会报错）。

Revision ID: 20260908_backfill_course_schedule_week_type
Revises: 20260908_add_student_class_semesters
Create Date: 2026-09-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260908_backfill_course_schedule_week_type'
down_revision: Union[str, Sequence[str], None] = '20260908_add_student_class_semesters'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """course_schedules 补 week_type 列（与模型 CourseScheduleBase 对齐）"""
    op.add_column(
        'course_schedules',
        sa.Column('week_type', sa.String(length=20), nullable=False, server_default='all'),
    )


def downgrade() -> None:
    """回滚：删除补列"""
    op.drop_column('course_schedules', 'week_type')
