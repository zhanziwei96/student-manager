"""失物招领操作者外键迁移测试

对独立 PG 库（classhub_migration_test）验证 20260921_fix_lost_found_actor_fk：
1. 在迁移前插入「旧形态」数据（user_id int + FK→users），迁移后列改名、
   类型转 varchar、外键改指 students.student_id，且旧值不丢
2. 迁移可重复执行（幂等）
"""
import os

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

BACKEND_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'backend')
MIGRATION_TEST_URL = os.environ['DATABASE__URL'].replace(
    'classhub_test', 'classhub_migration_test')
# 本迁移的前一版
PRE_HEAD = '20260916_add_visibility_classes'
REVISION = '20260921_fix_lost_found_actor_fk'


@pytest.fixture(scope="module")
def migrated_db():
    """清空迁移库 → 跑到 PRE_HEAD → 插入旧形态数据 → 跑到 head → 再跑一次（幂等）"""
    engine = create_engine(MIGRATION_TEST_URL)
    with engine.begin() as conn:
        # 历史迁移的 downgrade 不完整，downgrade base 不可靠 → DROP SCHEMA
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))

    cfg = Config(os.path.join(BACKEND_DIR, 'alembic.ini'))

    def run_alembic(target: str) -> None:
        # 切换 alembic 目标库：get_settings 有双层缓存（lru_cache + 模块级 _settings），
        # 需 reload_settings() 重建实例 + cache_clear() 清 lru，两者缺一不可
        from app.core.config import get_settings, reload_settings

        old = os.environ.get('DATABASE__URL')
        os.environ['DATABASE__URL'] = MIGRATION_TEST_URL
        reload_settings()
        get_settings.cache_clear()
        try:
            command.upgrade(cfg, target)
        finally:
            if old is not None:
                os.environ['DATABASE__URL'] = old
            else:
                os.environ.pop('DATABASE__URL', None)
            reload_settings()
            get_settings.cache_clear()

    run_alembic(PRE_HEAD)

    # 旧形态数据：
    # - users.id = 1（发布物品的教师）
    # - students.student_id = '1'（学号恰好等于该 user id —— 这正是旧代码
    #   「碰巧能写成」的那种行；迁移后 FK 改指 students 仍能匹配，不丢数据）
    # - 一条评论（user_id=1）+ 一条认领（student_id=1），均指向 users(id=1)
    with engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO users (username, name, password_hash, role,"
            " is_account_enabled, login_fail_count, version, created_at)"
            " VALUES ('t1', '教师一', 'x', 'teacher', true, 0, 1, now())"
        ))
        conn.execute(text(
            "INSERT INTO students (student_id, name, is_account_enabled,"
            " version, status, created_at)"
            " VALUES ('1', '学生一', true, 1, 'active', now())"
        ))
        conn.execute(text(
            "INSERT INTO lost_found_items (title, description, status,"
            " publisher_id, created_at, updated_at)"
            " VALUES ('钱包', '描述', 'open', 1, now(), now())"
        ))
        conn.execute(text(
            "INSERT INTO lost_found_comments (item_id, user_id, content, created_at)"
            " VALUES (1, 1, '是我的', now())"
        ))
        conn.execute(text(
            "INSERT INTO lost_found_claims (item_id, student_id, contact, status, created_at)"
            " VALUES (1, 1, '13800000000', 'pending', now())"
        ))

    run_alembic('head')
    # 幂等：第二次跑不应抛异常
    run_alembic('head')

    yield engine
    engine.dispose()


def test_comments_column_renamed_and_retyped(migrated_db):
    """lost_found_comments.user_id → student_id，类型 varchar"""
    insp = inspect(migrated_db)
    cols = {c['name']: c for c in insp.get_columns('lost_found_comments')}
    assert 'student_id' in cols, "列未改名为 student_id"
    assert 'user_id' not in cols, "旧列 user_id 应已不存在"
    assert 'varchar' in str(cols['student_id']['type']).lower()


def test_claims_column_retyped(migrated_db):
    """lost_found_claims.student_id 类型 varchar"""
    insp = inspect(migrated_db)
    cols = {c['name']: c for c in insp.get_columns('lost_found_claims')}
    assert 'varchar' in str(cols['student_id']['type']).lower()


def test_comments_fk_points_to_students(migrated_db):
    """外键从 users.id 改指 students.student_id"""
    fks = inspect(migrated_db).get_foreign_keys('lost_found_comments')
    assert any(
        fk['constrained_columns'] == ['student_id']
        and fk['referred_table'] == 'students'
        and fk['referred_columns'] == ['student_id']
        for fk in fks
    ), f"外键未指向 students.student_id：{fks}"
    assert not any(
        fk['constrained_columns'] == ['student_id'] and fk['referred_table'] == 'users'
        for fk in fks
    ), "不应再有指向 users 的外键"


def test_claims_fk_points_to_students(migrated_db):
    fks = inspect(migrated_db).get_foreign_keys('lost_found_claims')
    assert any(
        fk['constrained_columns'] == ['student_id']
        and fk['referred_table'] == 'students'
        and fk['referred_columns'] == ['student_id']
        for fk in fks
    ), f"外键未指向 students.student_id：{fks}"


def test_existing_rows_preserved(migrated_db):
    """旧值转为学号字符串后仍能匹配 students（不丢数据）"""
    with migrated_db.begin() as conn:
        comment = conn.execute(text(
            "SELECT student_id, content FROM lost_found_comments"
        )).first()
        claim = conn.execute(text(
            "SELECT student_id, contact FROM lost_found_claims"
        )).first()

    assert comment is not None and comment[0] == '1' and comment[1] == '是我的'
    assert claim is not None and claim[0] == '1' and claim[1] == '13800000000'

    # 迁移后的外键真能约束住：写一个不存在的学号必须被拒
    import sqlalchemy.exc

    with pytest.raises(sqlalchemy.exc.IntegrityError):
        with migrated_db.begin() as conn:
            conn.execute(text(
                "INSERT INTO lost_found_comments (item_id, student_id, content, created_at)"
                " VALUES (1, 'NOT_A_STUDENT', 'x', now())"
            ))


def test_index_renamed(migrated_db):
    """索引名规范化到 ix_lost_found_comments_student_id"""
    with migrated_db.begin() as conn:
        names = {
            r[0] for r in conn.execute(text(
                "SELECT indexname FROM pg_indexes WHERE tablename='lost_found_comments'"
            )).all()
        }
    assert 'ix_lost_found_comments_student_id' in names, names
    assert 'ix_lost_found_comments_user_id' not in names, names
