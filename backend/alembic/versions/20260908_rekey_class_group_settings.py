"""rekey class_group_settings: (class_name) → (class_id, semester_id)

班级小组设置主键改造（方案 Phase 1 步骤 10）：
原主键为 class_name 字符串，改为 (class_id, semester_id) 复合主键，
class_name 保留为冗余快照列。

Revision ID: 20260908_rekey_class_group_settings
Revises: 20260908_add_business_table_fks
Create Date: 2026-09-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260908_rekey_class_group_settings'
down_revision: Union[str, Sequence[str], None] = '20260908_add_business_table_fks'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """主键 (class_name) → (class_id, semester_id)，class_name 转为冗余快照"""
    op.add_column('class_group_settings', sa.Column('class_id', sa.Integer(), nullable=True))
    op.add_column('class_group_settings', sa.Column('semester_id', sa.Integer(), nullable=True))
    op.drop_constraint('class_group_settings_pkey', 'class_group_settings', type_='primary')
    op.create_primary_key(
        'pk_class_group_settings', 'class_group_settings', ['class_id', 'semester_id'],
    )
    op.create_foreign_key(
        'fk_class_group_settings_class_id_classes', 'class_group_settings', 'classes',
        ['class_id'], ['id'],
    )
    op.create_foreign_key(
        'fk_class_group_settings_semester_id_semesters', 'class_group_settings', 'semesters',
        ['semester_id'], ['id'],
    )


def downgrade() -> None:
    """回滚：恢复 class_name 主键，删除新列"""
    op.drop_constraint(
        'fk_class_group_settings_semester_id_semesters', 'class_group_settings',
        type_='foreignkey',
    )
    op.drop_constraint(
        'fk_class_group_settings_class_id_classes', 'class_group_settings',
        type_='foreignkey',
    )
    op.drop_constraint('pk_class_group_settings', 'class_group_settings', type_='primary')
    op.create_primary_key('class_group_settings_pkey', 'class_group_settings', ['class_name'])
    op.drop_column('class_group_settings', 'semester_id')
    op.drop_column('class_group_settings', 'class_id')
