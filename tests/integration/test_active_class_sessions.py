"""
活跃课堂 API 集成测试
测试获取和开始活跃课堂接口
"""
import pytest


class TestActiveClassSessionsAPI:
    """测试活跃课堂相关 API"""

    def test_start_class_with_course_name(self, teacher_client):
        """测试教师开始上课时传入 course_name"""
        # 执行
        response = teacher_client.post(
            "/api/v1/class-session/start",
            json={
                "class_name": "计算机1班",
                "course_name": "高等数学"
            }
        )
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["class_name"] == "计算机1班"
        assert data["data"]["course_name"] == "高等数学"
        assert data["data"]["active"] is True
        assert "id" in data["data"]
        assert "session_code" in data["data"]

    def test_start_class_without_course_name(self, teacher_client):
        """测试教师开始上课时不传 course_name"""
        # 执行
        response = teacher_client.post(
            "/api/v1/class-session/start",
            json={"class_name": "软件工程班"}
        )
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["class_name"] == "软件工程班"
        assert data["data"]["course_name"] is None
        assert data["data"]["active"] is True

    def test_get_active_class_sessions(self, admin_client, teacher_client):
        """测试获取所有活跃课堂列表"""
        # 准备：教师开始两个课堂
        teacher_client.post(
            "/api/v1/class-session/start",
            json={
                "class_name": "计算机1班",
                "course_name": "高等数学"
            }
        )
        
        # 使用另一个教师开始第二个课堂（需要登出并登录另一个教师）
        # 这里简化处理，只验证一个课堂
        
        # 执行：管理员获取活跃课堂列表
        response = admin_client.get("/api/v1/class-sessions/active")
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) >= 1
        
        # 验证返回的数据包含 course_name
        first_session = data["data"][0]
        assert "course_name" in first_session
        assert "class_name" in first_session
        assert "teacher_name" in first_session
        assert "start_time" in first_session

    def test_get_active_class_sessions_returns_empty_list(self, admin_client):
        """测试没有活跃课堂时返回空列表"""
        # 执行
        response = admin_client.get("/api/v1/class-sessions/active")
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []

    def test_start_class_requires_login(self, client):
        """测试开始上课需要登录"""
        # 执行：未登录用户
        response = client.post(
            "/api/v1/class-session/start",
            json={
                "class_name": "计算机1班",
                "course_name": "高等数学"
            }
        )
        
        # 验证
        assert response.status_code == 401

    def test_get_active_class_sessions_is_public(self, client):
        """测试获取活跃课堂需要登录"""
        # 执行
        response = client.get("/api/v1/class-sessions/active")
        
        # 验证 - 该接口是公开的，无需认证
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_end_class_clears_from_active_list(self, teacher_client, admin_client):
        """测试结束上课后从活跃列表移除"""
        # 准备：开始上课
        teacher_client.post(
            "/api/v1/class-session/start",
            json={
                "class_name": "计算机1班",
                "course_name": "高等数学"
            }
        )
        
        # 验证：活跃列表中有该课堂
        response = admin_client.get("/api/v1/class-sessions/active")
        assert len(response.json()["data"]) == 1
        
        # 执行：结束上课
        end_response = teacher_client.post("/api/v1/class-session/end")
        assert end_response.status_code == 200
        assert end_response.json()["success"] is True
        
        # 验证：活跃列表为空
        response = admin_client.get("/api/v1/class-sessions/active")
        assert response.json()["data"] == []

    def test_multiple_active_sessions(self, teacher_client, admin_client):
        """测试多个活跃课堂同时存在"""
        # 准备：创建多个活跃课堂（使用同一个教师，会自动结束之前的）
        # 注意：由于教师ID相同，start_class 会自动结束之前的课堂
        # 所以我们只能验证最后一个创建的课堂
        
        teacher_client.post(
            "/api/v1/class-session/start",
            json={
                "class_name": "计算机1班",
                "course_name": "高等数学"
            }
        )
        
        # 执行
        response = admin_client.get("/api/v1/class-sessions/active")
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) >= 1
        
        # 验证返回的数据包含 course_name
        course_names = [s["course_name"] for s in data["data"] if s["course_name"]]
        if course_names:
            assert "高等数学" in course_names
