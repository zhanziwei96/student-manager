"""失物招领评论/认领的操作者外键改指 students.student_id

`lost_found_comments.user_id` / `lost_found_claims.student_id` 原为 `int` + FK→`users.id`，
但学生的 JWT `sub` 是**学号**（`login.py`: `"sub": str(student.student_id)`）：

- 学号非纯数字（如 "S001"）→ 路由里 `int(user["sub"])` 抛 ValueError
- 学号是纯数字（如 "2025010101"）→ 无对应 users 行 → ForeignKeyViolation

两条路都是 500，所以这两张表在开发/生产库里都是 0 行（写入从未成功过）。

正确模型：失物招领**只有学生**能评论/认领（无任何教师评论端点），
故外键应指向 `students.student_id`、列类型 varchar
（与 `enrollments.student_id` / `student_class_semesters.student_id` 同构）。

改动：
- `lost_found_comments`: `user_id` → `student_id`（改名 + int→varchar + 换 FK），索引名同步规范化
- `lost_found_claims`: `student_id` int→varchar + 换 FK
- 无历史数据需回填（写入路径从未成功）

幂等：information_schema / pg_constraint 守卫，可重复执行。

Revision ID: 20260921_fix_lost_found_actor_fk
Revises: 20260916_add_visibility_classes
"""
from typing import Union, Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260921_fix_lost_found_actor_fk"
down_revision: Union[str, Sequence[str], None] = "20260916_add_visibility_classes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(bind, table: str, column: str) -> bool:
    return bool(bind.execute(sa.text("""
        SELECT count(*) FROM information_schema.columns
        WHERE table_name = :t AND column_name = :c
    """), {"t": table, "c": column}).scalar())


def _drop_fks_to(bind, table: str, column: str, ref_table: str) -> None:
    """删除该列上指向 ref_table 的外键（约束名不定，按目录查出后逐个删）"""
    names = bind.execute(sa.text("""
        SELECT con.conname
        FROM pg_constraint con
        JOIN pg_class rel  ON rel.oid  = con.conrelid
        JOIN pg_class frel ON frel.oid = con.confrelid
        JOIN pg_attribute att
          ON att.attrelid = con.conrelid AND att.attnum = ANY (con.conkey)
        WHERE con.contype = 'f'
          AND rel.relname = :t AND frel.relname = :r AND att.attname = :c
    """), {"t": table, "r": ref_table, "c": column}).scalars().all()
    for name in names:
        op.execute(f'ALTER TABLE {table} DROP CONSTRAINT IF EXISTS "{name}"')


def _has_fk_to_students(bind, table: str, column: str) -> bool:
    return bool(bind.execute(sa.text("""
        SELECT count(*)
        FROM pg_constraint con
        JOIN pg_class rel  ON rel.oid  = con.conrelid
        JOIN pg_class frel ON frel.oid = con.confrelid
        JOIN pg_attribute att
          ON att.attrelid = con.conrelid AND att.attnum = ANY (con.conkey)
        WHERE con.contype = 'f'
          AND rel.relname = :t AND frel.relname = 'students' AND att.attname = :c
    """), {"t": table, "c": column}).scalar())


def upgrade() -> None:
    bind = op.get_bind()

    # ── lost_found_comments: user_id → student_id ──
    if _column_exists(bind, 'lost_found_comments', 'user_id') \
            and not _column_exists(bind, 'lost_found_comments', 'student_id'):
        # 先摘掉指向 users 的外键，否则改名/改类型会被它挡住
        _drop_fks_to(bind, 'lost_found_comments', 'user_id', 'users')
        op.execute(
            "ALTER TABLE lost_found_comments RENAME COLUMN user_id TO student_id"
        )
        # 索引名不会跟着改名走，一并规范化到模型声明的名字
        op.execute(
            "ALTER INDEX IF EXISTS ix_lost_found_comments_user_id "
            "RENAME TO ix_lost_found_comments_student_id"
        )

    if _column_exists(bind, 'lost_found_comments', 'student_id'):
        _drop_fks_to(bind, 'lost_found_comments', 'student_id', 'users')
        op.execute(
            "ALTER TABLE lost_found_comments "
            "ALTER COLUMN student_id TYPE varchar USING student_id::varchar"
        )
        if not _has_fk_to_students(bind, 'lost_found_comments', 'student_id'):
            op.create_foreign_key(
                'lost_found_comments_student_id_fkey',
                'lost_found_comments', 'students', ['student_id'], ['student_id'],
            )

    # ── lost_found_claims: student_id int → varchar + 换 FK ──
    if _column_exists(bind, 'lost_found_claims', 'student_id'):
        _drop_fks_to(bind, 'lost_found_claims', 'student_id', 'users')
        op.execute(
            "ALTER TABLE lost_found_claims "
            "ALTER COLUMN student_id TYPE varchar USING student_id::varchar"
        )
        if not _has_fk_to_students(bind, 'lost_found_claims', 'student_id'):
            op.create_foreign_key(
                'lost_found_claims_student_id_fkey',
                'lost_found_claims', 'students', ['student_id'], ['student_id'],
            )


def downgrade() -> None:
    # 操作者标识语义已从 users.id 改为 students.student_id，回滚会指向错误的数据
    raise NotImplementedError("失物招领操作者外键已改指 students.student_id，不回滚")
