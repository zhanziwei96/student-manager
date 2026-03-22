"""
签到相关 API 集成测试
"""
import pytest


class TestClassSessionAPI:
    """上课状态 API 测试"""
    
    def test_get_class_session_not_active(self, client):
        """获取未开始的上课状态 - 不需要登录"""
        response = client.get("/api/class-session")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["active"] is False
    
    def test_start_class_success(self, admin_client):
        """成功开始上课"""
        response = admin_client.post("/api/class-session/start", json={
            "class_name": "一班"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "上课开始"
        assert data["data"]["active"] is True
        assert data["data"]["class_name"] == "一班"
    
    def test_start_class_unauthorized(self, client):
        """未授权开始上课"""
        response = client.post("/api/class-session/start", json={
            "class_name": "一班"
        })
        
        assert response.status_code == 401
    
    def test_end_class_success(self, admin_client):
        """成功结束上课"""
        # 先开始上课
        admin_client.post("/api/class-session/start", json={"class_name": "一班"})
        
        # 结束上课
        response = admin_client.post("/api/class-session/end")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "上课结束"
        
        # 验证状态
        get_response = admin_client.get("/api/class-session")
        assert get_response.json()["data"]["active"] is False
    
    def test_get_active_class_session(self, client, admin_client):
        """获取进行中的上课状态 - 不需要登录"""
        # 开始上课
        admin_client.post("/api/class-session/start", json={
            "class_name": "二班"
        })
        
        response = client.get("/api/class-session")
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["active"] is True
        assert data["data"]["class_name"] == "二班"
        assert "start_time" in data["data"]


class TestCheckinAPI:
    """签到 API 测试"""
    
    def test_checkin_success(self, client, admin_client, sample_students):
        """成功签到"""
        # 开始上课
        admin_client.post("/api/class-session/start", json={
            "class_name": "一班"
        })
        
        # 学生签到
        response = client.post("/api/checkin", json={
            "student_id": "S001",
            "student_name": "学生1"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "签到成功"
        assert data["data"]["student_id"] == "S001"
    
    def test_checkin_no_active_class(self, client, sample_students):
        """没有进行中的上课"""
        response = client.post("/api/checkin", json={
            "student_id": "S001",
            "student_name": "学生1"
        })
        
        assert response.status_code == 400
        assert "未在上课" in response.json()["message"]
    
    def test_checkin_student_not_found(self, client, admin_client):
        """学生不存在"""
        # 开始上课
        admin_client.post("/api/class-session/start", json={"class_name": "一班"})
        
        response = client.post("/api/checkin", json={
            "student_id": "NONEXISTENT",
            "student_name": "不存在的学生"
        })
        
        assert response.status_code == 404
    
    def test_checkin_duplicate(self, client, admin_client, sample_students):
        """重复签到"""
        # 开始上课
        admin_client.post("/api/class-session/start", json={"class_name": "一班"})
        
        # 第一次签到
        client.post("/api/checkin", json={
            "student_id": "S001",
            "student_name": "学生1"
        })
        
        # 第二次签到（重复）
        response = client.post("/api/checkin", json={
            "student_id": "S001",
            "student_name": "学生1"
        })
        
        assert response.status_code == 409
        assert "已签到" in response.json()["message"]


class TestTodayCheckinsAPI:
    """今日签到列表 API 测试"""
    
    def test_get_today_checkins_empty(self, client):
        """空签到列表"""
        response = client.get("/api/checkins/today")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 0
    
    def test_get_today_checkins(self, client, admin_client, sample_students):
        """获取今日签到列表"""
        # 开始上课
        admin_client.post("/api/class-session/start", json={"class_name": "一班"})
        
        # 签到两个学生
        client.post("/api/checkin", json={"student_id": "S001", "student_name": "学生1"})
        client.post("/api/checkin", json={"student_id": "S002", "student_name": "学生2"})
        
        # 获取签到列表
        response = client.get("/api/checkins/today")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 2
    
    def test_get_today_checkins_by_class(self, client, admin_client, sample_students):
        """按班级筛选签到"""
        # 开始一班上课
        admin_client.post("/api/class-session/start", json={"class_name": "一班"})
        
        # 签到不同班级的学生（但上课班级是一班，所以签到记录都属于一班）
        client.post("/api/checkin", json={"student_id": "S001", "student_name": "学生1"})
        client.post("/api/checkin", json={"student_id": "S004", "student_name": "学生4"})
        
        response = client.get("/api/checkins/today?class_name=一班")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2


class TestCheckinStatsAPI:
    """签到统计 API 测试"""
    
    def test_checkin_stats_no_active_class(self, client):
        """没有进行中的上课统计"""
        response = client.get("/api/checkins/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["active"] is False
        assert data["data"]["total"] == 0
    
    def test_checkin_stats_with_active_class(self, client, admin_client, sample_students):
        """有进行中的上课统计"""
        # 开始上课（一班有3个学生）
        admin_client.post("/api/class-session/start", json={"class_name": "一班"})
        
        # 签到2个学生
        client.post("/api/checkin", json={"student_id": "S001", "student_name": "学生1"})
        client.post("/api/checkin", json={"student_id": "S002", "student_name": "学生2"})
        
        response = client.get("/api/checkins/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["active"] is True
        assert data["data"]["class_name"] == "一班"
        assert data["data"]["total"] == 3  # 一班有3个学生
        assert data["data"]["checked_in"] == 2
        assert data["data"]["not_checked_in"] == 1
        assert data["data"]["rate"] == pytest.approx(66.7, 0.1)
