"""
课表 API 集成测试
"""
import pytest
from sqlmodel import Session


@pytest.fixture
def test_schedule_data():
    """测试课表数据"""
    return {
        "course_name": "计算机基础",
        "class_name": "2025康复治疗技术1班",
        "teacher_name": "张老师",
        "day_of_week": 1,
        "start_time": "08:00",
        "end_time": "09:40",
        "classroom": "A-101",
        "week_start": 1,
        "week_end": 20
    }


@pytest.fixture
def create_test_schedule(test_engine, teacher_user):
    """创建测试课表的 fixture"""
    from app.models.course_schedule import CourseSchedule
    
    def _create_schedule(**kwargs):
        with Session(test_engine) as session:
            schedule = CourseSchedule(
                course_name=kwargs.get("course_name", "测试课程"),
                class_name=kwargs.get("class_name", "测试班级"),
                teacher_id=kwargs.get("teacher_id", teacher_user.id),
                teacher_name=kwargs.get("teacher_name", teacher_user.name),
                day_of_week=kwargs.get("day_of_week", 1),
                start_time=kwargs.get("start_time", "08:00"),
                end_time=kwargs.get("end_time", "09:40"),
                classroom=kwargs.get("classroom", "A-101"),
                week_start=kwargs.get("week_start", 1),
                week_end=kwargs.get("week_end", 20)
            )
            session.add(schedule)
            session.commit()
            session.refresh(schedule)
            return schedule
    
    return _create_schedule


def test_get_schedules_list(teacher_client, create_test_schedule):
    """测试获取课表列表"""
    # 创建测试数据
    create_test_schedule(course_name="课程1", day_of_week=1)
    create_test_schedule(course_name="课程2", day_of_week=2)
    
    response = teacher_client.get("/api/schedules")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) >= 2


def test_get_schedules_with_filter(teacher_client, create_test_schedule):
    """测试按条件筛选课表"""
    # 创建不同班级的课程
    create_test_schedule(course_name="康复课程", class_name="2025康复治疗技术1班", day_of_week=1)
    create_test_schedule(course_name="中药课程", class_name="2025中药学1班", day_of_week=1)
    
    # 按班级筛选
    response = teacher_client.get("/api/schedules?class_name=2025康复治疗技术1班")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    # 教师只能看到自己的课表


def test_get_schedules_by_day(teacher_client, create_test_schedule):
    """测试按星期筛选课表"""
    create_test_schedule(course_name="周一课程", day_of_week=1)
    create_test_schedule(course_name="周二课程", day_of_week=2)
    
    response = teacher_client.get("/api/schedules?day_of_week=1")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_get_today_schedules(teacher_client, create_test_schedule):
    """测试获取今日课表"""
    from datetime import datetime
    
    today = datetime.now().isoweekday()
    create_test_schedule(course_name="今日课程", day_of_week=today)
    
    response = teacher_client.get("/api/schedules/today")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_get_schedules_unauthorized(client):
    """测试未登录无法获取课表"""
    response = client.get("/api/schedules")
    
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False


def test_import_schedules_csv(admin_client):
    """测试 CSV 导入课表"""
    import io
    
    # 创建 CSV 内容
    csv_content = """课程名称,班级,教师姓名,星期,开始时间,结束时间,教室,开始周,结束周
计算机基础,2025康复治疗技术1班,管理员,1,08:00,09:40,A-101,1,20
数据结构,2025康复治疗技术1班,管理员,2,10:00,11:40,B-202,1,20"""
    
    file = io.BytesIO(csv_content.encode('utf-8'))
    
    response = admin_client.post(
        "/api/schedules/import",
        files={"file": ("schedules.csv", file, "text/csv")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["imported"] == 2


def test_import_schedules_invalid_format(admin_client):
    """测试导入无效格式文件"""
    import io
    
    file = io.BytesIO(b"invalid content")
    
    response = admin_client.post(
        "/api/schedules/import",
        files={"file": ("invalid.txt", file, "text/plain")}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False


def test_import_schedules_missing_columns(admin_client):
    """测试导入缺少必需列的文件"""
    import io
    
    # 缺少"星期"列
    csv_content = """课程名称,班级,教师姓名,开始时间,结束时间
计算机基础,2025康复治疗技术1班,张老师,08:00,09:40"""
    
    file = io.BytesIO(csv_content.encode('utf-8'))
    
    response = admin_client.post(
        "/api/schedules/import",
        files={"file": ("schedules.csv", file, "text/csv")}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "缺少必需的列" in data["message"]


def test_delete_schedule(admin_client, create_test_schedule):
    """测试删除课程"""
    schedule = create_test_schedule(course_name="待删除课程")
    
    response = admin_client.delete(f"/api/schedules/{schedule.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "已删除" in data["message"]


def test_delete_schedule_not_found(admin_client):
    """测试删除不存在的课程"""
    response = admin_client.delete("/api/schedules/99999")
    
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False


def test_download_template(teacher_client):
    """测试下载导入模板"""
    response = teacher_client.get("/api/schedules/template")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def test_teacher_can_import(teacher_client):
    """测试教师可以导入课表"""
    import io
    
    csv_content = """课程名称,班级,教师姓名,星期,开始时间,结束时间
测试课程,2025康复治疗技术1班,教师1,1,08:00,09:40"""
    
    file = io.BytesIO(csv_content.encode('utf-8'))
    
    response = teacher_client.post(
        "/api/schedules/import",
        files={"file": ("schedules.csv", file, "text/csv")}
    )
    
    # 教师应该有权限导入
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.smoke
def test_schedule_api_smoke(admin_client):
    """课表 API 冒烟测试"""
    # 1. 获取列表
    response = admin_client.get("/api/schedules")
    assert response.status_code == 200
    
    # 2. 获取今日课表
    response = admin_client.get("/api/schedules/today")
    assert response.status_code == 200
    
    # 3. 下载模板
    response = admin_client.get("/api/schedules/template")
    assert response.status_code == 200
