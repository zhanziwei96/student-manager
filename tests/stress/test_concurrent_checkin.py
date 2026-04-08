"""
签到并发压力测试
模拟多学生同时签到场景，验证数据库并发性能
"""
import asyncio
import time
import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed
from httpx import Client, AsyncClient

# 测试配置
BASE_URL = "http://localhost:8000/api/v1"
TEST_CLASS = "测试班级"
TEST_STUDENTS = [f"202400{i:03d}" for i in range(1, 51)]  # 50个学生


@pytest.fixture(scope="module")
def client():
    """同步 HTTP 客户端"""
    with Client(base_url=BASE_URL, timeout=30) as c:
        yield c


@pytest.fixture(scope="module")
def teacher_token(client):
    """获取教师 token"""
    resp = client.post("/login", json={
        "username": "admin",
        "password": "admin123"
    })
    assert resp.status_code == 200
    return resp.json()["data"]["token"]


@pytest.fixture(scope="module")
def setup_course_session(client, teacher_token):
    """创建测试课堂会话"""
    # 先结束所有活跃会话
    client.post(
        "/class-session",
        json={"action": "end"},
        headers={"Authorization": f"Bearer {teacher_token}"}
    )

    # 创建新会话
    resp = client.post(
        "/class-session",
        json={
            "action": "start",
            "class_name": TEST_CLASS,
            "course_name": "压力测试课程"
        },
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert resp.status_code == 200
    session_id = resp.json()["data"]["session_id"]

    yield session_id

    # 清理：结束会话
    client.post(
        "/class-session",
        json={"action": "end"},
        headers={"Authorization": f"Bearer {teacher_token}"}
    )


def test_single_checkin(client, setup_course_session):
    """测试单用户签到 - 基线测试"""
    student_id = TEST_STUDENTS[0]

    start = time.time()
    resp = client.post("/checkin", json={
        "student_id": student_id,
        "student_name": f"学生{student_id}",
        "device_id": f"device_{student_id}",
        "device_info": "{}"
    })
    elapsed = time.time() - start

    assert resp.status_code == 200, f"签到失败: {resp.text}"
    assert resp.json()["success"] is True
    print(f"\n单用户签到耗时: {elapsed:.3f}s")
    assert elapsed < 1.0, f"单用户签到太慢: {elapsed}s"


def test_sequential_checkins(client, setup_course_session):
    """测试顺序签到 - 10个学生依次签到"""
    times = []

    for student_id in TEST_STUDENTS[:10]:
        start = time.time()
        resp = client.post("/checkin", json={
            "student_id": student_id,
            "student_name": f"学生{student_id}",
            "device_id": f"device_{student_id}",
            "device_info": "{}"
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
    test_students = TEST_STUDENTS[10:30]  # 取20个学生
    results = {"success": 0, "failed": 0, "rate_limited": 0, "times": []}

    def do_checkin(student_id):
        start = time.time()
        try:
            resp = client.post("/checkin", json={
                "student_id": student_id,
                "student_name": f"学生{student_id}",
                "device_id": f"device_{student_id}",
                "device_info": "{}"
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
async def test_concurrent_checkins_async(setup_course_session):
    """测试异步并发签到 - 使用 asyncio 模拟50学生同时签到"""
    test_students = TEST_STUDENTS[20:50]  # 取30个学生
    results = {"success": 0, "failed": 0, "rate_limited": 0, "times": []}

    async def do_checkin(student_id):
        start = time.time()
        try:
            async with AsyncClient(base_url=BASE_URL, timeout=30) as ac:
                resp = await ac.post("/checkin", json={
                    "student_id": student_id,
                    "student_name": f"学生{student_id}",
                    "device_id": f"device_{student_id}",
                    "device_info": "{}"
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
