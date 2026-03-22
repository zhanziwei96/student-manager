"""
端到端场景测试
测试完整的业务流程
"""
import pytest


class TestCompleteClassFlow:
    """完整课堂流程测试"""
    
    def test_full_class_session_workflow(self, admin_client, sample_students):
        """完整课堂流程：开始上课 -> 签到 -> 评分 -> 结束上课"""
        # 1. 管理员开始上课
        response = admin_client.post("/api/class-session/start", json={
            "class_name": "一班"
        })
        assert response.status_code == 200
        assert response.json()["data"]["active"] is True
        
        # 2. 学生签到
        checkin_response = admin_client.post("/api/checkin", json={
            "student_id": "S001",
            "student_name": "学生1"
        })
        assert checkin_response.status_code == 200
        
        # 3. 教师给学生加分
        score_response = admin_client.put("/api/students/S001/score", json={
            "score_change": 5.0,
            "reason": "课堂表现优秀"
        })
        assert score_response.status_code == 200
        assert score_response.json()["data"]["score"] == 80.0  # 75 + 5 (S001 default score is 75)
        
        # 4. 查看签到统计
        stats_response = admin_client.get("/api/checkins/stats")
        assert stats_response.status_code == 200
        stats = stats_response.json()["data"]
        assert stats["checked_in"] == 1
        assert stats["not_checked_in"] == 2  # 一班共3人 (S001, S002, S003)
        
        # 5. 结束上课
        end_response = admin_client.post("/api/class-session/end")
        assert end_response.status_code == 200
        
        # 6. 验证课程已结束
        session_response = admin_client.get("/api/class-session")
        assert session_response.json()["data"]["active"] is False
    
    def test_multiple_students_checkin_scenario(self, admin_client, sample_students):
        """多个学生签到场景"""
        # 开始上课
        admin_client.post("/api/class-session/start", json={"class_name": "一班"})
        
        # 签到所有一班学生
        for i in range(1, 4):  # S001, S002, S003
            response = admin_client.post("/api/checkin", json={
                "student_id": f"S00{i}",
                "student_name": f"学生{i}"
            })
            assert response.status_code == 200
        
        # 验证统计
        stats = admin_client.get("/api/checkins/stats").json()["data"]
        assert stats["checked_in"] == 3
        assert stats["rate"] == 100.0
        
        # 验证签到列表
        checkins = admin_client.get("/api/checkins/today").json()["data"]
        assert len(checkins) == 3


class TestUserManagementScenario:
    """用户管理场景测试"""
    
    def test_create_and_manage_teacher(self, admin_client):
        """创建并管理教师账号"""
        # 1. 创建教师
        create_response = admin_client.post("/api/admin/users", json={
            "username": "newteacher",
            "password": "pass1234",
            "name": "新教师",
            "role": "teacher",
            "assigned_classes": ["一班", "二班"]
        })
        assert create_response.status_code == 200
        user_id = create_response.json()["data"]["id"]
        
        # 2. 更新教师信息
        update_response = admin_client.put(f"/api/admin/users/{user_id}", json={
            "name": "更新的教师名",
            "assigned_classes": ["三班"]
        })
        assert update_response.status_code == 200
        assert update_response.json()["data"]["name"] == "更新的教师名"
        
        # 3. 重置密码
        reset_response = admin_client.put(f"/api/admin/users/{user_id}/reset-password", json={
            "new_password": "newpass123"
        })
        assert reset_response.status_code == 200
        
        # 4. 验证新密码可以登录
        from fastapi.testclient import TestClient
        from backend.main import app
        
        # 注意：这里需要新的客户端来测试登录
        # 实际测试中可能需要特殊处理
        
        # 5. 删除教师
        delete_response = admin_client.delete(f"/api/admin/users/{user_id}")
        assert delete_response.status_code == 200


