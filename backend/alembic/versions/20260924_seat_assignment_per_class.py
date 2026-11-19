"""seat assignment per class: seat_assignments 加 class_id 维度

座位归属从「学期 × 座位」收窄为「班级 × 学期 × 座位」——
同一教室被多个班共用时，各班有各自的座位表，互不霸占。
配合清空历史（老数据无班级维度，无法归属）→ 所有班从头重新选座。

Revision ID: 20260924_seat_assignment_per_class
Revises: 20260922_add_seat_system
"""
from typing import Union, Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260924_seat_assignment_per_class"
down_revision: Union[str, Sequence[str], None] = "20260922_add_seat_system"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(bind, table: str, column: str) -> bool:
    return bind.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
        "WHERE table_name=:t AND column_name=:c)"
    ), {"t": table, "c": column}).scalar()


def _constraint_exists(bind, table: str, name: str) -> bool:
    return bind.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.table_constraints "
        "WHERE table_name=:t AND constraint_name=:n)"
    ), {"t": table, "n": name}).scalar()


def upgrade() -> None:
    bind = op.get_bind()

    # 1. 加 class_id 列（可空：兼容，但清空历史后实际全有值）
    if not _column_exists(bind, "seat_assignments", "class_id"):
        op.add_column("seat_assignments",
                      sa.Column("class_id", sa.Integer(), nullable=True))
        op.create_foreign_key(
            "fk_seat_assignments_class_id_classes", "seat_assignments", "classes",
            ["class_id"], ["id"], ondelete="CASCADE",
        )
        op.create_index("ix_seat_assignments_class_id", "seat_assignments", ["class_id"])

    # 2. 清空历史分配：老数据没有班级维度，无法归属到任何班
    #    （用户确认：所有班从头重新选座，最干净）
    bind.execute(sa.text("DELETE FROM seat_assignments"))

    # 3. 唯一约束换维度：学期 → 班级 × 学期
    if _constraint_exists(bind, "seat_assignments", "uix_seat_semester"):
        op.drop_constraint("uix_seat_semester", "seat_assignments", type_="unique")
    if _constraint_exists(bind, "seat_assignments", "uix_student_semester_classroom"):
        op.drop_constraint("uix_student_semester_classroom", "seat_assignments",
                           type_="unique")

    if not _constraint_exists(bind, "seat_assignments", "uix_seat_class_semester"):
        op.create_unique_constraint(
            "uix_seat_class_semester", "seat_assignments",
            ["seat_id", "class_id", "semester_id"],
        )
    if not _constraint_exists(bind, "seat_assignments",
                              "uix_student_class_classroom_semester"):
        op.create_unique_constraint(
            "uix_student_class_classroom_semester", "seat_assignments",
            ["student_id", "class_id", "classroom_id", "semester_id"],
        )


def downgrade() -> None:
    raise NotImplementedError("座位分配维度变更不支持 downgrade（与 20260922 一致）")
