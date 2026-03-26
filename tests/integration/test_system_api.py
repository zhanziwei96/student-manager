"""
系统相关 API 集成测试
"""
import pytest


class TestHealthAPI:
    """健康检查 API 测试"""
    
    def test_health_check(self, client):
        """健康检查接口"""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
    
    def test_health_check_no_auth_required(self, client):
        """健康检查不需要认证"""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        # 确保没有返回 401
        assert response.json()["status"] == "healthy"


class TestStatsAPI:
    """统计 API 测试"""
    
    def test_get_stats_empty(self, admin_client):
        """空数据统计"""
        response = admin_client.get("/api/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total_students"] == 0
        assert data["data"]["total_classes"] == 0
        assert data["data"]["today_checkins"] == 0
    
    def test_get_stats_with_data(self, admin_client, sample_students):
        """有数据的统计"""
        response = admin_client.get("/api/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total_students"] == 6
        assert data["data"]["total_classes"] == 3  # 一班、二班
        assert data["data"]["today_checkins"] == 0
    
    def test_get_stats_requires_auth(self, client):
        """统计接口需要认证（未登录返回 401）"""
        response = client.get("/api/stats")
        
        assert response.status_code == 401
    
    def test_get_stats_student_access(self, student_client, student_user):
        """学生可以访问统计"""
        response = student_client.get("/api/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total_students"] == 1  # 只有 student_user 一个学生
    
    def test_get_stats_teacher_access(self, teacher_client, sample_students):
        """教师可以访问统计"""
        response = teacher_client.get("/api/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total_students"] == 6
