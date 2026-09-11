"""drop students.class_name 冗余快照列

class_id 唯一锚点化（Phase 6 Task 2）：班级展示名由 class_id 经 class_cache
运行时解析注入响应，students.class_name 冗余快照列失去存在意义。
生产库已验证 0 行依赖该列（class_id IS NULL AND class_name <> '未分班'），
删除无数据损失。

Revision ID: 20260911b_drop_students_class_name
Revises: 20260911_add_class_status
"""
from typing import Union, Sequence

from alembic import op

revision: str = "20260911b_drop_students_class_name"
down_revision: Union[str, Sequence[str], None] = "20260911_add_class_status"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index('idx_students_class_name', table_name='students')
    op.drop_column('students', 'class_name')


def downgrade() -> None:
    # 冗余快照列已废弃，不提供回滚（历史数据通过备份恢复）
    raise NotImplementedError("冗余快照列已废弃，不回滚")
