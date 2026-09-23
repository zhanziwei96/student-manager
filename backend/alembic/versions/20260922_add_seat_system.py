"""add seat system: classrooms / seats / seat_assignments / seat_session_overrides + checkin_records.seat_id

Revision ID: 20260922_add_seat_system
Revises: 20260921_fix_lost_found_actor_fk
"""
from typing import Union, Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260922_add_seat_system"
down_revision: Union[str, Sequence[str], None] = "20260921_fix_lost_found_actor_fk"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(bind, table: str) -> bool:
    return bind.execute(
        sa.text("SELECT to_regclass(:t) IS NOT NULL"), {"t": f"public.{table}"}
    ).scalar()


def upgrade() -> None:
    bind = op.get_bind()

    if not _table_exists(bind, "classrooms"):
        op.create_table(
            "classrooms",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(50), nullable=False),
            sa.Column("rows", sa.Integer(), nullable=False),
            sa.Column("cols", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="active"),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
            sa.UniqueConstraint("name", name="uq_classrooms_name"),
        )

    if not _table_exists(bind, "seats"):
        op.create_table(
            "seats",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("classroom_id", sa.Integer(), nullable=False),
            sa.Column("seat_no", sa.String(10), nullable=False),
            sa.Column("row", sa.Integer(), nullable=False),
            sa.Column("col", sa.Integer(), nullable=False),
            sa.Column("is_broken", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.ForeignKeyConstraint(["classroom_id"], ["classrooms.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("classroom_id", "seat_no", name="uix_seat_no_per_classroom"),
            sa.UniqueConstraint("classroom_id", "row", "col", name="uix_seat_pos_per_classroom"),
        )
        op.create_index("ix_seats_classroom_id", "seats", ["classroom_id"])

    if not _table_exists(bind, "seat_assignments"):
        op.create_table(
            "seat_assignments",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("seat_id", sa.Integer(), nullable=False),
            sa.Column("student_id", sa.String(20), nullable=False),
            sa.Column("classroom_id", sa.Integer(), nullable=False),  # 冗余：唯一约束需要
            sa.Column("semester_id", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["seat_id"], ["seats.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["student_id"], ["students.student_id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["classroom_id"], ["classrooms.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["semester_id"], ["semesters.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("seat_id", "semester_id", name="uix_seat_semester"),
            sa.UniqueConstraint(
                "student_id", "semester_id", "classroom_id",
                name="uix_student_semester_classroom",
            ),
        )
        op.create_index("ix_seat_assignments_student", "seat_assignments",
                        ["student_id", "semester_id"])

    if not _table_exists(bind, "seat_session_overrides"):
        op.create_table(
            "seat_session_overrides",
            sa.Column("session_id", sa.Integer(), nullable=False),
            sa.Column("student_id", sa.String(20), nullable=False),
            sa.Column("seat_id", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["session_id"], ["course_sessions.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["student_id"], ["students.student_id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["seat_id"], ["seats.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("session_id", "student_id"),
            sa.UniqueConstraint("session_id", "seat_id", name="uix_override_session_seat"),
        )

    # checkin_records.seat_id（可空：旧数据/无座位图课堂）
    col_exists = bind.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
        "WHERE table_name='checkin_records' AND column_name='seat_id')"
    )).scalar()
    if not col_exists:
        op.add_column("checkin_records", sa.Column("seat_id", sa.Integer(), nullable=True))
        op.create_foreign_key(
            "fk_checkin_records_seat_id", "checkin_records", "seats",
            ["seat_id"], ["id"], ondelete="SET NULL",
        )

    # 并发兜底：同一课堂同一座位最多一条签到占用；同一课堂同一座位最多一条调座
    idx_exists = bind.execute(sa.text(
        "SELECT to_regclass('public.uix_checkin_session_seat') IS NOT NULL"
    )).scalar()
    if not idx_exists:
        op.create_index(
            "uix_checkin_session_seat", "checkin_records", ["session_id", "seat_id"],
            unique=True,
            postgresql_where=sa.text("seat_id IS NOT NULL"),
        )

    # 中间态兜底：seat_session_overrides 已存在但约束缺失（旧版迁移建过表）则补上
    constraint_exists = bind.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.table_constraints "
        "WHERE table_name='seat_session_overrides' "
        "AND constraint_name='uix_override_session_seat')"
    )).scalar()
    if not constraint_exists:
        op.create_unique_constraint(
            "uix_override_session_seat", "seat_session_overrides",
            ["session_id", "seat_id"],
        )


def downgrade() -> None:
    raise NotImplementedError("座位系统迁移不支持 downgrade（与 20260916 一致）")
