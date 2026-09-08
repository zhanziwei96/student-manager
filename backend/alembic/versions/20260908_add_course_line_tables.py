"""add course line tables: courses, course_offerings, enrollments

学期/届数重构 Phase 1b — 课程线三表（见 docs/SEMESTER_COHORT_REFACTOR_PLAN.md 2.2）。
纯 DDL：数据回填由种子脚本负责（幂等，仅当前学期）。

Revision ID: 20260908_add_course_line_tables
Revises: 20260908_add_student_class_fields
Create Date: 2026-09-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260908_add_course_line_tables'
down_revision: Union[str, Sequence[str], None] = '20260908_add_student_class_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建 courses / course_offerings / enrollments 三张课程线表"""
    # courses 表 — 课程目录（跨学期稳定）
    op.create_table(
        'courses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('department', sa.String(length=50), nullable=False, server_default=''),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uix_course_code'),
    )

    # course_offerings 表 — 教学班/开课（课程×学期×教师×范围）
    op.create_table(
        'course_offerings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('semester_id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=True),
        sa.Column('teacher_name', sa.String(length=50), nullable=False, server_default=''),
        sa.Column('class_scope', sa.String(length=100), nullable=False),
        sa.Column('capacity', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('course_id', 'semester_id', 'teacher_id', 'class_scope',
                            name='uix_offering'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id']),
        sa.ForeignKeyConstraint(['semester_id'], ['semesters.id']),
        sa.ForeignKeyConstraint(['teacher_id'], ['users.id']),
    )
    op.create_index('idx_offerings_course_id', 'course_offerings', ['course_id'], unique=False)
    op.create_index('idx_offerings_semester_id', 'course_offerings', ['semester_id'], unique=False)

    # enrollments 表 — 选课（学生×教学班×学期，个人成绩 + 期末成绩）
    op.create_table(
        'enrollments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.String(length=50), nullable=False),
        sa.Column('offering_id', sa.Integer(), nullable=False),
        sa.Column('semester_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='enrolled'),
        sa.Column('score', sa.Float(), nullable=False, server_default='0'),
        sa.Column('final_score', sa.Float(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id', 'offering_id', name='uix_enrollment'),
        sa.ForeignKeyConstraint(['student_id'], ['students.student_id']),
        sa.ForeignKeyConstraint(['offering_id'], ['course_offerings.id']),
        sa.ForeignKeyConstraint(['semester_id'], ['semesters.id']),
    )
    op.create_index('idx_enrollments_offering_id', 'enrollments', ['offering_id'], unique=False)
    op.create_index('idx_enrollments_semester_student', 'enrollments',
                    ['semester_id', 'student_id'], unique=False)


def downgrade() -> None:
    """回滚：按依赖顺序删除三张表"""
    op.drop_table('enrollments')
    op.drop_table('course_offerings')
    op.drop_table('courses')
