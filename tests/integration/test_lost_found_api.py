"""
失物招领 API 集成测试

覆盖范围：
- 教师端：发布、列表、详情、删除
- 学生端：列表、详情（匿名）、评论、认领、重复认领
- 隐私验证：学生端不暴露认领者信息，教师端显示真实姓名和联系方式
- 认领确认流程：创建 → 认领 → 确认 → 验证关闭
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from main import create_app
from app.core.db import get_session
from app.core.jwt import create_access_token
from app.models.user import User
from app.models.student import Student
from app.models.constants import UserRoleConst
from app.core.security import generate_password_hash


# ============== Fixtures ==============

@pytest.fixture
def session():
    """创建内存数据库会话"""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


@pytest.fixture
def app(session):
    """创建测试应用实例"""
    def override():
        yield session
    a = create_app()
    a.dependency_overrides[get_session] = override
    return a


@pytest.fixture
def client(app):
    """创建未认证的测试客户端"""
    return TestClient(app)


@pytest.fixture
def teacher_user(session):
    """创建教师用户"""
    password_hash, salt = generate_password_hash("teacher123")
    user = User(
        username="teacher1",
        name="李老师",
        password_hash=password_hash,
        salt=salt,
        role=UserRoleConst.TEACHER,
        assigned_classes='["测试班"]',
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def student_user(session):
    """创建学生用户"""
    password_hash, salt = generate_password_hash("student123")
    user = User(
        username="student1",
        name="张三",
        password_hash=password_hash,
        salt=salt,
        role=UserRoleConst.STUDENT,
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    student = Student(
        student_id=str(user.id),
        name="张三",
        class_name="测试班",
        password_hash=password_hash,
        salt=salt,
    )
    session.add(student)
    session.commit()
    session.refresh(student)
    return user


@pytest.fixture
def teacher_token(teacher_user):
    """教师 JWT Token"""
    return create_access_token({
        "sub": str(teacher_user.id),
        "username": teacher_user.username,
        "name": teacher_user.name,
        "role": UserRoleConst.TEACHER,
        "is_admin": False,
    })


@pytest.fixture
def student_token(student_user):
    """学生 JWT Token"""
    return create_access_token({
        "sub": str(student_user.id),
        "username": student_user.username,
        "name": student_user.name,
        "role": UserRoleConst.STUDENT,
        "is_admin": False,
    })


@pytest.fixture
def teacher_client(app, teacher_token):
    """已认证的教师客户端"""
    c = TestClient(app)
    c.cookies.set("access_token", teacher_token)
    return c


@pytest.fixture
def student_client(app, student_token):
    """已认证的学生客户端"""
    c = TestClient(app)
    c.cookies.set("access_token", student_token)
    return c


# ============== 辅助函数 ==============

def _create_item(client: TestClient, title="测试物品", description="一个测试物品", location="教室") -> int:
    """教师创建失物招领物品，返回 item_id"""
    resp = client.post("/api/v1/teacher/lost-found", data={
        "title": title,
        "description": description,
        "location": location,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    return data["data"]["item_id"]


# ============== 教师端测试 ==============

class TestTeacherAPI:
    """教师端失物招领 API 测试"""

    def test_create_item(self, teacher_client: TestClient):
        """教师发布失物招领"""
        item_id = _create_item(teacher_client, title="丢失钱包", description="黑色皮质钱包", location="图书馆")
        assert item_id is not None

        # 验证详情
        resp = teacher_client.get(f"/api/v1/teacher/lost-found/{item_id}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["title"] == "丢失钱包"
        assert data["description"] == "黑色皮质钱包"
        assert data["location"] == "图书馆"
        assert data["status"] == "open"

    def test_list_items(self, teacher_client: TestClient):
        """教师获取失物招领列表"""
        _create_item(teacher_client, title="物品A", description="描述A")
        _create_item(teacher_client, title="物品B", description="描述B")

        resp = teacher_client.get("/api/v1/teacher/lost-found")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["total"] == 2
        assert len(data["data"]["items"]) == 2

    def test_get_item_detail(self, teacher_client: TestClient):
        """教师获取物品详情（含认领记录）"""
        item_id = _create_item(teacher_client, title="详情测试", description="测试详情")

        resp = teacher_client.get(f"/api/v1/teacher/lost-found/{item_id}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == item_id
        assert data["title"] == "详情测试"
        assert "comments" in data
        assert "claims" in data

    def test_delete_item(self, teacher_client: TestClient):
        """教师删除失物招领"""
        item_id = _create_item(teacher_client, title="待删除", description="将被删除")

        resp = teacher_client.delete(f"/api/v1/teacher/lost-found/{item_id}")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        # 验证已删除
        resp = teacher_client.get(f"/api/v1/teacher/lost-found/{item_id}")
        assert resp.status_code == 404

    def test_student_cannot_access_teacher_api(self, student_client: TestClient):
        """学生无法访问教师端 API"""
        resp = student_client.get("/api/v1/teacher/lost-found")
        assert resp.status_code == 403


# ============== 学生端测试 ==============

class TestStudentAPI:
    """学生端失物招领 API 测试"""

    def test_list_items(self, teacher_client: TestClient, student_client: TestClient):
        """学生浏览失物招领列表"""
        _create_item(teacher_client, title="学生可见物品", description="学生应该能看到")

        resp = student_client.get("/api/v1/student/lost-found")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["total"] >= 1
        items = data["data"]["items"]
        assert any(item["title"] == "学生可见物品" for item in items)

    def test_get_item_detail_anonymous(self, teacher_client: TestClient, student_client: TestClient):
        """学生查看详情时评论显示匿名用户"""
        item_id = _create_item(teacher_client)

        # 先发表一条评论
        student_client.post(
            f"/api/v1/student/lost-found/{item_id}/comments",
            json={"content": "我看到了这个物品"},
        )

        # 学生查看详情
        resp = student_client.get(f"/api/v1/student/lost-found/{item_id}")
        assert resp.status_code == 200
        data = resp.json()["data"]

        # 评论应显示匿名用户
        assert len(data["comments"]) == 1
        assert data["comments"][0]["user_name"] == "匿名用户"
        assert data["comments"][0]["user_id"] == 0

    def test_create_comment(self, teacher_client: TestClient, student_client: TestClient):
        """学生发表评论"""
        item_id = _create_item(teacher_client)

        resp = student_client.post(
            f"/api/v1/student/lost-found/{item_id}/comments",
            json={"content": "这是我的评论"},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        assert "comment_id" in resp.json()["data"]

    def test_claim_item(self, teacher_client: TestClient, student_client: TestClient):
        """学生认领物品"""
        item_id = _create_item(teacher_client)

        resp = student_client.post(
            f"/api/v1/student/lost-found/{item_id}/claim",
            json={"contact": "13800138000", "message": "这是我的"},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        assert "claim_id" in resp.json()["data"]

    def test_duplicate_claim(self, teacher_client: TestClient, student_client: TestClient):
        """学生重复认领应返回 400"""
        item_id = _create_item(teacher_client)

        # 第一次认领
        resp = student_client.post(
            f"/api/v1/student/lost-found/{item_id}/claim",
            json={"contact": "13800138000", "message": "第一次"},
        )
        assert resp.status_code == 200

        # 第二次认领
        resp = student_client.post(
            f"/api/v1/student/lost-found/{item_id}/claim",
            json={"contact": "13800138000", "message": "第二次"},
        )
        assert resp.status_code == 400

    def test_privacy_student_sees_no_claim_info(self, teacher_client: TestClient, student_client: TestClient):
        """学生端不暴露认领者信息，只有 my_claim"""
        item_id = _create_item(teacher_client)

        # 学生认领
        student_client.post(
            f"/api/v1/student/lost-found/{item_id}/claim",
            json={"contact": "13800138000", "message": "认领说明"},
        )

        # 学生查看详情
        resp = student_client.get(f"/api/v1/student/lost-found/{item_id}")
        assert resp.status_code == 200
        data = resp.json()["data"]

        # 学生端不应有 claims 字段
        assert "claims" not in data
        # 应有 my_claim 字段
        assert "my_claim" in data
        assert data["my_claim"] is not None
        assert data["my_claim"]["status"] == "pending"

    def test_teacher_sees_claim_info(self, teacher_client: TestClient, student_client: TestClient):
        """教师端能看到认领者真实姓名和联系方式"""
        item_id = _create_item(teacher_client)

        # 学生认领
        student_client.post(
            f"/api/v1/student/lost-found/{item_id}/claim",
            json={"contact": "13800138000", "message": "认领说明"},
        )

        # 教师查看详情
        resp = teacher_client.get(f"/api/v1/teacher/lost-found/{item_id}")
        assert resp.status_code == 200
        data = resp.json()["data"]

        # 教师端应有 claims 字段
        assert "claims" in data
        assert len(data["claims"]) == 1
        claim = data["claims"][0]
        # 教师能看到真实姓名和联系方式
        assert claim["student_name"] is not None
        assert claim["contact"] == "13800138000"
        assert claim["message"] == "认领说明"
        assert claim["status"] == "pending"

    def test_confirm_claim_flow(self, teacher_client: TestClient, student_client: TestClient):
        """完整认领流程：创建 → 认领 → 确认 → 验证关闭"""
        # 1. 教师创建物品
        item_id = _create_item(teacher_client)
        resp = teacher_client.get(f"/api/v1/teacher/lost-found/{item_id}")
        assert resp.json()["data"]["status"] == "open"

        # 2. 学生认领
        resp = student_client.post(
            f"/api/v1/student/lost-found/{item_id}/claim",
            json={"contact": "13800138000", "message": "是我的"},
        )
        assert resp.status_code == 200
        claim_id = resp.json()["data"]["claim_id"]

        # 验证物品状态变为 claiming
        resp = teacher_client.get(f"/api/v1/teacher/lost-found/{item_id}")
        assert resp.json()["data"]["status"] == "claiming"

        # 3. 教师确认认领
        resp = teacher_client.put(f"/api/v1/teacher/lost-found/{item_id}/claims/{claim_id}/confirm")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        # 4. 验证物品已关闭
        resp = teacher_client.get(f"/api/v1/teacher/lost-found/{item_id}")
        assert resp.json()["data"]["status"] == "closed"

        # 验证认领状态为 confirmed
        claims = resp.json()["data"]["claims"]
        assert len(claims) == 1
        assert claims[0]["status"] == "confirmed"
