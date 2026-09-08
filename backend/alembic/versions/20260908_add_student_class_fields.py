"""add students.class_id/cohort_year/status with backfill

students 表加班级外键、届、学籍状态三列，并按「导入年份即所属届」规则回填
（cohorts/classes/students 三级回填自包含，不依赖种子数据）。

Revision ID: 20260908_add_student_class_fields
Revises: 20260908_add_core_entity_tables
Create Date: 2026-09-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260908_add_student_class_fields'
down_revision: Union[str, Sequence[str], None] = '20260908_add_core_entity_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """students 加列 + 三级回填（cohorts ← classes ← students）"""
    op.add_column('students', sa.Column('class_id', sa.Integer(), nullable=True))
    op.add_column('students', sa.Column('cohort_year', sa.String(length=10), nullable=True))
    op.add_column(
        'students',
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
    )
    op.create_index('ix_students_class_id', 'students', ['class_id'], unique=False)
    op.create_index('ix_students_cohort_year', 'students', ['cohort_year'], unique=False)
    op.create_foreign_key(
        'fk_students_class_id_classes', 'students', 'classes',
        ['class_id'], ['id'],
    )

    # 1. 回填 cohorts：学生导入年份 DISTINCT 即届（在哪年导入就是哪届）
    op.execute("""
        INSERT INTO cohorts (year, label, status)
        SELECT DISTINCT
            EXTRACT(YEAR FROM created_at)::int::text,
            EXTRACT(YEAR FROM created_at)::int::text || '届',
            'active'
        FROM students
        WHERE created_at IS NOT NULL
        ON CONFLICT (year) DO NOTHING
    """)

    # 2. 回填 classes：按 (class_name, 导入年份) 推导（同班名不同届不冲突）
    op.execute("""
        INSERT INTO classes (name, major, cohort_year)
        SELECT DISTINCT
            class_name,
            '',
            EXTRACT(YEAR FROM created_at)::int::text
        FROM students
        WHERE class_name != '未分班' AND created_at IS NOT NULL
        ON CONFLICT (name, major, cohort_year) DO NOTHING
    """)

    # 3. 回填 students.class_id + cohort_year（未分班学生保持 NULL class_id）
    op.execute("""
        UPDATE students s
        SET cohort_year = EXTRACT(YEAR FROM s.created_at)::int::text,
            class_id = c.id
        FROM classes c
        WHERE c.name = s.class_name
          AND c.cohort_year = EXTRACT(YEAR FROM s.created_at)::int::text
    """)
    # 无班级归属（未分班/无 created_at）的学生至少补上届
    op.execute("""
        UPDATE students
        SET cohort_year = EXTRACT(YEAR FROM created_at)::int::text
        WHERE cohort_year IS NULL AND created_at IS NOT NULL
    """)


def downgrade() -> None:
    """回滚：删除三列（数据丢弃，班级/届表由上游迁移回滚）"""
    op.drop_constraint('fk_students_class_id_classes', 'students', type_='foreignkey')
    op.drop_index('ix_students_cohort_year', table_name='students')
    op.drop_index('ix_students_class_id', table_name='students')
    op.drop_column('students', 'status')
    op.drop_column('students', 'cohort_year')
    op.drop_column('students', 'class_id')
