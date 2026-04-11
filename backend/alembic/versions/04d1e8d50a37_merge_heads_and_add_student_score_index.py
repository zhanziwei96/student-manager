"""merge heads and add student score index

Revision ID: 04d1e8d50a37
Revises: 2026_04_11_add_group_collaboration_tables, fcfbc4da810e
Create Date: 2026-04-12 01:08:21.686238

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '04d1e8d50a37'
down_revision: Union[str, Sequence[str], None] = ('2026_04_11_add_group_collaboration_tables', 'fcfbc4da810e')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 补充 models/student.py 中声明但迁移中遗漏的 score 降序索引
    with op.batch_alter_table('students', schema=None) as batch_op:
        batch_op.create_index(
            'idx_students_score',
            [sa.text('score DESC')],
            unique=False,
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('students', schema=None) as batch_op:
        batch_op.drop_index('idx_students_score')
