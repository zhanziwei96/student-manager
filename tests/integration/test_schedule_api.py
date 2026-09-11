"""
课表 API 集成测试
"""
import pytest
from sqlmodel import Session, select


@pytest.fixture
def test_schedule_data():
    """测试课表数据"""
    return {
        "course_name": "计算机基础",
        "class_name": "一班",
        "teacher_name": "张老师",
        "day_of_week": 1,
        "start_time": "08:00",
        "end_time": "09:40",
        "classroom": "A-101",
        "week_start": 1,
        "week_end": 20
    }


@pytest.fixture
def create_test_schedule(test_engine, teacher_user, seed_refs):
    """创建测试课表的 fixture（class_id/semester_id 为纯 FK 锚点，取自 seed_refs）"""
    from app.models.course_schedule import CourseSchedule

    def _create_schedule(**kwargs):
        with Session(test_engine) as session:
            class_name = kwargs.get("class_name", "一班")
            schedule = CourseSchedule(
                course_name=kwargs.get("course_name", "测试课程"),
                semester_id=seed_refs["semester_id"],
                class_id=seed_refs[class_name],
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
    
    response = teacher_client.get("/api/v1/schedules")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) >= 2


def test_get_schedules_with_filter(teacher_client, create_test_schedule, seed_refs):
    """测试按条件筛选课表"""
    # 创建不同班级的课程
    create_test_schedule(course_name="康复课程", class_name="一班", day_of_week=1)
    create_test_schedule(course_name="中药课程", class_name="二班", day_of_week=1)

    # 按班级筛选
    response = teacher_client.get(f"/api/v1/schedules?class_id={seed_refs['一班']}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    # 教师只能看到自己的课表


def test_get_schedules_by_day(teacher_client, create_test_schedule):
    """测试按星期筛选课表"""
    create_test_schedule(course_name="周一课程", day_of_week=1)
    create_test_schedule(course_name="周二课程", day_of_week=2)
    
    response = teacher_client.get("/api/v1/schedules?day_of_week=1")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_get_today_schedules(teacher_client, create_test_schedule):
    """测试获取今日课表"""
    from datetime import datetime
    
    today = datetime.now().isoweekday()
    create_test_schedule(course_name="今日课程", day_of_week=today)
    
    response = teacher_client.get("/api/v1/schedules/today")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_get_schedules_unauthorized(client):
    """测试未登录无法获取课表"""
    response = client.get("/api/v1/schedules")
    
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False


def test_import_schedules_csv(admin_client, test_engine, seed_refs):
    """测试 CSV 导入课表"""
    import io

    # 创建 CSV 内容（班级按「所属届+专业+班级名」三元组定位，与学生导入对齐）
    csv_content = """课程名称,所属届,专业,班级名,教师姓名,星期,开始时间,结束时间,教室,开始周,结束周
计算机基础,2026,,一班,管理员,1,08:00,09:40,A-101,1,20
数据结构,2026,,一班,管理员,2,10:00,11:40,B-202,1,20"""
    
    file = io.BytesIO(csv_content.encode('utf-8'))
    
    response = admin_client.post(
        "/api/v1/schedules/import",
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
        "/api/v1/schedules/import",
        files={"file": ("invalid.txt", file, "text/plain")}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False


def test_import_schedules_missing_columns(admin_client):
    """测试导入缺少必需列的文件"""
    import io
    
    # 缺少"星期"列
    csv_content = """课程名称,所属届,专业,班级名,教师姓名,开始时间,结束时间
计算机基础,2025,康复治疗技术,1班,张老师,08:00,09:40"""
    
    file = io.BytesIO(csv_content.encode('utf-8'))
    
    response = admin_client.post(
        "/api/v1/schedules/import",
        files={"file": ("schedules.csv", file, "text/csv")}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "缺少必需的列" in data["message"]


def test_delete_schedule(admin_client, create_test_schedule):
    """测试删除课程"""
    schedule = create_test_schedule(course_name="待删除课程")
    
    response = admin_client.delete(f"/api/v1/schedules/{schedule.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "已删除" in data["message"]


def test_delete_schedule_not_found(admin_client):
    """测试删除不存在的课程"""
    response = admin_client.delete("/api/v1/schedules/99999")
    
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False


def test_download_template(teacher_client):
    """测试下载导入模板"""
    response = teacher_client.get("/api/v1/schedules/template")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def test_teacher_cannot_import(teacher_client):
    """测试教师无权导入课表（仅管理员可导入）"""
    import io
    
    csv_content = """课程名称,所属届,专业,班级名,教师姓名,星期,开始时间,结束时间
测试课程,2025,康复治疗技术,1班,教师1,1,08:00,09:40"""
    
    file = io.BytesIO(csv_content.encode('utf-8'))
    
    response = teacher_client.post(
        "/api/v1/schedules/import",
        files={"file": ("schedules.csv", file, "text/csv")}
    )
    
    # 教师无权导入课表，应返回 403
    assert response.status_code == 403


@pytest.mark.smoke
def test_schedule_api_smoke(admin_client):
    """课表 API 冒烟测试"""
    # 1. 获取列表
    response = admin_client.get("/api/v1/schedules")
    assert response.status_code == 200
    
    # 2. 获取今日课表
    response = admin_client.get("/api/v1/schedules/today")
    assert response.status_code == 200
    
    # 3. 下载模板
    response = admin_client.get("/api/v1/schedules/template")
    assert response.status_code == 200


def test_get_schedules_includes_week_data(teacher_client, create_test_schedule):
    """测试获取课表列表包含调课/课堂状态数据"""
    from datetime import datetime

    schedule = create_test_schedule(course_name="状态测试课", day_of_week=1)
    current_week = 5

    # 先创建一条停课调整记录
    teacher_client.post("/api/v1/schedule-adjustments", json={
        "schedule_id": schedule.id,
        "week_number": current_week,
        "type": "cancel",
        "reason": "测试停课"
    })

    response = teacher_client.get(f"/api/v1/schedules?week_number={current_week}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    item = next((s for s in data["data"] if s["id"] == schedule.id), None)
    assert item is not None
    assert item["week_number"] == current_week
    assert "week_type_match" in item
    assert "session_status" in item
    assert "active_session_id" in item
    assert "adjustment" in item
    assert item["session_status"] == "cancelled"
    assert item["adjustment"] is not None
    assert item["adjustment"]["type"] == "cancel"


def test_get_schedules_default_week_uses_current(teacher_client, create_test_schedule):
    """测试不传 week_number 时默认使用当前周"""
    schedule = create_test_schedule(course_name="默认周测试", day_of_week=1)

    response = teacher_client.get("/api/v1/schedules")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    item = next((s for s in data["data"] if s["id"] == schedule.id), None)
    assert item is not None
    assert "week_number" in item
    assert "session_status" in item


def test_import_schedule_dup_key_ignores_previous_term(admin_client, test_engine, seed_refs):
    """上学期同课程/教师/时段不应阻止新学期导入"""
    from datetime import date
    from app.models import CourseSchedule, Semester

    # 先手工造一条上学期的同键课表（旧学期用非当前学期的 semester_id 锚定）
    with Session(test_engine) as session:
        old_sem = Semester(label="2025-2026-2", start_date=date(2025, 9, 1),
                           total_weeks=20, is_current=False)
        session.add(old_sem)
        session.commit()
        session.refresh(old_sem)
        session.add(CourseSchedule(
            course_name="高等数学", class_id=seed_refs["一班"], semester_id=old_sem.id,
            teacher_name="张老师",
            day_of_week=1, start_time="08:00", end_time="09:40",
            week_start=1, week_end=20,
        ))
        session.commit()

    # 新学期导入同键课表（应成功而非"课程已存在"）
    import io

    csv_content = """课程名称,所属届,专业,班级名,教师姓名,星期,开始时间,结束时间,开始周,结束周
高等数学,2026,,一班,张老师,1,08:00,09:40,1,20"""

    file = io.BytesIO(csv_content.encode('utf-8'))

    response = admin_client.post(
        "/api/v1/schedules/import",
        files={"file": ("schedules.csv", file, "text/csv")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["imported"] == 1
    assert data["data"]["errors"] == []


def test_get_schedules_excludes_previous_term_schedules(admin_client, test_engine, seed_refs):
    """学期隔离：上学期课表不得混入当前学期课表列表"""
    from datetime import date
    from app.models import CourseSchedule, Semester

    # 手工造一条上学期的课表（当前学期数据经 create_test_schedule 验证被列表返回）
    with Session(test_engine) as session:
        old_sem = Semester(label="2025-2026-2", start_date=date(2025, 9, 1),
                           total_weeks=20, is_current=False)
        session.add(old_sem)
        session.commit()
        session.refresh(old_sem)
        old = CourseSchedule(
            course_name="上学期遗留课", class_id=seed_refs["一班"], semester_id=old_sem.id,
            teacher_name="张老师",
            day_of_week=1, start_time="08:00", end_time="09:40",
            week_start=1, week_end=20,
        )
        session.add(old)
        session.commit()
        session.refresh(old)

    response = admin_client.get("/api/v1/schedules")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert all(item["id"] != old.id for item in data["data"])
    assert all(item["course_name"] != "上学期遗留课" for item in data["data"])
