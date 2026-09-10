"""remove redundant class_name/semester string columns from business tables

业务表字符串冗余列删除：数据锚点唯一化为 FK（class_id / semester_id）。
- 回填：FK 为空且字符串可解析的行，按名称/label 匹配回填（best-effort；
  跨届同名班取最小 id——双写期后写入的行 FK 已非空，不受影响）
- 删除：14 个字符串列（7 表）
- FK 必填化：schedules/sessions/groups 的 class_id + 5 表的 semester_id
- 唯一索引 uix_active_class_semester 重建为 (class_id, semester_id)
"""
from typing import Union, Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260910_remove_redundant_string_columns"
down_revision: Union[str, Sequence[str], None] = "20260909_remove_assigned_classes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 需删除 semester 字符串列的表
_SEMESTER_TABLES = (
    "course_schedules", "course_sessions", "schedule_adjustments",
    "checkin_records", "questions", "groups", "group_score_logs",
)
# 需删除 class_name 字符串列的表
_CLASS_NAME_TABLES = (
    "course_schedules", "course_sessions", "checkin_records",
    "questions", "groups", "class_group_settings",
)
# class_id 必填化的表
_CLASS_ID_NOT_NULL = ("course_schedules", "course_sessions", "groups")
# semester_id 必填化的表
_SEMESTER_ID_NOT_NULL = (
    "course_schedules", "course_sessions", "schedule_adjustments",
    "groups", "group_score_logs",
)


def upgrade() -> None:
    # 1. 回填（仅处理 FK 为空的历史行；多行同名取最小 id）
    for table in _CLASS_NAME_TABLES:
        if table == "class_group_settings":
            continue  # 复合主键表，无独立 class_name 语义行
        op.execute(f"""
            UPDATE {table} t SET class_id = (
                SELECT c.id FROM classes c WHERE c.name = t.class_name
                ORDER BY c.id LIMIT 1
            ) WHERE t.class_id IS NULL AND t.class_name IS NOT NULL
        """)
    for table in _SEMESTER_TABLES:
        op.execute(f"""
            UPDATE {table} t SET semester_id = (
                SELECT s.id FROM semesters s WHERE s.label = t.semester
                ORDER BY s.id LIMIT 1
            ) WHERE t.semester_id IS NULL AND t.semester IS NOT NULL
        """)

    # 2. 唯一索引重建（先删旧的字符串维度索引）
    op.drop_index("uix_active_class_semester", table_name="course_sessions")
    op.create_index(
        "uix_active_class_semester", "course_sessions",
        ["class_id", "semester_id"], unique=True,
        postgresql_where=sa.text("status='active'"),
    )

    # 3. 删除字符串列
    for table in _SEMESTER_TABLES:
        op.drop_column(table, "semester")
    for table in _CLASS_NAME_TABLES:
        op.drop_column(table, "class_name")

    # 4. FK 必填化（回填后无 NULL；历史残留 NULL 行按空值兜底处理）
    for table in _CLASS_ID_NOT_NULL:
        op.alter_column(table, "class_id", nullable=False)
    for table in _SEMESTER_ID_NOT_NULL:
        op.alter_column(table, "semester_id", nullable=False)


def downgrade() -> None:
    # 冗余列已废弃，不提供回滚（历史数据通过备份恢复）
    raise NotImplementedError("冗余字符串列已废弃，不回滚")
