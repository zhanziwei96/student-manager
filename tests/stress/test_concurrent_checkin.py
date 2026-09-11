"""签到并发压力测试（进程内 ASGI + 独立测试库）

模拟多学生同时签到，测量并发路径的正确性与耗时。

注意：早期版本打真实服务（localhost:8000）并直连数据库造数——既依赖"后端在跑"，
也会污染开发库。现改为进程内 TestClient/ASGITransport + 测试库（classhub_test_N），
每个用例自造班级/学生/课堂数据，随测试库 TRUNCATE 自动清理。
"""
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import Session

from app.crud.course_session import start_course_session
from app.models import Student
from tests.integration.conftest import ensure_class

pytestmark = pytest.mark.integration

CLASS_NAME = "压测班"
COURSE_NAME = "压力测试课程"
STUDENT_IDS = [f"STRESS{i:03d}" for i in range(1, 51)]
TEST_SINGLE = STUDENT_IDS[0:1]
TEST_SEQUENTIAL = STUDENT_IDS[1:11]
TEST_CONCURRENT_THREAD = STUDENT_IDS[11:31]
TEST_CONCURRENT_ASYNC = STUDENT_IDS[31:]

# 进程内调用的宽松耗时上限（真实服务往返通常更快，这里只拦截数量级退化）
SINGLE_LATENCY_LIMIT = 2.0
SEQUENTIAL_AVG_LIMIT = 1.0
CONCURRENT_TOTAL_LIMIT = 10.0


@pytest.fixture
def setup_course_session(test_engine, seed_refs, teacher_user):
    """造压测数据：班级 + 50 名启用学生 + 一节进行中的课堂，返回 session_id"""
    class_id = ensure_class(test_engine, CLASS_NAME)
    with Session(test_engine) as session:
        for sid in STUDENT_IDS:
            session.add(Student(
                student_id=sid, name=f"压测学生{sid}",
                class_id=class_id,
            ))
        session.commit()
        cs = start_course_session(
            session=session,
            class_id=class_id,
            teacher_id=teacher_user.id,
            teacher_name=teacher_user.name,
            course_name=COURSE_NAME,
        )
        return cs.id


def _checkin_payload(student_id: str, session_id: int) -> dict:
    return {
        "student_id": student_id,
        "student_name": f"压测学生{student_id}",
        "device_id": f"device_{student_id}",
        "device_info": "{}",
        "session_id": session_id,
    }


def test_single_checkin(admin_client, setup_course_session):
    """单用户签到基线（教师/管理员手动签到路径）"""
    student_id = TEST_SINGLE[0]

    start = time.time()
    resp = admin_client.post("/api/v1/checkin", json=_checkin_payload(student_id, setup_course_session))
    elapsed = time.time() - start

    assert resp.status_code == 200, f"签到失败: {resp.text}"
    assert resp.json()["success"] is True
    print(f"\n单用户签到耗时: {elapsed:.3f}s")
    assert elapsed < SINGLE_LATENCY_LIMIT, f"单用户签到太慢: {elapsed}s"


def test_sequential_checkins(admin_client, setup_course_session):
    """10 个学生依次签到"""
    times = []
    for student_id in TEST_SEQUENTIAL:
        start = time.time()
        resp = admin_client.post(
            "/api/v1/checkin", json=_checkin_payload(student_id, setup_course_session))
        times.append(time.time() - start)
        assert resp.status_code == 200, f"学生 {student_id} 签到失败: {resp.text}"

    avg_time = sum(times) / len(times)
    print(f"\n顺序签到平均耗时: {avg_time:.3f}s, 最大: {max(times):.3f}s")
    assert avg_time < SEQUENTIAL_AVG_LIMIT, f"平均签到时间太长: {avg_time}s"