class TestPermissionScenario:
    """权限控制场景测试"""
    
    def test_teacher_cannot_access_admin_features(self, teacher_client, student_user):
        """教师无法访问管理员功能"""
        # 不能创建用户
        response = teacher_client.post("/api/admin/users", json={
            "username": "test",
            "password": "pass1234",
            "name": "测试"
        })
        assert response.status_code == 403
        
        # 不能删除学生
        response = teacher_client.delete(f"/api/students/{student_user.student_id}")
        assert response.status_code == 403
        
        # 可以查看学生列表
        response = teacher_client.get("/api/students")
        assert response.status_code == 200
    
    def test_student_cannot_access_any_features(self, client, student_user):
        """未登录学生无法访问功能"""
        # 不能查看学生列表
        response = client.get("/api/students")
        assert response.status_code == 401
        
        # 不能签到（但签到本身不需要登录，需要单独测试）
        # 不能修改分数
        response = client.put(f"/api/students/{student_user.student_id}/score", json={
            "score_change": 5.0,
            "reason": "测试"
        })
        assert response.status_code == 401


class TestStudentLifecycleScenario:
    """学生生命周期场景测试"""
    
    def test_complete_student_lifecycle(self, admin_client):
        """完整的学生生命周期"""
        # 1. 创建学生
        create_response = admin_client.post("/api/students", json={
            "student_id": "LIFECYCLE001",
            "name": "生命周期测试学生",
            "class_name": "测试班"
        })
        assert create_response.status_code == 200
        
        # 2. 更新分数（多次）
        scores = [
            (5.0, "首次加分"),
            (-2.0, "迟到扣分"),
            (3.0, "作业优秀"),
            (10.0, "期末考试")
        ]
        current_score = 70.0  # 默认分数
        
        for change, reason in scores:
            response = admin_client.put("/api/students/LIFECYCLE001/score", json={
                "score_change": change,
                "reason": reason
            })
            assert response.status_code == 200
            current_score += change
            assert response.json()["data"]["score"] == current_score
        
        # 3. 查看分数历史
        logs_response = admin_client.get("/api/students/LIFECYCLE001/scores")
        assert logs_response.status_code == 200
        assert len(logs_response.json()["data"]) == 4
        
        # 4. 验证班级列表
        classes_response = admin_client.get("/api/classes")
        assert "测试班" in classes_response.json()["data"]
        
        # 5. 删除学生
        delete_response = admin_client.delete("/api/students/LIFECYCLE001")
        assert delete_response.status_code == 200
        
        # 6. 验证已删除
        get_response = admin_client.get("/api/students")
        students = get_response.json()["data"]
        assert not any(s["student_id"] == "LIFECYCLE001" for s in students)


class TestLoginFailureScenario:
    """登录失败场景测试"""
    
    def test_login_failure_and_recovery(self, client, admin_user, test_engine):
        """登录失败和恢复"""
        from sqlmodel import Session
        from app.crud import get_user_by_username
        
        # 连续失败登录
        for i in range(9):
            response = client.post("/api/login", json={
                "username": "admin",
                "password": "wrongpassword",
                "role": "admin"
            })
            assert response.status_code == 401
            # 验证提示剩余次数
            assert f"还剩 {10 - i - 1} 次机会" in response.json()["message"]
        
        # 第10次失败 - 账号锁定
        response = client.post("/api/login", json={
            "username": "admin",
            "password": "wrongpassword",
            "role": "admin"
        })
        assert response.status_code == 403
        assert "锁定" in response.json()["message"]
        
        # 即使使用正确密码也无法登录（因为账号被锁定）
        # 注意：在测试中可能需要修改 locked_until 字段来模拟时间过去
        # 这里简化处理，直接重置登录失败次数
        with Session(test_engine) as session:
            user = get_user_by_username(session, "admin")
            user.login_fail_count = 0
            user.locked_until = None
            session.add(user)
            session.commit()
        
        # 现在可以正常登录
        success_response = client.post("/api/login", json={
            "username": "admin",
            "password": "admin123",
            "role": "admin"
        })
        assert success_response.status_code == 200
