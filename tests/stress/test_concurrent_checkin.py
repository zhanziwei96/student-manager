"""
签到并发压力测试
模拟多学生同时签到场景，验证数据库并发性能
"""
import asyncio
import time
import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed
from httpx import Client, AsyncClient

# 后端服务探测：未运行时跳过压测（live-service 测试惯例，同根 conftest ServiceChecker）
import urllib.request
_backend_up = False
try:
    urllib.request.urlopen("http://localhost:8000/api/v1/health", timeout=2)
    _backend_up = True
except Exception:
    pass
pytestmark = pytest.mark.skipif(not _backend_up, reason="后端服务未运行，跳过压测")

# 测试配置
BASE_URL = "http://localhost:8000/api/v1"
TEST_CLASS = "2025中医康复治疗2班"
# 50个测试学生，每个测试使用不同范围避免冲突
TEST_STUDENTS_ALL = [f"25130702{i:02d}" for i in range(1, 51)]  # 50个学生
TEST_SINGLE = TEST_STUDENTS_ALL[0]  # 单人测试
TEST_SEQUENTIAL = TEST_STUDENTS_ALL[1:11]  # 10个学生顺序测试
TEST_CONCURRENT_THREAD = TEST_STUDENTS_ALL[11:31]  # 20个学生并发测试
TEST_CONCURRENT_ASYNC = TEST_STUDENTS_ALL[31:51]  # 20个学生异步并发测试


@pytest.fixture(scope="module")
def client():
    """同步 HTTP 客户端"""
    with Client(base_url=BASE_URL, timeout=30) as c:
        yield c


@pytest.fixture(scope="module")
def teacher_cookies(client):
    """获取教师 session cookies"""
    resp = client.post("/login", json={
        "username": "admin",
        "password": "admin123"
    })
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    # 返回 cookies dict
    return dict(client.cookies)


@pytest.fixture(scope="module")
def setup_course_session(client, teacher_cookies):
    """创建测试课堂会话"""
    # 导入cookies
    client.cookies.update(teacher_cookies)

    # 为压测班级造一个启用学生（满足 verify_class_has_active_students 校验）
    import psycopg2
    from datetime import datetime
    from app.core.config import get_settings
    db_url = get_settings().database.url
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    now = datetime.now()
    cursor.execute(
        "INSERT INTO students (student_id, name, class_name, score, is_account_enabled, created_at, version, login_fail_count) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (student_id) DO NOTHING",
        ("STRESS_TEST_STUDENT", "压测学生", TEST_CLASS, 70.0, True, now, 1, 0)
    )
    conn.commit()
    conn.close()

    # 先结束所有活跃会话
    sessions_resp = client.get("/course-sessions")
    if sessions_resp.status_code == 200:
        for s in sessions_resp.json().get("data", []):
            client.post(f"/course-sessions/{s['id']}/end")

    # 创建新会话
    resp = client.post(
        "/course-sessions/start",
        json={
            "class_name": TEST_CLASS,
            "course_name": "压力测试课程"
        }
    )
    assert resp.status_code == 200
    session_id = resp.json()["data"]["id"]

    yield session_id

    # 清理：删除该会话的所有签到记录，然后结束会话
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM checkin_records WHERE session_id = %s", (session_id,))
        cursor.execute("DELETE FROM students WHERE student_id = %s", ("STRESS_TEST_STUDENT",))
        conn.commit()
        conn.close()
        print(f"\n清理：已删除会话 {session_id} 的 {cursor.rowcount} 条签到记录")
    except Exception as e:
        print(f"\n清理签到记录失败: {e}")

    client.post(f"/course-sessions/{session_id}/end")


def test_single_checkin(client, setup_course_session):
    """测试单用户签到 - 基线测试（教师手动签到路径）"""
    student_id = TEST_SINGLE
    session_id = setup_course_session

    start = time.time()
    resp = client.post("/checkin", json={
        "student_id": student_id,
        "student_name": f"学生{student_id}",
        "device_id": f"device_{student_id}",
        "device_info": "{}",
        "session_id": session_id
    })
    elapsed = time.time() - start

    assert resp.status_code == 200, f"签到失败: {resp.text}"
    assert resp.json()["success"] is True
    print(f"\n单用户签到耗时: {elapsed:.3f}s")
    assert elapsed < 1.0, f"单用户签到太慢: {elapsed}s"


