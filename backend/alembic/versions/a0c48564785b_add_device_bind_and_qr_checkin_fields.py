"""add device_bind and qr checkin fields

Revision ID: a0c48564785b
Revises: e20c12c98147
Create Date: 2026-04-16 09:26:12.314488

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = 'a0c48564785b'
down_revision: Union[str, Sequence[str], None] = 'e20c12c98147'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    from sqlalchemy import inspect
    inspector = inspect(op.get_bind())

    # 1. 创建设备绑定表（幂等）
    if not inspector.has_table('device_binds'):
        op.create_table(
            'device_binds',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('session_id', sa.Integer(), nullable=False),
            sa.Column('student_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('device_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['session_id'], ['course_sessions.id']),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('session_id', 'student_id', name='unique_session_student_bind')
        )
        with op.batch_alter_table('device_binds', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_device_binds_device_id'), ['device_id'], unique=False)
            batch_op.create_index(batch_op.f('ix_device_binds_session_id'), ['session_id'], unique=False)
            batch_op.create_index(batch_op.f('ix_device_binds_student_id'), ['student_id'], unique=False)

    # 2. 为 checkin_records 添加二维码相关字段（幂等）
    existing_checkin_cols = {c['name'] for c in inspector.get_columns('checkin_records')}
    with op.batch_alter_table('checkin_records', schema=None) as batch_op:
        if 'qr_signature' not in existing_checkin_cols:
            batch_op.add_column(sa.Column('qr_signature', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
        if 'device_bound' not in existing_checkin_cols:
            batch_op.add_column(
                sa.Column('device_bound', sa.Boolean(), nullable=False, server_default=sa.text('true'))
            )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('checkin_records', schema=None) as batch_op:
        batch_op.drop_column('device_bound')
        batch_op.drop_column('qr_signature')

    with op.batch_alter_table('device_binds', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_device_binds_student_id'))
        batch_op.drop_index(batch_op.f('ix_device_binds_session_id'))
        batch_op.drop_index(batch_op.f('ix_device_binds_device_id'))

    op.drop_table('device_binds')
