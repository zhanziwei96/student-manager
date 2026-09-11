"""核心实体迁移测试

对独立 PG 库（classhub_migration_test）跑 Alembic 迁移链，
验证新表结构、students 新列与「导入年份即届」的回填逻辑。
"""
import os

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

BACKEND_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'backend')
MIGRATION_TEST_URL = os.environ['DATABASE__URL'].replace(
    'classhub_test', 'classhub_migration_test')
# 新迁移之前的 head：在此插入回填验证数据，再跑新迁移
PRE_HEAD = '20260907_add_group_subject_score'


@pytest.fixture(scope="module")
def migrated_db():
    """清空迁移库 → 跑到 PRE_HEAD → 插入回填验证学生 → 跑到 20260911c 之前
    → 插入 class_scope 回填验证数据 → 跑到 head"""
    engine = create_engine(MIGRATION_TEST_URL)
    # 清库用 DROP SCHEMA（历史迁移的 downgrade 不完整，downgrade base 不可靠）
    with engine.begin() as conn:
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
    with engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO students (student_id, name, class_name, score,"
            " is_account_enabled, version, created_at)"
            " VALUES ('MIG001', '迁移学生', '迁移测试班', 80.0, true, 1,"
            " '2025-09-01 08:00:00')"
        ))
    # 20260911c 回填验证：class_scope 列在 20260911c 才删除，须在其前插入
    # - '实验3班'：裸名唯一 → 链接
    # - '1班'：跨届/跨专业同名（2 行）→ 歧义不链接
    # - '所有专业'：无匹配 → 不链接（通配语义覆盖）
    run_alembic('20260911b_drop_students_class_name')
    with engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO cohorts (year, label) VALUES ('2096', '2096届'), ('2097', '2097届')"
        ))
        conn.execute(text(
            "INSERT INTO classes (name, major, cohort_year) VALUES"
            " ('1班', '计算机', '2096'), ('1班', '软件', '2097'), ('实验3班', '计算机', '2096')"
        ))
        conn.execute(text(
            "INSERT INTO courses (code, name, created_at)"
            " VALUES ('MIGC1', '迁移课程', '2026-09-01 08:00:00')"
        ))
        conn.execute(text(
            "INSERT INTO semesters (label, start_date, total_weeks)"
            " VALUES ('2096-2097-1', '2096-09-01', 20)"
        ))
        conn.execute(text(
            "INSERT INTO course_offerings (course_id, semester_id, teacher_id, class_scope, created_at)"
            " SELECT c.id, s.id, NULL, scope, '2026-09-01 08:00:00'"
            " FROM courses c, semesters s,"
            "      (VALUES ('实验3班'), ('1班'), ('所有专业')) AS v(scope)"
            " WHERE c.code = 'MIGC1' AND s.label = '2096-2097-1'"
        ))
    run_alembic('head')

    yield engine
    engine.dispose()


def test_core_entity_tables_exist(migrated_db):
    with migrated_db.connect() as conn:
        rows = conn.execute(text(
            "SELECT table_name FROM information_schema.tables"
            " WHERE table_schema = 'public' AND table_name IN"
            " ('semesters', 'cohorts', 'classes')"
        )).all()
    assert {r[0] for r in rows} == {'semesters', 'cohorts', 'classes'}


def test_students_new_columns_exist(migrated_db):
    with migrated_db.connect() as conn:
        rows = conn.execute(text(
            "SELECT column_name FROM information_schema.columns"
            " WHERE table_name = 'students' AND column_name IN"
            " ('class_id', 'cohort_year', 'status')"
        )).all()
    assert {r[0] for r in rows} == {'class_id', 'cohort_year', 'status'}


def test_partial_index_is_current_exists(migrated_db):
    with migrated_db.connect() as conn:
        indexdef = conn.execute(text(
            "SELECT indexdef FROM pg_indexes"
            " WHERE indexname = 'idx_semesters_is_current'"
        )).scalar()
    assert indexdef is not None
    assert 'WHERE' in indexdef  # 部分索引（方案 4.1）


