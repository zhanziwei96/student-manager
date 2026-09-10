"""审计日志 API 集成测试：学期过滤（ADM-13）+ admin 权限"""
from datetime import date

from sqlmodel import select

from app.models import AuditLog, Semester


def _seed_audit_logs(session):
    """造两条审计日志：一条带学期、一条无学期"""
    session.add(Semester(label="2026-2027-1", start_date=date(2026, 9, 7),
                         total_weeks=20, is_current=True))
    session.commit()
    sem = session.exec(select(Semester)).one()
    session.add(AuditLog(user_id=1, user_name="admin", role="admin",
                         action="测试操作", semester_id=sem.id))
    session.add(AuditLog(user_id=1, user_name="admin", role="admin",
                         action="无学期操作", semester_id=None))
    session.commit()
    return sem


def test_audit_logs_filtered_by_semester(admin_client, session):
    """按学期过滤审计日志（ADM-13）"""
    sem = _seed_audit_logs(session)

    resp = admin_client.get(f"/api/v1/audit-logs?semester_id={sem.id}")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["action"] == "测试操作"
    assert data[0]["semester_id"] == sem.id


def test_audit_logs_without_filter_returns_all(admin_client, session):
    """不传学期返回全部"""
    _seed_audit_logs(session)

    resp = admin_client.get("/api/v1/audit-logs")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 2


def test_audit_logs_require_admin(teacher_client, student_client):
    """非管理员 403"""
    for client in (teacher_client, student_client):
        resp = client.get("/api/v1/audit-logs")
        assert resp.status_code == 403, client
