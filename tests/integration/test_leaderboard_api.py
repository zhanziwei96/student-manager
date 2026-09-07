# tests/integration/test_leaderboard_api.py
import pytest
from sqlmodel import Session
from app.models import Student


@pytest.fixture
def leaderboard_students(client, test_engine):
    """创建排行榜测试学生数据"""
    from app.core.security import hash_password
    with Session(test_engine) as session:
        students = []
        test_data = [
            ("S101", "张三", "一班", 95.0),
            ("S102", "李四", "一班", 88.0),
            ("S103", "王五", "一班", 88.0),  # 并列排名测试
            ("S104", "赵六", "一班", 75.0),
            ("S105", "孙七", "二班", 92.0),
            ("S106", "周八", "二班", 85.0),
        ]
        for student_id, name, class_name, score in test_data:
            password_hash = hash_password(student_id)  # 学号作为默认密码
            student = Student(
                student_id=student_id,
                name=name,
                class_name=class_name,
                score=score,
                password_hash=password_hash
            )
            session.add(student)
            students.append(student)
        session.commit()
        for student in students:
            session.refresh(student)
        return students


class TestLeaderboardAPI:
    """排行榜 API 集成测试"""

    def test_get_class_leaderboard(self, client, test_engine, leaderboard_students):
        """测试获取班级排行榜"""
        # 先登录（密码是学号）
        client.post("/api/v1/login", json={
            "username": "S101",
            "password": "S101",
            "role": "student"
        })

        response = client.get("/api/v1/students/leaderboard?scope=class&class_name=一班")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["scope"] == "class"
        assert len(data["data"]["students"]) > 0
        assert "my_rank" in data["data"]

    def test_get_school_leaderboard(self, client, test_engine, leaderboard_students):
        """测试获取全校排行榜"""
        client.post("/api/v1/login", json={
            "username": "S101",
            "password": "S101",
            "role": "student"
        })

        response = client.get("/api/v1/students/leaderboard?scope=school")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["scope"] == "school"

    def test_leaderboard_ranking_order(self, client, test_engine, leaderboard_students):
        """测试排行榜按分数降序排列"""
        client.post("/api/v1/login", json={
            "username": "S101",
            "password": "S101",
            "role": "student"
        })

        response = client.get("/api/v1/students/leaderboard?scope=school")
        data = response.json()

        students = data["data"]["students"]
        scores = [s["score"] for s in students]

        # 验证分数降序
        assert scores == sorted(scores, reverse=True)

    def test_leaderboard_parallel_ranking(self, client, test_engine, leaderboard_students):
        """测试并列排名（相同分数同一名次）"""
        client.post("/api/v1/login", json={
            "username": "S101",
            "password": "S101",
            "role": "student"
        })

        response = client.get("/api/v1/students/leaderboard?scope=class&class_name=一班")
        data = response.json()

        students = data["data"]["students"]
        # 张三 95分(第1名), 李四和王五 88分(并列第2名), 赵六 75分(第4名)
        ranks = {s["student_id"]: s["rank"] for s in students}

        assert ranks["S101"] == 1  # 张三
        assert ranks["S102"] == 2  # 李四
        assert ranks["S103"] == 2  # 王五（并列）
        assert ranks["S104"] == 4  # 赵六（跳过了第3名）

    def test_leaderboard_limit_parameter(self, client, test_engine, leaderboard_students):
        """测试 limit 参数限制返回数量"""
        client.post("/api/v1/login", json={
            "username": "S101",
            "password": "S101",
            "role": "student"
        })

        response = client.get("/api/v1/students/leaderboard?limit=3")
        data = response.json()

        assert len(data["data"]["students"]) <= 3

    def test_leaderboard_unauthorized(self, client):
        """测试未登录无法访问排行榜"""
        response = client.get("/api/v1/students/leaderboard")
        assert response.status_code == 401


@pytest.fixture
def session(test_engine):
    """绑定集成测试共享引擎的会话（API 客户端与测试读写同一数据库）"""
    with Session(test_engine) as s:
        yield s


def test_leaderboard_by_subject_and_teacher(student_client, session):
    """按教师+科目聚合排行榜"""
    from app.models import Subject, StudentSubjectScore, Student, User
    from app.core.security import hash_password

    # 造数据：student_client 已创建学生 S001，再补 1 个学生 + 2 个教师 + 1 个科目
    student2 = Student(
        student_id="S002", name="学生2", class_name="1班", score=80.0,
        password_hash=hash_password("pass"), is_account_enabled=True
    )
    teacher1 = User(username="t_math_1", name="张老师", password_hash=hash_password("pass"), role="teacher")
    teacher2 = User(username="t_math_2", name="李老师", password_hash=hash_password("pass"), role="teacher")
    subject = Subject(name="数学", semester="2026-2027-1")
    session.add_all([student2, teacher1, teacher2, subject])
    session.commit()

    # 同一科目，不同老师
    score1 = StudentSubjectScore(student_id="S001", subject_id=subject.id, teacher_id=teacher1.id, score=85.0, semester="2026-2027-1")
    score2 = StudentSubjectScore(student_id="S002", subject_id=subject.id, teacher_id=teacher2.id, score=90.0, semester="2026-2027-1")
    session.add_all([score1, score2])
    session.commit()

    # 按教师+科目排
    resp = student_client.get(f"/api/v1/students/leaderboard?subject_id={subject.id}&teacher_id={teacher1.id}")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data["students"]) == 1
    assert data["students"][0]["student_id"] == "S001"
    assert data["students"][0]["score"] == 85.0