def test_course_line_tables_exist(migrated_db):
    with migrated_db.connect() as conn:
        rows = conn.execute(text(
            "SELECT table_name FROM information_schema.tables"
            " WHERE table_schema = 'public' AND table_name IN"
            " ('courses', 'course_offerings', 'enrollments', 'student_class_semesters')"
        )).all()
    assert {r[0] for r in rows} == {
        'courses', 'course_offerings', 'enrollments', 'student_class_semesters'}


def test_enrollments_final_score_and_groups_course_id_columns(migrated_db):
    with migrated_db.connect() as conn:
        final_score = conn.execute(text(
            "SELECT data_type FROM information_schema.columns"
            " WHERE table_name = 'enrollments' AND column_name = 'final_score'"
        )).scalar()
        course_id = conn.execute(text(
            "SELECT data_type FROM information_schema.columns"
            " WHERE table_name = 'groups' AND column_name = 'course_id'"
        )).scalar()
    assert final_score == 'double precision'  # 期末成绩可空 float
    assert course_id == 'integer'  # 小组科目外键（过渡期可空）


def test_business_table_fk_columns_exist(migrated_db):
    """业务表 FK 列：5 张表含 class_id+semester_id，4 张表仅 semester_id"""
    class_tables = [
        'course_schedules', 'course_sessions', 'checkin_records', 'groups', 'questions',
    ]
    semester_tables = ['schedule_adjustments', 'group_score_logs', 'audit_logs']

    with migrated_db.connect() as conn:
        for t in class_tables:
            rows = conn.execute(text(
                "SELECT column_name FROM information_schema.columns"
                " WHERE table_name = :t AND column_name IN ('class_id', 'semester_id')"
            ), {"t": t}).all()
            assert {r[0] for r in rows} == {'class_id', 'semester_id'}, t
        for t in semester_tables:
            rows = conn.execute(text(
                "SELECT column_name FROM information_schema.columns"
                " WHERE table_name = :t AND column_name = 'semester_id'"
            ), {"t": t}).all()
            assert [r[0] for r in rows] == ['semester_id'], t


def test_class_group_settings_composite_pk(migrated_db):
    """class_group_settings 主键已切换为 (class_id, semester_id) 复合主键"""
    with migrated_db.connect() as conn:
        pk_cols = conn.execute(text(
            "SELECT a.attname FROM pg_index i"
            " JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)"
            " WHERE i.indrelid = 'class_group_settings'::regclass AND i.indisprimary"
        )).all()
    assert {r[0] for r in pk_cols} == {'class_id', 'semester_id'}


def test_backfill_course_offering_classes(migrated_db):
    """20260911c 回填：唯一裸名 token 链接；歧义（同名多行）/无匹配 token 不链接

    fixture 在 20260911c 之前插入 3 个教学班：class_scope 分别为
    '实验3班'（唯一）、'1班'（跨届/跨专业同名 2 行）、'所有专业'（无匹配，通配覆盖）。
    """
    with migrated_db.connect() as conn:
        offerings = conn.execute(text(
            "SELECT count(*) FROM course_offerings"
        )).scalar_one()
        links = conn.execute(text(
            "SELECT c.name, c.major, c.cohort_year FROM course_offering_classes oc"
            " JOIN classes c ON c.id = oc.class_id"
        )).all()
    assert offerings == 3  # 3 个教学班均保留
    assert [(r[0], r[1], r[2]) for r in links] == [('实验3班', '计算机', '2096')]


def test_backfill_cohort_class_student_by_import_year(migrated_db):
    """2025-09-01 导入的学生 → 届 2025 → 班级（迁移测试班, 2025）→ class_id 回填"""
    with migrated_db.connect() as conn:
        cohort = conn.execute(text(
            "SELECT label FROM cohorts WHERE year = '2025'"
        )).one()
        assert cohort[0] == '2025届'

        cls_id = conn.execute(text(
            "SELECT id FROM classes WHERE name = '迁移测试班' AND cohort_year = '2025'"
        )).scalar_one()

        student = conn.execute(text(
            "SELECT class_id, cohort_year, status FROM students"
            " WHERE student_id = 'MIG001'"
        )).one()
        assert student[0] == cls_id
        assert student[1] == '2025'
        assert student[2] == 'active'
