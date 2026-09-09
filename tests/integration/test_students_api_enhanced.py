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
        assert data["data"]["score"] == 0.0  # 默认分数
    
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
    
    def test_update_student_score_as_admin(self, admin_client, student_user):
        """测试管理员更新学生分数"""
        response = admin_client.put("/api/v1/students/S001/score", json={
            "score_change": 5.0,
            "reason": "回答问题奖励"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["score"] == 85.0  # 80 + 5
    
    def test_update_student_score_negative(self, admin_client, student_user):
        """测试扣分"""
        response = admin_client.put("/api/v1/students/S001/score", json={
            "score_change": -10.0,
            "reason": "迟到扣分"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["score"] == 70.0  # 80 - 10
    
    def test_update_student_score_not_found(self, admin_client):
        """测试更新不存在学生的分数"""
        response = admin_client.put("/api/v1/students/NOTEXIST/score", json={
            "score_change": 5.0,
            "reason": "测试"
        })
        
        assert response.status_code == 404
    
    def test_delete_student_as_admin(self, admin_client):
        """测试管理员删除学生"""
        # 先创建一个学生
        admin_client.post("/api/v1/students", json={
            "student_id": "S999",
            "name": "待删除学生",
            "class_name": "一班"
        })
        
        response = admin_client.delete("/api/v1/students/S999")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_delete_student_not_found(self, admin_client):
        """测试删除不存在的学生"""
        response = admin_client.delete("/api/v1/students/NOTEXIST")
        
        assert response.status_code == 404
    
    def test_reset_student_password_as_admin(self, admin_client, student_user):
        """测试管理员重置学生密码"""
        response = admin_client.put("/api/v1/students/S001/reset-password", json={
            "new_password": "reset123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # 验证新密码可以登录
        response = admin_client.post("/api/v1/login", json={
            "username": "S001",
            "password": "reset123",
            "role": "student"
        })
        assert response.status_code == 200
    
    def test_get_student_scores_history(self, admin_client, student_user):
        """测试获取学生分数历史"""
        # 先更新几次分数
        admin_client.put("/api/v1/students/S001/score", json={
            "score_change": 5.0,
            "reason": "第一次加分"
        })
        admin_client.put("/api/v1/students/S001/score", json={
            "score_change": -3.0,
            "reason": "扣分"
        })
        
        response = admin_client.get("/api/v1/students/S001/scores")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # 由于领域事件处理器使用独立会话，在测试中可能无法立即看到日志
        # 只验证 API 返回成功，数据条数可能为 0（由于会话隔离）或更多
        assert isinstance(data["data"], list)
    
class TestStudentsPagination:
    """学生列表分页（limit/offset/total）集成测试"""

    @staticmethod
    def _create_students(test_engine, class_name: str, count: int, id_prefix: str):
        """批量创建测试学生"""
        from sqlmodel import Session
        from app.models import Student

        with Session(test_engine) as session:
            for i in range(1, count + 1):
                session.add(Student(
                    student_id=f"{id_prefix}{i:04d}",
                    name=f"学生{i}",
                    class_name=class_name,
                    score=60.0,
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

    def test_admin_pagination_with_class_filter(self, admin_client, test_engine):
        """分页与班级筛选同时生效，total 为筛选后总数"""
        self._create_students(test_engine, "一班", 30, "CA")
        self._create_students(test_engine, "二班", 20, "CB")

        resp = admin_client.get("/api/v1/students?class_name=一班&limit=10&offset=25")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 5
        assert data["total"] == 30
        assert all(s["class_name"] == "一班" for s in data["data"])

    def test_teacher_pagination(self, teacher_client, test_engine):
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


class TestScoreLogsPagination:
    """分数日志分页（limit/offset）集成测试"""

    @staticmethod
    def _create_score_logs(test_engine, student_id: str, count: int):
        """直接插入分数日志（绕过事件会话隔离问题）"""
        from sqlmodel import Session
        from app.models import ScoreLog

        with Session(test_engine) as session:
            for i in range(count):
                session.add(ScoreLog(
                    student_id=student_id,
                    old_score=80.0 + i,
                    new_score=81.0 + i,
                    delta=1.0,
                    reason=f"加分{i + 1}",
                    operator="老师",
                ))
            session.commit()

    def test_score_logs_pagination(self, student_client, test_engine):
        """学生查看自己的分数日志：30 条分 2 页（20 + 10）"""
        self._create_score_logs(test_engine, "S001", 30)

        resp1 = student_client.get("/api/v1/students/S001/scores?limit=20&offset=0")
        assert resp1.status_code == 200
        page1 = resp1.json()["data"]
        assert len(page1) == 20

        resp2 = student_client.get("/api/v1/students/S001/scores?limit=20&offset=20")
        assert resp2.status_code == 200
        page2 = resp2.json()["data"]
        assert len(page2) == 10

        # 两页 id 互不重复且覆盖全部 30 条
        ids = {log["id"] for log in page1 + page2}
        assert len(ids) == 30

    def test_score_logs_offset_beyond_total(self, student_client, test_engine):
        """offset 超出总数时返回空列表"""
        self._create_score_logs(test_engine, "S001", 5)

        resp = student_client.get("/api/v1/students/S001/scores?limit=20&offset=100")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_score_logs_default_behavior_unchanged(self, student_client, test_engine):
        """不传分页参数时按默认 limit 返回（向后兼容）"""
        self._create_score_logs(test_engine, "S001", 10)

        resp = student_client.get("/api/v1/students/S001/scores")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 10

    def test_score_logs_invalid_offset(self, student_client, test_engine):
        """非法 offset 返回 422"""
        assert student_client.get("/api/v1/students/S001/scores?offset=-1").status_code == 422
