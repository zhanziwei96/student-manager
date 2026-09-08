"""rekey class_group_settings: (class_name) → (class_id, semester_id)

主键切换（Phase 1 步骤 10，推迟至 CRUD 双写完成后执行）：
回填 → 删除无法回填的行 → 置 NOT NULL → 换复合主键。

Revision ID: 20260909_rekey_class_group_settings
Revises: 20260909_add_enrollment_score_logs
Create Date: 2026-09-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260909_rekey_class_group_settings'
down_revision: Union[str, Sequence[str], None] = '20260909_add_enrollment_score_logs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """回填 → 清理 → NOT NULL → 复合主键"""
    # 1. 回填：class_name → classes.name 匹配当前学年届；semester_id = 当前学期行
    op.execute("""
        UPDATE class_group_settings cgs
        SET class_id = c.id,
            semester_id = (SELECT id FROM semesters WHERE is_current = TRUE LIMIT 1)
        FROM classes c
        WHERE cgs.class_id IS NULL
          AND c.name = cgs.class_name
          AND c.cohort_year = EXTRACT(YEAR FROM now())::int::text
    """)
    # 2. 无法回填的行删除（默认设置，重建成本为零）
    op.execute("DELETE FROM class_group_settings WHERE class_id IS NULL OR semester_id IS NULL")
    # 3. 置 NOT NULL + 换复合主键
    op.alter_column('class_group_settings', 'class_id', nullable=False)
    op.alter_column('class_group_settings', 'semester_id', nullable=False)
    op.drop_constraint('class_group_settings_pkey', 'class_group_settings', type_='primary')
    op.create_primary_key(
        'pk_class_group_settings', 'class_group_settings', ['class_id', 'semester_id'],
    )


def downgrade() -> None:
    """回滚：恢复 class_name 主键，列回可空"""
    op.drop_constraint('pk_class_group_settings', 'class_group_settings', type_='primary')
    op.create_primary_key('class_group_settings_pkey', 'class_group_settings', ['class_name'])
    op.alter_column('class_group_settings', 'semester_id', nullable=True)
    op.alter_column('class_group_settings', 'class_id', nullable=True)
