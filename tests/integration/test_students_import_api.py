"""学生批量导入 API 集成测试

覆盖：模板下载（xlsx 可解析、含填写说明）、Excel 导入成功（按「届+专业+班名」
三元组自动建届/建班）、学号重复跳过、缺少必需列 400、非管理员 403。

班级模型：Class_(name="1班", major="软件工程", cohort_year="2026")，
完整名由 display_name 拼成 "2026届软件工程1班"。
"""
from io import BytesIO

import pandas as pd
import pytest
from sqlmodel import Session, select

from app.models import Class_, Cohort, Student

pytestmark = pytest.mark.integration

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _xlsx_bytes(rows, columns=("学号", "姓名", "所属届", "专业", "班级名")) -> bytes:
    buf = BytesIO()
    pd.DataFrame(rows, columns=list(columns)).to_excel(buf, index=False)
    return buf.getvalue()


def _upload(client, content: bytes, filename: str = "students.xlsx"):
    return client.post(
        "/api/v1/students/import",
        files={"file": (filename, content, XLSX_MIME)},
    )


def _seed_class(test_engine, name: str, major: str, cohort_year: str) -> int:
    """直接落库一个班级行（模拟管理员已在 UI 建好班级），返回 class_id"""
    from app.core.class_cache import invalidate_class_cache

    with Session(test_engine) as session:
        cls = Class_(name=name, major=major, cohort_year=cohort_year)
        session.add(cls)
        session.commit()
        session.refresh(cls)
        class_id = cls.id
    invalidate_class_cache()
    return class_id


def test_download_import_template(admin_client):
    """模板可下载且能解析：首表为学生名单（含专业列），次表为填写说明"""
    resp = admin_client.get("/api/v1/students/import-template")

    assert resp.status_code == 200
    assert "spreadsheetml" in resp.headers["content-type"]
    assert "attachment" in resp.headers["content-disposition"]

    sheets = pd.read_excel(BytesIO(resp.content), sheet_name=None)
    assert list(sheets) == ["学生名单", "填写说明"]
    assert list(sheets["学生名单"].columns) == ["学号", "姓名", "所属届", "专业", "班级名"]
    assert len(sheets["学生名单"]) >= 1  # 含示例行
    assert sheets["学生名单"].iloc[0]["班级名"] == "1班"  # 只写班名，不带届/专业
    assert "学号" in list(sheets["填写说明"]["列名"])
    assert "专业" in list(sheets["填写说明"]["列名"])


def test_import_creates_class_with_major(admin_client, test_engine):
    """导入时按 届+专业+班名 建班：major 正确落库，不再产生 "2026届2026软件工程5班" 这类垃圾班"""
    content = _xlsx_bytes([
        ("2513010101", "张三", "2026", "软件工程", "5班"),
        ("2513010102", "李四", "2026", "软件工程", "5班"),
    ])

    resp = _upload(admin_client, content)

    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["imported"] == 2
    assert data["skipped"] == 0
    assert data["errors"] == []

    with Session(test_engine) as session:
        assert session.get(Cohort, "2026") is not None
        classes = session.exec(select(Class_)).all()
        assert len(classes) == 1  # 没有多出垃圾班级
        cls = classes[0]
        assert (cls.name, cls.major, cls.cohort_year) == ("5班", "软件工程", "2026")
        # 完整名由 届+专业+班名 拼成，届不重复、专业不丢失
        assert f"{cls.cohort_year}届{cls.major}{cls.name}" == "2026届软件工程5班"
        for sid in ("2513010101", "2513010102"):
            assert session.get(Student, sid).class_id == cls.id


def test_import_links_existing_class_by_triple(admin_client, test_engine):
    """班级已按 (届,专业,班名) 存在时，导入复用该班，不新建重复班级"""
    class_id = _seed_class(test_engine, name="5班", major="软件工程", cohort_year="2026")

    content = _xlsx_bytes([("2513010103", "王五", "2026", "软件工程", "5班")])

    resp = _upload(admin_client, content)

    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["imported"] == 1

    with Session(test_engine) as session:
        assert len(session.exec(select(Class_)).all()) == 1  # 未新建
        assert session.get(Student, "2513010103").class_id == class_id


