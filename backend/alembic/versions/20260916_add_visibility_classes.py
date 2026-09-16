"""add question_classes / lost_found_classes 可见班级关联表，删除 questions.class_id

问答/失物招领班级可见范围关联表（class-visibility Task 1）：可见范围由
questions.class_id 单班级字段改为关联表（权限真源）。无关联行 = 所有班级可见
（通配语义，与 course_offering_classes 一致）。
- 建表：(question_id, class_id) / (item_id, class_id) 复合主键，FK ondelete=CASCADE
- 回填：questions.class_id 非空行 → question_classes
- 失物招领无历史单班级字段，无需回填（新建即通配）
- 删除 questions.class_id 列（硬切换）

Revision ID: 20260916_add_visibility_classes
Revises: 20260911c_add_course_offering_classes
"""
from typing import Union, Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260916_add_visibility_classes"
down_revision: Union[str, Sequence[str], None] = "20260911c_add_course_offering_classes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. 关联表：复合主键 + FK 级联删除。
    # 幂等保护：兼容手工建过同构表的库（同 20260911c 的 to_regclass 守卫模式）
    bind = op.get_bind()

    for table, fk1_col, fk1_ref, fk2_col, fk2_ref in (
        ('question_classes', 'question_id', 'questions', 'class_id', 'classes'),
        ('lost_found_classes', 'item_id', 'lost_found_items', 'class_id', 'classes'),
    ):
        table_exists = bind.execute(sa.text(
            f"SELECT to_regclass('public.{table}') IS NOT NULL"
        )).scalar()

        if not table_exists:
            op.create_table(
                table,
                sa.Column(fk1_col, sa.Integer(), nullable=False),
                sa.Column(fk2_col, sa.Integer(), nullable=False),
                sa.PrimaryKeyConstraint(fk1_col, fk2_col),
                sa.ForeignKeyConstraint([fk1_col], [f'{fk1_ref}.id'], ondelete='CASCADE'),
                sa.ForeignKeyConstraint([fk2_col], [f'{fk2_ref}.id'], ondelete='CASCADE'),
            )
        else:
            # 表已存在：确保 FK 带 CASCADE（手工建表时可能未带）
            for fk, col, ref in (
                (f'{table}_{fk1_col}_fkey', fk1_col, fk1_ref),
                (f'{table}_{fk2_col}_fkey', fk2_col, fk2_ref),
            ):
                op.execute(f"""
                    ALTER TABLE {table}
                    DROP CONSTRAINT IF EXISTS {fk},
                    ADD CONSTRAINT {fk} FOREIGN KEY ({col}) REFERENCES {ref}(id) ON DELETE CASCADE
                """)

    # 2. 回填：questions.class_id 非空 → question_classes（ON CONFLICT 保护幂等重跑）
    op.execute("""
        INSERT INTO question_classes (question_id, class_id)
        SELECT id, class_id FROM questions WHERE class_id IS NOT NULL
        ON CONFLICT (question_id, class_id) DO NOTHING
    """)

    # 3. 删除单班级列（守卫：已删过的库重跑不报错）
    col_exists = bind.execute(sa.text("""
        SELECT count(*) FROM information_schema.columns
        WHERE table_name='questions' AND column_name='class_id'
    """)).scalar()
    if col_exists:
        op.drop_column('questions', 'class_id')


def downgrade() -> None:
    # 单班级字段已废弃，不提供回滚（历史数据通过备份恢复）
    raise NotImplementedError("questions.class_id 单班级字段已废弃，不回滚")
