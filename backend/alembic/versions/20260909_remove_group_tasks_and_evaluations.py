"""remove group tasks/evaluations and subject_id columns

任务/互评流程已停用（需求表 ❌）：删除 group_tasks/group_task_dimensions/
evaluation_assignments/group_evaluation_scores 四张表；
小组科目维度从 subjects（旧科目表）迁移到 courses：删除 groups 与
group_score_logs 的 subject_id 列。
"""
from typing import Union, Sequence

from alembic import op

revision: str = "20260909_remove_group_tasks_and_evaluations"
down_revision: Union[str, Sequence[str], None] = "20260909_rekey_class_group_settings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("group_evaluation_scores")
    op.drop_table("evaluation_assignments")
    op.drop_table("group_task_dimensions")
    op.drop_table("group_tasks")
    op.drop_column("group_score_logs", "subject_id")
    op.drop_column("groups", "subject_id")


def downgrade() -> None:
    # 任务/互评功能已停用，不提供回滚（历史数据通过备份恢复）
    raise NotImplementedError("group_tasks 已废弃，不回滚")
