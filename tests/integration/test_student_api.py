"""
学生管理 API 集成测试
"""
import pytest


class TestStudentListAPI:
    """学生列表 API 测试"""
    
    def test_get_students_list_admin(self, admin_client, sample_students):
        """管理员获取学生列表"""
        response = admin_client.get("/api/students")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 6  # 包括三班学生
    
    def test_get_students_list_teacher(self, teacher_client, sample_students):
        """教师获取学生列表（只能看到负责班级的学生）"""
        response = teacher_client.get("/api/students")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # 教师负责"一班"和"二班"，共5个学生（一班3个，二班2个），看不到三班学生
        assert len(data["data"]) == 5
    
    def test_get_students_list_teacher_filter_by_class(self, teacher_client, sample_students):
        """教师按班级筛选学生（只能筛选负责班级）"""
        # 筛选一班（有权限）
        response = teacher_client.get("/api/students?class_name=一班")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 3
        
        # 筛选二班（有权限）
        response = teacher_client.get("/api/students?class_name=二班")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 2
    
    def test_get_students_unauthorized(self, client):
        """未授权访问学生列表"""
        response = client.get("/api/students")
        
        assert response.status_code == 401
    
    def test_get_students_by_class(self, admin_client, sample_students):
        """按班级筛选学生"""
        response = admin_client.get("/api/students?class_name=一班")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 3  # S001-S003
    
    def test_teacher_cannot_access_unassigned_class(self, teacher_client, sample_students):
        """教师无法查看未负责班级的学生"""
        response = teacher_client.get("/api/students?class_name=三班")
        
        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert "无权查看" in data["message"]


class TestStudentCreateAPI:
    """学生创建 API 测试"""
    
    def test_create_student_success(self, admin_client):
        """成功创建学生"""
        response = admin_client.post("/api/students", json={
            "student_id": "S100",
            "name": "新学生",
            "class_name": "三班"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "学生添加成功"
        assert data["data"]["student_id"] == "S100"
        assert data["data"]["class_name"] == "三班"
    
    def test_create_student_duplicate_id(self, admin_client, student_user):
        """学号重复"""
        response = admin_client.post("/api/students", json={
            "student_id": "S001",
            "name": "重复学生",
            "class_name": "一班"
        })
        
        assert response.status_code == 409
        assert "学号已存在" in response.json()["message"]
    
    def test_create_student_default_class(self, admin_client):
        """默认班级"""
        response = admin_client.post("/api/students", json={
            "student_id": "S101",
            "name": "无班级学生"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["class_name"] == "未分班"
    
    def test_create_student_validation_error(self, admin_client):
        """参数验证错误"""
        response = admin_client.post("/api/students", json={
            "student_id": "",
            "name": "无效学生"
        })
        
        assert response.status_code == 422


class TestStudentScoreAPI:
    """学生分数 API 测试"""
    
    def test_update_score_success(self, admin_client, student_user):
        """成功更新分数"""
        old_score = student_user.score
        
        response = admin_client.put(f"/api/students/{student_user.student_id}/score", json={
            "score_change": 5.0,
            "reason": "课堂表现优秀"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "分数更新成功"
        assert data["data"]["score"] == old_score + 5.0
    
    def test_update_score_negative(self, admin_client, student_user):
        """扣分"""
        old_score = student_user.score
        
        response = admin_client.put(f"/api/students/{student_user.student_id}/score", json={
            "score_change": -3.0,
            "reason": "迟到"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["score"] == old_score - 3.0
    
    def test_update_score_student_not_found(self, admin_client):
        """学生不存在"""
        response = admin_client.put("/api/students/NONEXISTENT/score", json={
            "score_change": 5.0,
            "reason": "测试"
        })
        
        assert response.status_code == 404
    
    def test_update_score_validation_error(self, admin_client, student_user):
        """参数验证错误"""
        response = admin_client.put(f"/api/students/{student_user.student_id}/score", json={
            "score_change": 5.0
            # 缺少 reason
        })
        
        assert response.status_code == 422
    
    def test_get_score_logs(self, admin_client, student_user):
        """获取分数历史"""
        # 先更新几次分数
        for i in range(3):
            admin_client.put(f"/api/students/{student_user.student_id}/score", json={
                "score_change": 1.0,
                "reason": f"测试原因{i}"
            })
        
        response = admin_client.get(f"/api/students/{student_user.student_id}/scores")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 3


class TestStudentDeleteAPI:
    """学生删除 API 测试"""
    
    def test_delete_student_success(self, admin_client, student_user):
        """成功删除学生"""
        response = admin_client.delete(f"/api/students/{student_user.student_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "学生删除成功"
        
        # 验证已删除
        get_response = admin_client.get(f"/api/students")
        students = get_response.json()["data"]
        assert not any(s["student_id"] == student_user.student_id for s in students)
    
    def test_delete_student_not_found(self, admin_client):
        """学生不存在"""
        response = admin_client.delete("/api/students/NONEXISTENT")
        
        assert response.status_code == 404
    
    def test_delete_student_teacher_forbidden(self, teacher_client, student_user):
        """教师无权删除学生"""
        response = teacher_client.delete(f"/api/students/{student_user.student_id}")
        
        assert response.status_code == 403


class TestClassAPI:
    """班级 API 测试"""
    
    def test_get_classes_list(self, admin_client, sample_students):
        """获取班级列表"""
        response = admin_client.get("/api/classes")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "一班" in data["data"]
        assert "二班" in data["data"]
    
    def test_get_classes_unauthorized(self, client):
        """未授权访问班级列表"""
        response = client.get("/api/classes")
        
        assert response.status_code == 401
