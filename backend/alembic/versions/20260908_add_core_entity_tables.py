"""add core entity tables: semesters, cohorts, classes

学期/届数重构 Phase 1a — 核心实体表（见 docs/SEMESTER_COHORT_REFACTOR_PLAN.md 2.2）。

Revision ID: 20260908_add_core_entity_tables
Revises: 20260907_add_group_subject_score
Create Date: 2026-09-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260908_add_core_entity_tables'
down_revision: Union[str, Sequence[str], None] = '20260907_add_group_subject_score'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建 semesters / cohorts / classes 三张核心实体表"""
    # semesters 表 — 学期实体（替代 .env TermSettings）
    op.create_table(
        'semesters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('label', sa.String(length=20), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('total_weeks', sa.Integer(), nullable=False),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('label', name='uix_semester_label'),
    )
    # 部分索引：当前学期只有 1 行，索引极小（方案 4.1）
    op.create_index(
        'idx_semesters_is_current', 'semesters', ['is_current'],
        unique=False, postgresql_where=sa.text('is_current = TRUE'),
    )

    # cohorts 表 — 届（入学年份）
    op.create_table(
        'cohorts',
        sa.Column('year', sa.String(length=10), nullable=False),
        sa.Column('label', sa.String(length=50), nullable=False, server_default=''),
        sa.Column('entry_semester_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.PrimaryKeyConstraint('year'),
        sa.ForeignKeyConstraint(['entry_semester_id'], ['semesters.id']),
    )

    # classes 表 — 班级（届+专业下的班）
    op.create_table(
        'classes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('major', sa.String(length=50), nullable=False, server_default=''),
        sa.Column('cohort_year', sa.String(length=10), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'major', 'cohort_year', name='uix_class_name_major_cohort'),
        sa.ForeignKeyConstraint(['cohort_year'], ['cohorts.year']),
    )
    op.create_index('idx_classes_cohort_year', 'classes', ['cohort_year'], unique=False)


def downgrade() -> None:
    """回滚：按依赖顺序删除三张表"""
    op.drop_table('classes')
    op.drop_table('cohorts')
    op.drop_table('semesters')
