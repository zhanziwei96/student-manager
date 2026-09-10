"""remove legacy score system

旧成绩体系（subjects/student_subject_scores/ScoreLog）已被 enrollments +
groups 取代：删除相关表与 students.score 综合分列。
"""
from typing import Union, Sequence

from alembic import op

revision: str = "20260909_remove_legacy_scores"
down_revision: Union[str, Sequence[str], None] = "20260909_remove_group_tasks_and_evaluations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("student_subject_score_logs")
    op.drop_table("student_subject_scores")
    op.drop_table("subjects")
    op.drop_table("score_logs")
    op.drop_column("students", "score")


def downgrade() -> None:
    # 旧成绩体系已停用，不提供回滚（历史数据通过备份恢复）
    raise NotImplementedError("旧成绩体系已废弃，不回滚")
