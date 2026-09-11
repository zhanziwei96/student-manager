"""add course_offering_classes 关联表，删除 course_offerings.class_scope

class_id 唯一锚点化（Phase 6 Task 3）：教学班面向范围由自由文本 class_scope
改为关联表（权限真源）。offering 无关联行 = 面向全部班级（通配，Phase 6 决策，
覆盖 "所有专业" 等无法匹配的历史值）。
- 建表：(offering_id, class_id) 复合主键，FK ondelete=CASCADE
- 回填（best-effort）：按逗号拆分 class_scope，去空白后按裸名唯一匹配 classes.name；
  无法匹配或匹配多行（跨届/跨专业同名）的 token 不插入，由通配语义覆盖
- uix_offering 重建为 (course_id, semester_id, teacher_id)
- 删除 class_scope 列

Revision ID: 20260911c_add_course_offering_classes
Revises: 20260911b_drop_students_class_name
"""
from typing import Union, Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260911c_add_course_offering_classes"
down_revision: Union[str, Sequence[str], None] = "20260911b_drop_students_class_name"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. 关联表：复合主键 + FK 级联删除
    op.create_table(
        'course_offering_classes',
        sa.Column('offering_id', sa.Integer(), nullable=False),
        sa.Column('class_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('offering_id', 'class_id'),
        sa.ForeignKeyConstraint(['offering_id'], ['course_offerings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['class_id'], ['classes.id'], ondelete='CASCADE'),
    )

    # 2. 回填（best-effort）：裸名唯一匹配才插入；regexp_split_to_table(NULL) 返回空集，天然跳过
    op.execute("""
        INSERT INTO course_offering_classes (offering_id, class_id)
        SELECT DISTINCT o.id, c.id
        FROM course_offerings o
        CROSS JOIN LATERAL regexp_split_to_table(o.class_scope, ',') AS token
        JOIN classes c ON c.name = btrim(token)
        WHERE (SELECT count(*) FROM classes c2 WHERE c2.name = btrim(token)) = 1
    """)

    # 3. 唯一约束重建：去掉 class_scope 维度
    op.drop_constraint('uix_offering', 'course_offerings', type_='unique')
    op.create_unique_constraint(
        'uix_offering', 'course_offerings',
        ['course_id', 'semester_id', 'teacher_id'],
    )

    # 4. 删除自由文本列
    op.drop_column('course_offerings', 'class_scope')


def downgrade() -> None:
    # 冗余文本列已废弃，不提供回滚（历史数据通过备份恢复）
    raise NotImplementedError("class_scope 自由文本已废弃，不回滚")
