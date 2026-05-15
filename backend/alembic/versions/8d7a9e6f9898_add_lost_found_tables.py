"""add lost found tables

Revision ID: 8d7a9e6f9898
Revises: a0c48564785b
Create Date: 2026-05-15 15:56:30.230631

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8d7a9e6f9898'
down_revision: Union[str, Sequence[str], None] = 'a0c48564785b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 创建失物招领物品表
    op.create_table('lost_found_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('location', sa.String(length=200), nullable=True),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='open'),
        sa.Column('publisher_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['publisher_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('lost_found_items', schema=None) as batch_op:
        batch_op.create_index('ix_lost_found_items_publisher_id', ['publisher_id'], unique=False)

    # 创建失物招领评论表
    op.create_table('lost_found_comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['item_id'], ['lost_found_items.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('lost_found_comments', schema=None) as batch_op:
        batch_op.create_index('ix_lost_found_comments_item_id', ['item_id'], unique=False)
        batch_op.create_index('ix_lost_found_comments_user_id', ['user_id'], unique=False)

    # 创建失物招领认领记录表
    op.create_table('lost_found_claims',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('contact', sa.String(length=200), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['item_id'], ['lost_found_items.id'], ),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('lost_found_claims', schema=None) as batch_op:
        batch_op.create_index('ix_lost_found_claims_item_id', ['item_id'], unique=False)
        batch_op.create_index('ix_lost_found_claims_student_id', ['student_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('lost_found_claims', schema=None) as batch_op:
        batch_op.drop_index('ix_lost_found_claims_student_id')
        batch_op.drop_index('ix_lost_found_claims_item_id')

    op.drop_table('lost_found_claims')

    with op.batch_alter_table('lost_found_comments', schema=None) as batch_op:
        batch_op.drop_index('ix_lost_found_comments_user_id')
        batch_op.drop_index('ix_lost_found_comments_item_id')

    op.drop_table('lost_found_comments')

    with op.batch_alter_table('lost_found_items', schema=None) as batch_op:
        batch_op.drop_index('ix_lost_found_items_publisher_id')

    op.drop_table('lost_found_items')
