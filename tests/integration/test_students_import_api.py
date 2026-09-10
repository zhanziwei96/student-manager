"""学生批量导入 API 集成测试

覆盖：模板下载（xlsx 可解析、含填写说明）、Excel 导入成功（自动建届/建班）、
学号重复跳过、缺少必需列 400、非管理员 403。
"""
from io import BytesIO

import pandas as pd
import pytest
from sqlmodel import Session, select

from app.models import Class_, Cohort, Student

pytestmark = pytest.mark.integration

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _xlsx_bytes(rows, columns=("学号", "姓名", "所属届", "班级名")) -> bytes:
    buf = BytesIO()
    pd.DataFrame(rows, columns=list(columns)).to_excel(buf, index=False)
    return buf.getvalue()


def _upload(client, content: bytes, filename: str = "students.xlsx"):
    return client.post(
        "/api/v1/students/import",
        files={"file": (filename, content, XLSX_MIME)},
    )


def test_download_import_template(admin_client):
    """模板可下载且能解析：首表为学生名单，含表头与示例行；次表为填写说明"""
    resp = admin_client.get("/api/v1/students/import-template")

    assert resp.status_code == 200
    assert "spreadsheetml" in resp.headers["content-type"]
    assert "attachment" in resp.headers["content-disposition"]

    sheets = pd.read_excel(BytesIO(resp.content), sheet_name=None)
    assert list(sheets) == ["学生名单", "填写说明"]
    assert list(sheets["学生名单"].columns) == ["学号", "姓名", "所属届", "班级名"]
    assert len(sheets["学生名单"]) >= 1  # 含示例行
    assert "学号" in list(sheets["填写说明"]["列名"])


def test_import_students_auto_creates_class_and_cohort(admin_client, test_engine):
    """导入两名学生：班级与届不存在时自动创建，学生带 FK 锚点落库"""
    content = _xlsx_bytes([
        ("2513010101", "张三", "2027", "2027护理1班"),
        ("2513010102", "李四", "2027", "2027护理1班"),
    ])

    resp = _upload(admin_client, content)

    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["imported"] == 2
    assert data["skipped"] == 0
    assert data["errors"] == []

    with Session(test_engine) as session:
        assert session.get(Cohort, "2027") is not None
        cls = session.exec(select(Class_).where(Class_.name == "2027护理1班")).one()
        s1 = session.get(Student, "2513010101")
        assert s1.class_name == "2027护理1班"
        assert s1.class_id == cls.id


def test_import_students_skips_existing_id(admin_client, test_engine):
    """学号已存在 → 跳过并列出；既有学生数据不被修改；空班级记为未分班"""
    with Session(test_engine) as session:
        session.add(Student(student_id="S001", name="既有学生", class_name="旧班名"))
        session.commit()

    content = _xlsx_bytes([
        ("S001", "改名尝试", "2027", "2027护理1班"),
        ("S002", "新学生", "2027", "2027护理1班"),
        ("S003", "未分班学生", "", ""),
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


def test_import_normalizes_numeric_columns(admin_client, test_engine):
    """数字列（含空单元格 → pandas 推断 float64）不得出现 ".0" 尾巴"""
    content = _xlsx_bytes([
        ("2513010201", "数字学号甲", "2029", "2029检验1班"),
        ("2513010202", "数字学号乙", "", ""),  # 空值使该列被推断为 float64
    ])

    resp = _upload(admin_client, content)

    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["imported"] == 2

    with Session(test_engine) as session:
        assert session.get(Student, "2513010201") is not None  # 而非 "2513010201.0"
        assert session.exec(
            select(Class_).where(Class_.name == "2029检验1班")).one()
        assert session.get(Cohort, "2029") is not None  # 而非 "2029.0"
        assert session.exec(select(Cohort).where(Cohort.year.like("%.0"))).all() == []


def test_import_students_missing_required_column_returns_400(admin_client):
    """缺少必需列（姓名）→ 400 并提示使用模板"""
    content = _xlsx_bytes([("S004", "2027", "2027护理1班")], columns=("学号", "所属届", "班级名"))

    resp = _upload(admin_client, content)

    assert resp.status_code == 400
    assert "缺少必需列" in resp.json()["message"]


def test_import_students_requires_admin(teacher_client):
    """教师无权导入 → 403"""
    content = _xlsx_bytes([("S005", "赵六", "2027", "2027护理1班")])

    resp = _upload(teacher_client, content)

    assert resp.status_code == 403