def test_concurrent_checkins_thread(admin_client, setup_course_session):
    """线程池模拟 20 名学生同时签到"""
    session_id = setup_course_session
    results = {"success": 0, "failed": 0, "rate_limited": 0, "times": []}

    def do_checkin(student_id: str):
        start = time.time()
        try:
            resp = admin_client.post(
                "/api/v1/checkin", json=_checkin_payload(student_id, session_id))
            elapsed = time.time() - start
            if resp.status_code == 200:
                return ("success", elapsed, None)
            if resp.status_code == 429:
                return ("rate_limited", elapsed, resp.json().get("message"))
            return ("failed", elapsed, resp.text)
        except Exception as e:  # noqa: BLE001 - 压测需统计任意异常
            return ("failed", time.time() - start, str(e))

    start_all = time.time()
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(do_checkin, sid) for sid in TEST_CONCURRENT_THREAD]
        for future in as_completed(futures):
            status, elapsed, error = future.result()
            results[status] += 1
            if status == "success":
                results["times"].append(elapsed)
    total_time = time.time() - start_all

    print(f"\n线程并发签到结果 ({len(TEST_CONCURRENT_THREAD)}人同时):")
    print(f"  成功: {results['success']}，失败: {results['failed']}，限流: {results['rate_limited']}")
    print(f"  总耗时: {total_time:.3f}s")
    if results["times"]:
        print(f"  平均耗时: {sum(results['times']) / len(results['times']):.3f}s, "
              f"最大: {max(results['times']):.3f}s")

    assert results["failed"] == 0, f"并发签到出现失败: {results}"
    assert results["success"] / len(TEST_CONCURRENT_THREAD) > 0.8, "成功率太低"
    assert total_time < CONCURRENT_TOTAL_LIMIT, f"并发处理太慢: {total_time}s"


@pytest.mark.asyncio
async def test_concurrent_checkins_async(admin_client, setup_course_session):
    """asyncio 模拟 19 名学生同时签到（ASGITransport 进程内调用）

    依赖 admin_client：它负责建管理员账号与 app.dependency_overrides[get_session]。
    """
    from main import app

    session_id = setup_course_session
    results = {"success": 0, "failed": 0, "rate_limited": 0, "times": []}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        login = await ac.post("/api/v1/login", json={
            "username": "admin", "password": "admin123", "role": "admin",
        })
        assert login.status_code == 200, login.text

        async def do_checkin(student_id: str):
            start = time.time()
            try:
                resp = await ac.post("/api/v1/checkin", json=_checkin_payload(student_id, session_id))
                elapsed = time.time() - start
                if resp.status_code == 200:
                    return ("success", elapsed, None)
                if resp.status_code == 429:
                    return ("rate_limited", elapsed, resp.json().get("message"))
                return ("failed", elapsed, resp.text)
            except Exception as e:  # noqa: BLE001 - 压测需统计任意异常
                return ("failed", time.time() - start, str(e))

        start_all = time.time()
        outcomes = await asyncio.gather(*[do_checkin(sid) for sid in TEST_CONCURRENT_ASYNC])
        total_time = time.time() - start_all

    for status, elapsed, error in outcomes:
        results[status] += 1
        if status == "success":
            results["times"].append(elapsed)

    print(f"\n异步并发签到结果 ({len(TEST_CONCURRENT_ASYNC)}人同时):")
    print(f"  成功: {results['success']}，失败: {results['failed']}，限流: {results['rate_limited']}")
    print(f"  总耗时: {total_time:.3f}s，QPS: {len(TEST_CONCURRENT_ASYNC) / total_time:.1f}")
    if results["times"]:
        print(f"  平均耗时: {sum(results['times']) / len(results['times']):.3f}s, "
              f"最大: {max(results['times']):.3f}s")

    assert results["failed"] == 0, f"异步并发签到出现失败: {results}"
    assert results["success"] / len(TEST_CONCURRENT_ASYNC) > 0.8, "成功率太低"
    assert total_time < CONCURRENT_TOTAL_LIMIT, f"并发处理太慢: {total_time}s"