def test_import_picks_correct_class_when_bare_name_duplicated(admin_client, test_engine):
    """同名不同专业：两个班都叫 "1班"（计算机 / 软件工程），
    导入「专业=软件工程」的学生必须挂到软件工程那个班（裸名解析会有歧义）"""
    cs_id = _seed_class(test_engine, name="1班", major="计算机", cohort_year="2026")
    se_id = _seed_class(test_engine, name="1班", major="软件工程", cohort_year="2026")
    assert cs_id != se_id

    content = _xlsx_bytes([("2513010104", "赵六", "2026", "软件工程", "1班")])

    resp = _upload(admin_client, content)

    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["imported"] == 1

    with Session(test_engine) as session:
        assert len(session.exec(select(Class_)).all()) == 2  # 未新建
        student = session.get(Student, "2513010104")
        assert student.class_id == se_id  # 挂到软件工程班，而非计算机班
        assert student.class_id != cs_id


def test_import_without_major_when_class_exists(admin_client, test_engine):
    """专业列留空：按 (name, "", cohort) 仍能命中已存在的无专业班级"""
    class_id = _seed_class(test_engine, name="1班", major="", cohort_year="2026")

    content = _xlsx_bytes([("2513010105", "孙七", "2026", "", "1班")])

    resp = _upload(admin_client, content)

    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["imported"] == 1

    with Session(test_engine) as session:
        assert len(session.exec(select(Class_)).all()) == 1  # 未新建
        assert session.get(Student, "2513010105").class_id == class_id


def test_import_missing_class_without_cohort_reports_error(admin_client, test_engine):
    """班级不存在且未填所属届 → 该行报错，其余行正常导入"""
    content = _xlsx_bytes([
        ("2513010106", "周八", "", "软件工程", "9班"),  # 无届，无法建班
        ("2513010107", "吴九", "2026", "软件工程", "9班"),
    ])

    resp = _upload(admin_client, content)

    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["imported"] == 1
    assert len(data["errors"]) == 1
    assert "第 2 行" in data["errors"][0]
    assert "未填写所属届" in data["errors"][0]

    with Session(test_engine) as session:
        assert session.get(Student, "2513010106") is None  # 失败行未落库
        assert session.get(Student, "2513010107") is not None


def test_import_students_skips_existing_id(admin_client, test_engine):
    """学号已存在 → 跳过并列出；既有学生数据不被修改；空班级记为未分班"""
    with Session(test_engine) as session:
        session.add(Student(student_id="S001", name="既有学生", class_name="旧班名"))
        session.commit()

    content = _xlsx_bytes([
        ("S001", "改名尝试", "2027", "护理", "1班"),
        ("S002", "新学生", "2027", "护理", "1班"),
        ("S003", "未分班学生", "", "", ""),
    ])

    resp = _upload(admin_client, content)

    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["imported"] == 2
    assert data["skipped"] == 1
    assert "S001" in data["skipped_rows"][0]
    assert data["errors"] == []

    with Session(test_engine) as session:
        assert session.get(Student, "S001").name == "既有学生"  # 未被覆盖
        assert session.get(Student, "S003").class_id is None  # 未分班
        cls = session.exec(select(Class_).where(Class_.name == "1班")).one()
        assert cls.major == "护理"


def test_import_normalizes_numeric_columns(admin_client, test_engine):
    """数字列（含空单元格 → pandas 推断 float64）不得出现 ".0" 尾巴"""
    content = _xlsx_bytes([
        ("2513010201", "数字学号甲", "2029", "检验", "1班"),
        ("2513010202", "数字学号乙", "", "", ""),  # 空值使该列被推断为 float64
    ])

    resp = _upload(admin_client, content)

    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["imported"] == 2

    with Session(test_engine) as session:
        assert session.get(Student, "2513010201") is not None  # 而非 "2513010201.0"
        cls = session.exec(
            select(Class_).where(Class_.name == "1班")).one()
        assert (cls.major, cls.cohort_year) == ("检验", "2029")
        assert session.get(Cohort, "2029") is not None  # 而非 "2029.0"
        assert session.exec(select(Cohort).where(Cohort.year.like("%.0"))).all() == []


def test_import_students_missing_required_column_returns_400(admin_client):
    """缺少必需列（姓名）→ 400 并提示使用模板"""
    content = _xlsx_bytes(
        [("S004", "2027", "护理", "1班")], columns=("学号", "所属届", "专业", "班级名"))

    resp = _upload(admin_client, content)

    assert resp.status_code == 400
    assert "缺少必需列" in resp.json()["message"]


def test_import_students_requires_admin(teacher_client):
    """教师无权导入 → 403"""
    content = _xlsx_bytes([("S005", "赵六", "2027", "护理", "1班")])

    resp = _upload(teacher_client, content)

    assert resp.status_code == 403
