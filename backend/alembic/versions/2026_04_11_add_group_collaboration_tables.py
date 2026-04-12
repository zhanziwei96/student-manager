"""add group collaboration tables

Revision ID: 2026_04_11_add_group_collaboration_tables
Revises: 2026_04_09_add_schedule_adjustment_unique_constraint
Create Date: 2026-04-11 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = '2026_04_11_add_group_collaboration_tables'
down_revision: Union[str, None] = '2026_04_09_add_schedule_adjustment_unique_constraint'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. groups
    op.create_table(
        'groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('class_name', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('leader_student_id', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_groups_class_name'), 'groups', ['class_name'], unique=False)
    op.create_index(op.f('ix_groups_leader_student_id'), 'groups', ['leader_student_id'], unique=False)

    # 2. group_members
    op.create_table(
        'group_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.String(length=50), nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_group_members_group_id'), 'group_members', ['group_id'], unique=False)
    op.create_index(op.f('ix_group_members_student_id'), 'group_members', ['student_id'], unique=False)

    # 3. group_membership_requests
    op.create_table(
        'group_membership_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_group_membership_requests_group_id'), 'group_membership_requests', ['group_id'], unique=False)
    op.create_index(op.f('ix_group_membership_requests_student_id'), 'group_membership_requests', ['student_id'], unique=False)

    # 4. group_tasks
    op.create_table(
        'group_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('class_name', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_by', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_group_tasks_class_name'), 'group_tasks', ['class_name'], unique=False)

    # 5. group_task_dimensions
    op.create_table(
        'group_task_dimensions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['group_tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_group_task_dimensions_task_id'), 'group_task_dimensions', ['task_id'], unique=False)

    # 6. evaluation_assignments
    op.create_table(
        'evaluation_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('evaluator_group_id', sa.Integer(), nullable=False),
        sa.Column('target_group_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['evaluator_group_id'], ['groups.id'], ),
        sa.ForeignKeyConstraint(['target_group_id'], ['groups.id'], ),
        sa.ForeignKeyConstraint(['task_id'], ['group_tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evaluation_assignments_evaluator_group_id'), 'evaluation_assignments', ['evaluator_group_id'], unique=False)
    op.create_index(op.f('ix_evaluation_assignments_target_group_id'), 'evaluation_assignments', ['target_group_id'], unique=False)
    op.create_index(op.f('ix_evaluation_assignments_task_id'), 'evaluation_assignments', ['task_id'], unique=False)

    # 7. group_evaluation_scores
    op.create_table(
        'group_evaluation_scores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('target_group_id', sa.Integer(), nullable=False),
        sa.Column('evaluator_type', sa.String(length=20), nullable=False),
        sa.Column('evaluator_id', sa.String(length=50), nullable=False),
        sa.Column('dimension_id', sa.Integer(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['dimension_id'], ['group_task_dimensions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_group_id'], ['groups.id'], ),
        sa.ForeignKeyConstraint(['task_id'], ['group_tasks.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('task_id', 'target_group_id', 'evaluator_type', 'evaluator_id', 'dimension_id', name='uix_evaluation_score'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_group_evaluation_scores_dimension_id'), 'group_evaluation_scores', ['dimension_id'], unique=False)
    op.create_index(op.f('ix_group_evaluation_scores_target_group_id'), 'group_evaluation_scores', ['target_group_id'], unique=False)
    op.create_index(op.f('ix_group_evaluation_scores_task_id'), 'group_evaluation_scores', ['task_id'], unique=False)

    # 8. group_dissolution_requests
    op.create_table(
        'group_dissolution_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_group_dissolution_requests_group_id'), 'group_dissolution_requests', ['group_id'], unique=False)

    # 9. class_group_settings
    op.create_table(
        'class_group_settings',
        sa.Column('class_name', sa.String(length=100), nullable=False),
        sa.Column('max_members_per_group', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('class_name')
    )


def downgrade() -> None:
    op.drop_table('class_group_settings')

    op.drop_index(op.f('ix_group_dissolution_requests_group_id'), table_name='group_dissolution_requests')
    op.drop_table('group_dissolution_requests')

    op.drop_index(op.f('ix_group_evaluation_scores_task_id'), table_name='group_evaluation_scores')
    op.drop_index(op.f('ix_group_evaluation_scores_target_group_id'), table_name='group_evaluation_scores')
    op.drop_index(op.f('ix_group_evaluation_scores_dimension_id'), table_name='group_evaluation_scores')
    op.drop_table('group_evaluation_scores')

    op.drop_index(op.f('ix_evaluation_assignments_task_id'), table_name='evaluation_assignments')
    op.drop_index(op.f('ix_evaluation_assignments_target_group_id'), table_name='evaluation_assignments')
    op.drop_index(op.f('ix_evaluation_assignments_evaluator_group_id'), table_name='evaluation_assignments')
    op.drop_table('evaluation_assignments')

    op.drop_index(op.f('ix_group_task_dimensions_task_id'), table_name='group_task_dimensions')
    op.drop_table('group_task_dimensions')

    op.drop_index(op.f('ix_group_tasks_class_name'), table_name='group_tasks')
    op.drop_table('group_tasks')

    op.drop_index(op.f('ix_group_membership_requests_student_id'), table_name='group_membership_requests')
    op.drop_index(op.f('ix_group_membership_requests_group_id'), table_name='group_membership_requests')
    op.drop_table('group_membership_requests')

    op.drop_index(op.f('ix_group_members_student_id'), table_name='group_members')
    op.drop_index(op.f('ix_group_members_group_id'), table_name='group_members')
    op.drop_table('group_members')

    op.drop_index(op.f('ix_groups_leader_student_id'), table_name='groups')
    op.drop_index(op.f('ix_groups_class_name'), table_name='groups')
    op.drop_table('groups')
