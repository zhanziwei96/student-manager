"""add class_id/semester_id to class_group_settings (PK switch deferred)

班级小组设置加 FK 列（方案 Phase 1 步骤 10 前半）：
class_name 主键保留，仅加 class_id/semester_id 可空列 + FK + 索引。
主键切换 (class_name) → (class_id, semester_id) 推迟到 Phase 2 CRUD 适配时执行
（主键非空要求所有创建路径先有 FK 值，需与 CRUD 双写同步改造）。

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
    """加 class_id/semester_id 可空列 + FK + 索引（class_name 主键保留）"""
    op.add_column('class_group_settings', sa.Column('class_id', sa.Integer(), nullable=True))
    op.add_column('class_group_settings', sa.Column('semester_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_class_group_settings_class_id_classes', 'class_group_settings', 'classes',
        ['class_id'], ['id'],
    )
    op.create_foreign_key(
        'fk_class_group_settings_semester_id_semesters', 'class_group_settings', 'semesters',
        ['semester_id'], ['id'],
    )
    op.create_index(
        'idx_class_group_settings_class_id', 'class_group_settings', ['class_id'], unique=False,
    )
    op.create_index(
        'idx_class_group_settings_semester_id', 'class_group_settings', ['semester_id'], unique=False,
    )


def downgrade() -> None:
    """回滚：删除新列"""
    op.drop_index('idx_class_group_settings_semester_id', table_name='class_group_settings')
    op.drop_index('idx_class_group_settings_class_id', table_name='class_group_settings')
    op.drop_constraint(
        'fk_class_group_settings_semester_id_semesters', 'class_group_settings',
        type_='foreignkey',
    )
    op.drop_constraint(
        'fk_class_group_settings_class_id_classes', 'class_group_settings',
        type_='foreignkey',
    )
    op.drop_column('class_group_settings', 'semester_id')
    op.drop_column('class_group_settings', 'class_id')
