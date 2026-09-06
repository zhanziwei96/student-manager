"""add subject tables

Revision ID: 20260906_subject_tables
Revises: 20260904_student_lockout
Create Date: 2026-09-06 21:53:52.426233

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260906_subject_tables'
down_revision: Union[str, Sequence[str], None] = '20260904_student_lockout'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建科目相关表"""
    # 科目表
    op.create_table(
        'subjects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('semester', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'semester', name='uix_subject_name_semester')
    )
    op.create_index('ix_subjects_semester', 'subjects', ['semester'], unique=False)

    # 学生科目分数表
    op.create_table(
        'student_subject_scores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.String(length=50), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('semester', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ),
        sa.ForeignKeyConstraint(['teacher_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id', 'subject_id', 'teacher_id', 'semester', name='uix_student_subject_teacher_semester')
    )
    op.create_index('ix_student_subject_scores_student_id', 'student_subject_scores', ['student_id'], unique=False)
    op.create_index('ix_student_subject_scores_subject_id', 'student_subject_scores', ['subject_id'], unique=False)
    op.create_index('ix_student_subject_scores_teacher_id', 'student_subject_scores', ['teacher_id'], unique=False)
    op.create_index('ix_student_subject_scores_score', 'student_subject_scores', ['score'], unique=False)
    op.create_index('ix_student_subject_scores_semester', 'student_subject_scores', ['semester'], unique=False)

    # 学生科目分数日志表
    op.create_table(
        'student_subject_score_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.String(length=50), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('old_score', sa.Float(), nullable=True),
        sa.Column('new_score', sa.Float(), nullable=True),
        sa.Column('delta', sa.Float(), nullable=True),
        sa.Column('reason', sa.String(), nullable=True),
        sa.Column('operator', sa.String(), nullable=True),
        sa.Column('semester', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_subject_score_logs_student_created_at', 'student_subject_score_logs', ['student_id', sa.text('created_at DESC')], unique=False)


def downgrade() -> None:
    """回滚：删除科目相关表"""
    op.drop_index('idx_subject_score_logs_student_created_at', table_name='student_subject_score_logs')
    op.drop_table('student_subject_score_logs')

    op.drop_index('ix_student_subject_scores_semester', table_name='student_subject_scores')
    op.drop_index('ix_student_subject_scores_score', table_name='student_subject_scores')
    op.drop_index('ix_student_subject_scores_teacher_id', table_name='student_subject_scores')
    op.drop_index('ix_student_subject_scores_subject_id', table_name='student_subject_scores')
    op.drop_index('ix_student_subject_scores_student_id', table_name='student_subject_scores')
    op.drop_table('student_subject_scores')

    op.drop_index('ix_subjects_semester', table_name='subjects')
    op.drop_table('subjects')