def test_sequential_checkins(client, setup_course_session):
    """测试顺序签到 - 10个学生依次签到"""
    times = []
    session_id = setup_course_session

    for student_id in TEST_SEQUENTIAL:
        start = time.time()
        resp = client.post("/checkin", json={
            "student_id": student_id,
            "student_name": f"学生{student_id}",
            "device_id": f"device_{student_id}",
            "device_info": "{}",
            "session_id": session_id
        })
        elapsed = time.time() - start
        times.append(elapsed)

        assert resp.status_code == 200, f"学生 {student_id} 签到失败: {resp.text}"

    avg_time = sum(times) / len(times)
    max_time = max(times)
    print(f"\n顺序签到平均耗时: {avg_time:.3f}s, 最大: {max_time:.3f}s")
    assert avg_time < 0.5, f"平均签到时间太长: {avg_time}s"


def test_concurrent_checkins_thread(client, setup_course_session):
    """测试并发签到 - 使用线程池模拟20学生同时签到"""
    test_students = TEST_CONCURRENT_THREAD
    session_id = setup_course_session
    results = {"success": 0, "failed": 0, "rate_limited": 0, "times": []}

    def do_checkin(student_id):
        start = time.time()
        try:
            resp = client.post("/checkin", json={
                "student_id": student_id,
                "student_name": f"学生{student_id}",
                "device_id": f"device_{student_id}",
                "device_info": "{}",
                "session_id": session_id
            })
            elapsed = time.time() - start

            if resp.status_code == 200:
                return ("success", elapsed, None)
            elif resp.status_code == 429:
                return ("rate_limited", elapsed, resp.json().get("message"))
            else:
                return ("failed", elapsed, resp.text)
        except Exception as e:
            elapsed = time.time() - start
            return ("failed", elapsed, str(e))

    # 并发执行
    start_all = time.time()
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(do_checkin, sid): sid for sid in test_students}

        for future in as_completed(futures):
            status, elapsed, error = future.result()
            results[status] += 1
            if status == "success":
                results["times"].append(elapsed)

    total_time = time.time() - start_all

    print(f"\n并发签到结果 (20人同时):")
    print(f"  成功: {results['success']}")
    print(f"  限流: {results['rate_limited']}")
    print(f"  失败: {results['failed']}")
    print(f"  总耗时: {total_time:.3f}s")

    if results["times"]:
        avg_time = sum(results["times"]) / len(results["times"])
        max_time = max(results["times"])
        print(f"  平均耗时: {avg_time:.3f}s, 最大: {max_time:.3f}s")

    # 验证：成功率应 > 80%
    success_rate = results["success"] / len(test_students)
    assert success_rate > 0.8, f"成功率太低: {success_rate:.1%}"

    # 验证：总耗时应 < 5秒（20人同时）
    assert total_time < 5.0, f"并发处理太慢: {total_time}s"


@pytest.mark.asyncio
async def test_concurrent_checkins_async(setup_course_session, teacher_cookies):
    """测试异步并发签到 - 使用 asyncio 模拟20学生同时签到"""
    test_students = TEST_CONCURRENT_ASYNC
    session_id = setup_course_session
    results = {"success": 0, "failed": 0, "rate_limited": 0, "times": []}

    async def do_checkin(student_id):
        start = time.time()
        try:
            async with AsyncClient(base_url=BASE_URL, timeout=30, cookies=teacher_cookies) as ac:
                resp = await ac.post("/checkin", json={
                    "student_id": student_id,
                    "student_name": f"学生{student_id}",
                    "device_id": f"device_{student_id}",
                    "device_info": "{}",
                    "session_id": session_id
                })
                elapsed = time.time() - start

                if resp.status_code == 200:
                    return ("success", elapsed, None)
                elif resp.status_code == 429:
                    return ("rate_limited", elapsed, resp.json().get("message"))
                else:
                    return ("failed", elapsed, resp.text)
        except Exception as e:
            elapsed = time.time() - start
            return ("failed", elapsed, str(e))

    # 并发执行所有签到
    start_all = time.time()
    tasks = [do_checkin(sid) for sid in test_students]
    outcomes = await asyncio.gather(*tasks)

    for status, elapsed, error in outcomes:
        results[status] += 1
        if status == "success":
            results["times"].append(elapsed)

    total_time = time.time() - start_all

    print(f"\n异步并发签到结果 (30人同时):")
    print(f"  成功: {results['success']}")
    print(f"  限流: {results['rate_limited']}")
    print(f"  失败: {results['failed']}")
    print(f"  总耗时: {total_time:.3f}s")

    if results["times"]:
        avg_time = sum(results["times"]) / len(results["times"])
        max_time = max(results["times"])
        print(f"  平均耗时: {avg_time:.3f}s, 最大: {max_time:.3f}s")
        print(f"  QPS: {len(test_students)/total_time:.1f}")

    # 验证
    success_rate = results["success"] / len(test_students)
    assert success_rate > 0.8, f"成功率太低: {success_rate:.1%}"
    assert total_time < 5.0, f"并发处理太慢: {total_time}s"


if __name__ == "__main__":
    # 直接运行测试
    pytest.main([__file__, "-v", "-s"])
