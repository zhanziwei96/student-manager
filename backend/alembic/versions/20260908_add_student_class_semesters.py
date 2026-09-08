"""add student_class_semesters bridge and groups.course_id

学生-行政班-学期归属桥接表 + 小组科目外键改造（subject_id → course_id，过渡期双列）。

Revision ID: 20260908_add_student_class_semesters
Revises: 20260908_add_course_line_tables
Create Date: 2026-09-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260908_add_student_class_semesters'
down_revision: Union[str, Sequence[str], None] = '20260908_add_course_line_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建 student_class_semesters 表 + groups 加 course_id 列"""
    # student_class_semesters — 记录学生每个学期的行政班归属
    op.create_table(
        'student_class_semesters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.String(length=50), nullable=False),
        sa.Column('class_id', sa.Integer(), nullable=False),
        sa.Column('semester_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id', 'semester_id', name='uix_student_class_semester'),
        sa.ForeignKeyConstraint(['student_id'], ['students.student_id']),
        sa.ForeignKeyConstraint(['class_id'], ['classes.id']),
        sa.ForeignKeyConstraint(['semester_id'], ['semesters.id']),
    )
    op.create_index('idx_scs_student_id', 'student_class_semesters', ['student_id'], unique=False)
    op.create_index('idx_scs_class_id', 'student_class_semesters', ['class_id'], unique=False)
    op.create_index('idx_scs_semester_id', 'student_class_semesters', ['semester_id'], unique=False)

    # groups 加 course_id（过渡期双列，subject_id 保留至 Phase 4 删除）
    op.add_column('groups', sa.Column('course_id', sa.Integer(), nullable=True))
    op.create_index('idx_groups_course_id', 'groups', ['course_id'], unique=False)
    op.create_foreign_key(
        'fk_groups_course_id_courses', 'groups', 'courses',
        ['course_id'], ['id'],
    )


def downgrade() -> None:
    """回滚：删桥接表 + groups 去掉 course_id"""
    op.drop_constraint('fk_groups_course_id_courses', 'groups', type_='foreignkey')
    op.drop_index('idx_groups_course_id', table_name='groups')
    op.drop_column('groups', 'course_id')
    op.drop_table('student_class_semesters')
