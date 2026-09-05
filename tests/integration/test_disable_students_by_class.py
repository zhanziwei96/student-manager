"""
按班级批量禁用学生账号集成测试（学期归档）

覆盖：
- admin 可禁用任意班级
- 教师可禁用自己负责的班级
- 教师不能禁用其他班级（403）
- 学生无权调用（403）
- 缺少班级名称返回 400
- 禁用后学生无法登录，且班级从班级列表消失
"""
from sqlmodel import Session


def _create_students(test_engine, class_name: str, count: int, id_prefix: str = "SA"):
    """批量创建测试学生（默认账号启用）"""
    from app.models import Student

    with Session(test_engine) as session:
        for i in range(1, count + 1):
            session.add(Student(
                student_id=f"{id_prefix}{i:03d}",
                name=f"学生{i}",
                class_name=class_name,
                score=60.0,
            ))
        session.commit()


class TestDisableStudentsByClass:
    """按班级批量禁用学生账号"""

    def test_admin_can_disable_students_by_class(self, admin_client, test_engine):
        """admin 可按班级批量禁用学生，且班级从列表消失"""
        from app.crud import get_all_classes, get_students_by_class

        _create_students(test_engine, "旧班级", 3)

        resp = admin_client.post(
            "/api/v1/students/disable-by-class",
            json={"class_name": "旧班级"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["disabled_count"] == 3
        assert data["data"]["class_name"] == "旧班级"

        with Session(test_engine) as session:
            students = get_students_by_class(session, "旧班级")
            assert len(students) == 3
            assert all(s.is_account_enabled is False for s in students)
            # 班级列表不再返回该班级
            assert "旧班级" not in get_all_classes(session)

        # 重复禁用返回 0（幂等，不产生错误）
        resp = admin_client.post(
            "/api/v1/students/disable-by-class",
            json={"class_name": "旧班级"}
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["disabled_count"] == 0

    def test_teacher_can_disable_own_class(self, teacher_client, test_engine):
        """教师可禁用自己负责的班级（一班）"""
        from app.crud import get_students_by_class

        _create_students(test_engine, "一班", 2)

        resp = teacher_client.post(
            "/api/v1/students/disable-by-class",
            json={"class_name": "一班"}
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["disabled_count"] == 2

        with Session(test_engine) as session:
            students = get_students_by_class(session, "一班")
            assert all(s.is_account_enabled is False for s in students)

    def test_teacher_cannot_disable_other_class(self, teacher_client, test_engine):
        """教师不能禁用未分配的班级（三班）→ 403，数据不变"""
        from app.crud import get_students_by_class

        _create_students(test_engine, "三班", 2)

        resp = teacher_client.post(
            "/api/v1/students/disable-by-class",
            json={"class_name": "三班"}
        )
        assert resp.status_code == 403

        with Session(test_engine) as session:
            students = get_students_by_class(session, "三班")
            assert all(s.is_account_enabled is True for s in students)

    def test_student_cannot_disable_by_class(self, student_client):
        """学生无权调用 → 403"""
        resp = student_client.post(
            "/api/v1/students/disable-by-class",
            json={"class_name": "一班"}
        )
        assert resp.status_code == 403

    def test_missing_class_name_returns_400(self, admin_client):
        """缺少班级名称 → 400"""
        resp = admin_client.post("/api/v1/students/disable-by-class", json={})
        assert resp.status_code == 400

    def test_disabled_student_cannot_login(self, admin_client, test_engine):
        """禁用后学生无法登录，历史数据保留"""
        from app.core.security import generate_password_hash
        from app.models import Student

        with Session(test_engine) as session:
            password_hash, salt = generate_password_hash("student123")
            session.add(Student(
                student_id="SB001",
                name="旧班学生",
                class_name="旧班级",
                score=60.0,
                password_hash=password_hash,
                salt=salt,
            ))
            session.commit()

        resp = admin_client.post(
            "/api/v1/students/disable-by-class",
            json={"class_name": "旧班级"}
        )
        assert resp.status_code == 200

        login_resp = admin_client.post("/api/v1/login", json={
            "username": "SB001",
            "password": "student123",
            "role": "student"
        })
        assert login_resp.status_code == 403

        # 历史数据保留：学生记录仍在
        from app.crud import get_student
        with Session(test_engine) as session:
            assert get_student(session, "SB001") is not None
