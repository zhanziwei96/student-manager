"""
课表教师分配 API 测试
测试分配和取消分配教师到课程的功能
"""
import pytest
from sqlmodel import Session

from app.models.course_schedule import CourseSchedule


@pytest.fixture
def sample_schedule(test_engine):
    """创建测试课程"""
    with Session(test_engine) as session:
        schedule = CourseSchedule(
            course_name="测试课程",
            class_name="测试班级",
            day_of_week=1,
            start_time="08:00",
            end_time="09:40",
            classroom="A-101",
            week_start=1,
            week_end=20
        )
        session.add(schedule)
        session.commit()
        session.refresh(schedule)
        yield schedule


class TestScheduleTeacherAssignment:
    """测试课表教师分配功能"""
    
    def test_assign_teacher_to_schedule_success(self, admin_client, sample_schedule):
        """测试成功分配教师到课程"""
        response = admin_client.put(
            f"/api/v1/schedules/{sample_schedule.id}/assign",
            params={"teacher_id": 1, "teacher_name": "张老师"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "张老师" in data["message"]
        assert "测试课程" in data["message"]
    
    def test_assign_teacher_to_nonexistent_schedule(self, admin_client):
        """测试为不存在的课程分配教师"""
        response = admin_client.put(
            "/api/v1/schedules/99999/assign",
            params={"teacher_id": 1, "teacher_name": "张老师"}
        )
        
        assert response.status_code == 404
        data = response.json()
        # 项目全局异常处理器转换后的格式: {"success": False, "message": "..."}
        assert data["success"] is False
        assert "message" in data
        assert "不存在" in data["message"]
    
    def test_unassign_teacher_from_schedule_success(self, admin_client, sample_schedule):
        """测试成功取消教师分配"""
        # 先分配教师
        admin_client.put(
            f"/api/v1/schedules/{sample_schedule.id}/assign",
            params={"teacher_id": 1, "teacher_name": "张老师"}
        )
        
        # 再取消分配
        response = admin_client.put(
            f"/api/v1/schedules/{sample_schedule.id}/unassign"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "取消" in data["message"]
    
    def test_unassign_teacher_from_nonexistent_schedule(self, admin_client):
        """测试为不存在的课程取消教师分配"""
        response = admin_client.put(
            "/api/v1/schedules/99999/unassign"
        )
        
        assert response.status_code == 404
        data = response.json()
        # 项目全局异常处理器转换后的格式: {"success": False, "message": "..."}
        assert data["success"] is False
        assert "message" in data
        assert "不存在" in data["message"]
    
    def test_assign_teacher_requires_admin(self, teacher_client, sample_schedule):
        """测试非管理员无法分配教师"""
        response = teacher_client.put(
            f"/api/v1/schedules/{sample_schedule.id}/assign",
            params={"teacher_id": 1, "teacher_name": "张老师"}
        )
        
        assert response.status_code == 403
    
    def test_unassign_teacher_requires_admin(self, teacher_client, sample_schedule):
        """测试非管理员无法取消教师分配"""
        response = teacher_client.put(
            f"/api/v1/schedules/{sample_schedule.id}/unassign"
        )
        
        assert response.status_code == 403
    
    def test_schedule_teacher_persistence(self, admin_client, sample_schedule):
        """测试教师分配信息持久化"""
        # 分配教师
        admin_client.put(
            f"/api/v1/schedules/{sample_schedule.id}/assign",
            params={"teacher_id": 5, "teacher_name": "李老师"}
        )
        
        # 获取课表列表并验证
        response = admin_client.get("/api/v1/schedules", params={"teacher_id": 5})
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert len(data["data"]) > 0
        assert data["data"][0]["teacher_id"] == 5
        assert data["data"][0]["teacher_name"] == "李老师"
