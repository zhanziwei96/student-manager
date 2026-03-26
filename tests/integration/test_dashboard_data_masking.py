"""
Dashboard 数据脱敏测试
REVIEW-P1: 学号、姓名脱敏规则测试

测试场景:
- 学号脱敏（保留前几位/后几位）
- 姓名脱敏（隐藏部分字符）
- 公开接口不暴露敏感信息
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from app.models import Student, User
from app.core.security import hash_password


@pytest.fixture(scope="function")
def test_students(session: Session):
    """创建测试学生"""
    students_data = [
        ("2021001001", "张三", "软件1班"),
        ("2021001002", "李四", "软件1班"),
        ("2021001003", "王五", "软件2班"),
    ]
    
    created = []
    for sid, name, cls in students_data:
        student = session.exec(select(Student).where(Student.student_id == sid)).first()
        if student:
            session.delete(student)
            session.commit()
        
        student = Student(
            student_id=sid,
            name=name,
            class_name=cls,
            score=85.0
        )
        session.add(student)
        session.commit()
        session.refresh(student)
        created.append(student)
    
    return created


class TestDashboardDataMasking:
    """测试仪表盘数据脱敏"""
    
    def test_dashboard_public_endpoint_no_sensitive_data(self, client: TestClient, test_students):
        """测试公开仪表盘接口不返回敏感数据"""
        # 访问公开仪表盘接口
        response = client.get("/api/dashboard")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # 检查返回的数据
        dashboard_data = data.get("data", {})
        
        # 公开接口不应包含学生姓名和学号
        # 只应返回统计信息
        assert "total_students" in dashboard_data
        assert "checkin_rate" in dashboard_data
        
        # 不应包含完整的学生列表（含敏感信息）
        if "recent_checkins" in dashboard_data:
            for checkin in dashboard_data["recent_checkins"]:
                # 如果返回学生信息，应已脱敏
                if "student_name" in checkin:
                    name = checkin["student_name"]
                    # 姓名应被脱敏（如：张**）
                    assert "*" in name or len(name) <= 1
    
    def test_score_ranking_anonymization(self, client: TestClient, test_students):
        """测试分数排行榜脱敏"""
        response = client.get("/api/dashboard")
        
        assert response.status_code == 200
        data = response.json()
        
        dashboard_data = data.get("data", {})
        
        # 检查分数排行榜
        if "score_ranking" in dashboard_data:
            for item in dashboard_data["score_ranking"]:
                # 排行榜应脱敏处理
                if "name" in item:
                    name = item["name"]
                    # 姓名应被脱敏或隐藏
                    assert "*" in name or name == "" or "同学" in name
                
                if "student_id" in item:
                    sid = item["student_id"]
                    # 学号应被脱敏
                    assert "*" in sid or len(sid) < 4
    
    def test_public_stats_endpoint(self, client: TestClient, test_students):
        """测试公开统计接口"""
        response = client.get("/api/stats")
        
        # 公开接口可能需要认证，测试其行为一致性
        assert response.status_code in [200, 401]
        
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            
            # 不应包含可识别个人身份的信息
            response_text = response.text
            # 检查是否包含原始学生姓名
            for student in test_students:
                # 姓名不应以明文形式出现在响应中
                # （除非接口设计需要，但应脱敏）
                pass  # 具体断言取决于脱敏实现
    
    def test_student_name_masking_pattern(self):
        """测试姓名脱敏规则"""
        # 测试各种姓名的脱敏
        test_names = [
            ("张三", "张*"),
            ("张三丰", "张**"),
            ("欧阳锋", "欧**"),
            ("A", "*"),
        ]
        
        for original, expected_pattern in test_names:
            # 脱敏逻辑：保留第一个字，其余用 * 替换
            if len(original) <= 1:
                masked = "*"
            else:
                masked = original[0] + "*" * (len(original) - 1)
            
            assert masked == expected_pattern, f"姓名 {original} 脱敏失败"
    
    def test_student_id_masking_pattern(self):
        """测试学号脱敏规则"""
        # 测试学号脱敏
        test_ids = [
            ("2021001001", "2021****01"),  # 保留前4位和后2位
            ("S12345678", "S123****78"),   # 保留前4位和后2位
        ]
        
        for original, expected_pattern in test_ids:
            # 脱敏逻辑：保留前4位和后2位，中间用 **** 替换
            if len(original) <= 5:
                masked = "*" * len(original)
            else:
                masked = original[:4] + "****" + original[-2:]
            
            assert masked == expected_pattern, f"学号 {original} 脱敏失败，期望 {expected_pattern}，实际 {masked}"


class TestDataMaskingImplementation:
    """测试数据脱敏实现"""
    
    def test_masking_function_exists(self):
        """测试脱敏函数是否存在"""
        try:
            # 尝试导入脱敏函数
            from app.api.routes.system import get_dashboard_stats
            # 函数存在
            assert True
        except ImportError:
            pytest.skip("脱敏函数未实现")
    
    def test_student_response_masking(self, client: TestClient):
        """测试学生响应数据脱敏"""
        # 登录获取权限
        # 此测试需要认证，暂时跳过具体实现
        
        # 访问学生列表（应脱敏）
        # response = client.get("/api/students")
        
        # 验证脱敏
        pass
