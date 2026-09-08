"""backfill missing tables: questions, answers

questions/answers 历史上由 SQLModel.metadata.create_all 创建（从未进迁移链），
导致干净库上 add_semester_fields 迁移 ALTER 时 relation 不存在。
本迁移在 add_semester_fields 之前补建（不含 semester 列，交由下游迁移加列）。

Revision ID: 20260908_backfill_missing_tables
Revises: 8d7a9e6f9898
Create Date: 2026-09-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260908_backfill_missing_tables'
down_revision: Union[str, Sequence[str], None] = '8d7a9e6f9898'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """补建 questions / answers（结构与 semester 加列前的模型一致）"""
    op.create_table(
        'questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('class_name', sa.String(length=100), nullable=True),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('is_realtime', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['teacher_id'], ['users.id']),
    )
    op.create_index('ix_questions_teacher_id', 'questions', ['teacher_id'], unique=False)
    op.create_index('ix_questions_class_name', 'questions', ['class_name'], unique=False)

    op.create_table(
        'answers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.String(length=50), nullable=False),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('is_anonymous', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_starred', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id']),
        sa.ForeignKeyConstraint(['parent_id'], ['answers.id']),
    )
    op.create_index('ix_answers_question_id', 'answers', ['question_id'], unique=False)
    op.create_index('ix_answers_student_id', 'answers', ['student_id'], unique=False)


def downgrade() -> None:
    """回滚：删除两张补建表"""
    op.drop_table('answers')
    op.drop_table('questions')
