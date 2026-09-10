"""
学生管理 API 集成测试 - 增强版（提升覆盖率）
"""
import pytest
from fastapi.testclient import TestClient


class TestStudentsAPIEnhanced:
    """学生管理 API 增强测试"""
    
    def test_get_students_list_as_admin(self, admin_client, sample_students):
        """测试管理员获取所有学生列表"""
        response = admin_client.get("/api/v1/students")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 6  # sample_students 创建了6个学生
    
    def test_get_students_list_as_teacher(self, teacher_client, sample_students):
        """测试教师获取负责班级的学生列表"""
        response = teacher_client.get("/api/v1/students")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # 教师只能看到一班和二班的学生
        assert len(data["data"]) == 5  # 3个一班 + 2个二班
    
    def test_get_students_by_class_as_admin(self, admin_client, sample_students):
        """测试管理员按班级筛选学生"""
        response = admin_client.get("/api/v1/students?class_name=一班")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 3
    
    def test_get_students_by_class_as_teacher_authorized(self, teacher_client, sample_students):
        """测试教师获取有权限的班级学生"""
        response = teacher_client.get("/api/v1/students?class_name=一班")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 3
    
    def test_get_students_by_class_as_teacher_unauthorized(self, teacher_client, sample_students):
        """测试教师获取无权限的班级学生"""
        response = teacher_client.get("/api/v1/students?class_name=三班")
        
        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
    
    def test_get_student_info(self, admin_client, student_user):
        """测试获取单个学生信息"""
        response = admin_client.get("/api/v1/students/S001")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["student_id"] == "S001"
        assert data["data"]["name"] == "学生1"
    
    def test_get_student_info_not_found(self, admin_client):
        """测试获取不存在的学生"""
        response = admin_client.get("/api/v1/students/NOTEXIST")
        
        assert response.status_code == 404
    
    def test_create_student_as_admin(self, admin_client):
        """测试管理员创建学生"""
        response = admin_client.post("/api/v1/students", json={
            "student_id": "S100",
            "name": "新学生",
            "class_name": "一班"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["student_id"] == "S100"
        assert data["data"]["status"] == "active"
    
    def test_create_student_duplicate_id(self, admin_client, student_user):
        """测试创建重复学号的学生"""
        response = admin_client.post("/api/v1/students", json={
            "student_id": "S001",  # 已存在
            "name": "重复学生",
            "class_name": "一班"
        })
        
        assert response.status_code == 409
        data = response.json()
        assert data["success"] is False
        assert "已存在" in data["message"]
    
    
class TestStudentsPagination:
    """学生列表分页（limit/offset/total）集成测试"""

    @staticmethod
    def _create_students(test_engine, class_name: str, count: int, id_prefix: str):
        """批量创建测试学生（class_id 按班级名解析，未登记班级名则为 None）"""
        from sqlmodel import Session
        from app.models import Student
        from app.core.class_cache import get_class_id_by_name

        with Session(test_engine) as session:
            class_id = get_class_id_by_name(session, class_name)
            for i in range(1, count + 1):
                session.add(Student(
                    student_id=f"{id_prefix}{i:04d}",
                    name=f"学生{i}",
                    class_name=class_name,
                    class_id=class_id,
                ))
            session.commit()

    def test_admin_pagination_pages(self, admin_client, test_engine):
        """管理员分页：150 个学生分 3 页，第 4 页为空"""
        self._create_students(test_engine, "分页班", 150, "PG")

        ids = []
        for offset, expected in ((0, 50), (50, 50), (100, 50), (150, 0)):
            resp = admin_client.get(f"/api/v1/students?limit=50&offset={offset}")
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True
            assert len(data["data"]) == expected
            assert data["total"] == 150
            ids.extend(s["student_id"] for s in data["data"])

        # 各页不重复且覆盖全部
        assert len(set(ids)) == 150

    def test_admin_pagination_with_class_filter(self, admin_client, test_engine, seed_refs):
        """分页与班级筛选同时生效，total 为筛选后总数（班级按 FK 过滤）"""
        self._create_students(test_engine, "一班", 30, "CA")
        self._create_students(test_engine, "二班", 20, "CB")

        resp = admin_client.get("/api/v1/students?class_name=一班&limit=10&offset=25")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 5
        assert data["total"] == 30
        assert all(s["class_name"] == "一班" for s in data["data"])

    def test_teacher_pagination(self, teacher_client, test_engine, seed_refs):
        """教师分页：只看负责班级，total 为负责班级总数"""
        self._create_students(test_engine, "一班", 30, "TA")
        self._create_students(test_engine, "三班", 10, "TB")  # 教师不负责三班

        resp = teacher_client.get("/api/v1/students?limit=20&offset=0")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 20
        # 教师负责一班和二班，只有一班有 30 个学生
        assert data["total"] == 30
        assert all(s["class_name"] in ("一班", "二班") for s in data["data"])

    def test_no_limit_returns_all_without_total(self, admin_client, test_engine):
        """不传 limit 时返回全部且不带 total（向后兼容）"""
        self._create_students(test_engine, "分页班", 60, "NL")

        resp = admin_client.get("/api/v1/students")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 60
        assert data["total"] is None

    def test_pagination_invalid_params(self, admin_client, test_engine):
        """非法分页参数返回 422"""
        assert admin_client.get("/api/v1/students?limit=0").status_code == 422
        assert admin_client.get("/api/v1/students?limit=201").status_code == 422
        assert admin_client.get("/api/v1/students?offset=-1").status_code == 422
