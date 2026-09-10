"""remove users.assigned_classes

教师授课关系唯一真源 = course_offerings.teacher_id，旧 JSON 班级列表删除。
"""
from typing import Union, Sequence

from alembic import op

revision: str = "20260909_remove_assigned_classes"
down_revision: Union[str, Sequence[str], None] = "20260909_remove_legacy_scores"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("users", "assigned_classes")


def downgrade() -> None:
    # 授课关系唯一真源已切换，不提供回滚
    raise NotImplementedError("assigned_classes 已废弃，不回滚")
