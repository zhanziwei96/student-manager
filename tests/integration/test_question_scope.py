"""问答模块越权回归测试

覆盖 `backend/app/api/routes/questions.py` 的五个越权点：
- Q1 `POST /teacher/questions`：教师只能投放到自己授课关联的班级
- Q2 `PUT /teacher/answers/{id}/star`：只能标记自己问题下的回答
- Q3 `POST /teacher/answers/{id}/reply`：只能追问自己问题下的回答
- Q4 `GET /student/questions/{id}/answers`：教师视图仅限归属教师与管理员，
  其余调用者（含别班教师）一律匿名视图，且必须先对该问题可见
- Q5 `POST /student/answers`：只能回答对自己可见的问题（与 Q4 读侧对齐）

`teacher_client` 关联「一班 + 二班」，`make_teacher_client` 可造出关联
「三班」或**不关联任何班级**的教师，作为越权/ fail-closed 场景。
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select


@pytest.fixture(autouse=True)
def seed_active_students(test_engine, seed_refs):
    """为三个班各预置 1 个启用学生，返回 {班名: 学号}

    关键：三班也要有启用学生，否则「向三班提问」会因「班级无启用学生」而 400，
    掩盖真正的归属校验 403（测试会因为错误的原因通过）。
    """
    from app.models import Student

    ids = {}
    with Session(test_engine) as session:
        for i, name in enumerate(("一班", "二班", "三班")):
            student_id = f"SC{i:03d}"
            session.add(Student(
                student_id=student_id, name=f"范围学生{i}", class_id=seed_refs[name],
            ))
            ids[name] = student_id
        session.commit()
    return ids


@pytest.fixture
def make_teacher_client(test_engine, seed_refs):
    """工厂夹具：创建教师（关联指定班级的教学班）并返回已登录客户端

    class_names 传空元组 → 教学班不写 course_offering_classes 关联行（fail-closed 场景）。
    """
    from contextlib import ExitStack
    from datetime import date

    from app.core.db import get_session
    from app.core.security import generate_password_hash
    from app.models import (
        Course, CourseOffering, CourseOfferingClass, Semester, User,
    )
    from app.models.constants import UserRoleConst
    from main import app

    stack = ExitStack()

    def _make(username: str, class_names: tuple = ()):
        with Session(test_engine) as session:
            password_hash, salt = generate_password_hash("scope123")
            user = User(
                username=username, name=username,
                password_hash=password_hash, salt=salt,
                role=UserRoleConst.TEACHER, is_active=True,
            )
            session.add(user)
            session.commit()
            session.refresh(user)

            course = session.exec(select(Course).where(Course.code == "SCOPE1")).first()
            if course is None:
                course = Course(code="SCOPE1", name="越权测试课程")
                session.add(course)
            sem = session.exec(select(Semester).where(Semester.label == "SCOPE-SEED")).first()
            if sem is None:
                sem = Semester(label="SCOPE-SEED", start_date=date(2026, 1, 1),
                               total_weeks=20, is_current=False)
                session.add(sem)
            session.commit()

            offering = CourseOffering(
                course_id=course.id, semester_id=sem.id, teacher_id=user.id,
                teacher_name=user.name, status="active",
            )
            session.add(offering)
            session.flush()
            for name in class_names:
                session.add(CourseOfferingClass(
                    offering_id=offering.id, class_id=seed_refs[name],
                ))
            session.commit()

        def get_session_override():
            with Session(test_engine) as s:
                yield s

        app.dependency_overrides[get_session] = get_session_override
        c = stack.enter_context(TestClient(app, cookies={}))
        resp = c.post("/api/v1/login", json={
            "username": username, "password": "scope123", "role": "teacher",
        })
        assert resp.status_code == 200, resp.json()
        return c

    yield _make
    stack.close()
    app.dependency_overrides.clear()


@pytest.fixture
def other_teacher_question(test_engine, make_teacher_client, seed_refs, seed_active_students):
    """别的老师（只关联三班）的问题 + 三班学生的匿名回答

    返回 (该教师客户端, question_id, answer_id)
    """
    from app.models.question import Answer

    other = make_teacher_client("scope_teacher_other", ("三班",))
    resp = other.post("/api/v1/teacher/questions", json={
        "content": "三班问题", "class_ids": [seed_refs["三班"]],
    })
    assert resp.status_code == 200, resp.json()
    qid = resp.json()["data"]["question_id"]

    with Session(test_engine) as session:
        answer = Answer(
            question_id=qid, student_id=seed_active_students["三班"],
            content="三班匿名回答", is_anonymous=True,
        )
        session.add(answer)
        session.commit()
        session.refresh(answer)
        aid = answer.id
    return other, qid, aid


# ---------- Q1：提问投放范围 ----------

def test_teacher_cannot_post_question_to_other_class(teacher_client: TestClient, seed_refs):
    """教师向别的班（三班）投放问题 → 403，且不落库"""
    resp = teacher_client.post("/api/v1/teacher/questions", json={
        "content": "越权问题", "class_ids": [seed_refs["三班"]],
    })
    assert resp.status_code == 403
    assert resp.json()["message"] == "无权操作该班级"
    assert teacher_client.get("/api/v1/teacher/questions").json()["data"] == []


def test_teacher_cannot_post_question_with_mixed_classes(teacher_client: TestClient, seed_refs):
    """列表里混入别的班 → 整体拒绝，不落库（部分合法也不行）"""
    resp = teacher_client.post("/api/v1/teacher/questions", json={
        "content": "混合问题", "class_ids": [seed_refs["一班"], seed_refs["三班"]],
    })
    assert resp.status_code == 403
    assert resp.json()["message"] == "无权操作该班级"
    assert teacher_client.get("/api/v1/teacher/questions").json()["data"] == []


def test_teacher_can_post_to_own_class(teacher_client: TestClient, seed_refs):
    """回归：自己关联的班级仍可投放"""
    resp = teacher_client.post("/api/v1/teacher/questions", json={
        "content": "本班问题", "class_ids": [seed_refs["一班"]],
    })
    assert resp.status_code == 200, resp.json()


def test_teacher_empty_class_ids_converges_to_own_classes(
    teacher_client: TestClient, seed_refs
):
    """教师空 class_ids → 收敛为自己可访问的班级，不再是「全校所有班级」"""
    resp = teacher_client.post("/api/v1/teacher/questions", json={"content": "通用问题"})
    assert resp.status_code == 200, resp.json()

    item = teacher_client.get("/api/v1/teacher/questions").json()["data"][0]
    assert sorted(item["class_ids"]) == sorted([seed_refs["一班"], seed_refs["二班"]])


def test_admin_empty_class_ids_still_means_all_classes(admin_client: TestClient):
    """回归：admin 空 class_ids 保持原语义（所有班级，不写关联行）"""
    resp = admin_client.post("/api/v1/teacher/questions", json={"content": "admin通用问题"})
    assert resp.status_code == 200, resp.json()

    item = admin_client.get("/api/v1/teacher/questions").json()["data"][0]
    assert item["class_ids"] == []
    assert item["class_name"] == "所有班级"


def test_admin_can_post_to_any_class(admin_client: TestClient, seed_refs):
    """回归：admin 不受班级归属限制"""
    resp = admin_client.post("/api/v1/teacher/questions", json={
        "content": "admin三班问题", "class_ids": [seed_refs["三班"]],
    })
    assert resp.status_code == 200, resp.json()


def test_teacher_without_linked_class_cannot_post(
    make_teacher_client, seed_refs
):
    """教学班未关联任何班级 → 空列表与显式列表都拒绝（fail-closed）"""
    c = make_teacher_client("scope_teacher_none", ())
    resp = c.post("/api/v1/teacher/questions", json={"content": "空列表问题"})
    assert resp.status_code == 403
    assert resp.json()["message"] == "您没有关联任何班级，无法发布问题"

    resp = c.post("/api/v1/teacher/questions", json={
        "content": "显式问题", "class_ids": [seed_refs["一班"]],
    })
    assert resp.status_code == 403


# ---------- Q2/Q3：回答管理（追问 / 标记优秀） ----------

def test_teacher_cannot_star_other_teachers_answer(
    teacher_client: TestClient, other_teacher_question, test_engine
):
    """标记别班问题下的回答 → 403，且未写入"""
    from app.models.question import Answer

    _, _, aid = other_teacher_question
    resp = teacher_client.put(f"/api/v1/teacher/answers/{aid}/star?starred=true")
    assert resp.status_code == 403
    assert resp.json()["message"] == "无权操作此问题"

    with Session(test_engine) as session:
        assert session.get(Answer, aid).is_starred is False


def test_teacher_cannot_reply_other_teachers_answer(
    teacher_client: TestClient, other_teacher_question, test_engine
):
    """追问别班问题下的回答 → 403，且未产生追问"""
    from app.models.question import Answer

    _, _, aid = other_teacher_question
    resp = teacher_client.post(f"/api/v1/teacher/answers/{aid}/reply", json={
        "answer_id": aid, "content": "越权追问",
    })
    assert resp.status_code == 403
    assert resp.json()["message"] == "无权操作此问题"

    with Session(test_engine) as session:
        assert len(session.exec(select(Answer)).all()) == 1


def test_owner_teacher_can_star_and_reply(
    teacher_client: TestClient, student_client: TestClient, seed_refs
):
    """回归：归属教师仍可追问并标记自己问题下的回答"""
    qid = teacher_client.post("/api/v1/teacher/questions", json={
        "content": "一班问题", "class_ids": [seed_refs["一班"]],
    }).json()["data"]["question_id"]
    aid = student_client.post("/api/v1/student/answers", json={
        "question_id": qid, "content": "学生回答",
    }).json()["data"]["answer_id"]

    assert teacher_client.post(f"/api/v1/teacher/answers/{aid}/reply", json={
        "answer_id": aid, "content": "老师追问",
    }).status_code == 200
    assert teacher_client.put(
        f"/api/v1/teacher/answers/{aid}/star?starred=true"
    ).status_code == 200


def test_admin_can_manage_any_answer(admin_client: TestClient, other_teacher_question):
    """admin 放行：可标记/追问任意问题下的回答"""
    _, _, aid = other_teacher_question
    assert admin_client.put(
        f"/api/v1/teacher/answers/{aid}/star?starred=true"
    ).status_code == 200
    assert admin_client.post(f"/api/v1/teacher/answers/{aid}/reply", json={
        "answer_id": aid, "content": "admin追问",
    }).status_code == 200


def test_star_missing_answer_404(teacher_client: TestClient):
    """不存在的回答仍是 404"""
    assert teacher_client.put(
        "/api/v1/teacher/answers/999999/star?starred=true"
    ).status_code == 404


# ---------- Q4：回答列表的去匿名化 ----------

def test_owner_teacher_sees_identity(
    other_teacher_question, seed_active_students
):
    """回归：归属教师本人仍能看到学号与姓名"""
    other, qid, _ = other_teacher_question
    data = other.get(f"/api/v1/student/questions/{qid}/answers").json()["data"]
    assert data[0]["student_id"] == seed_active_students["三班"]
    assert data[0]["student_name"] != "匿名"
    assert data[0]["student_name"] is not None


def test_admin_sees_identity(other_teacher_question, admin_client: TestClient):
    """admin 仍能看到学号与姓名"""
    _, qid, _ = other_teacher_question
    data = admin_client.get(f"/api/v1/student/questions/{qid}/answers").json()["data"]
    assert data[0]["student_id"] != ""
    assert data[0]["student_name"] != "匿名"


def test_foreign_teacher_cannot_deanonymize_answers(
    teacher_client: TestClient, other_teacher_question
):
    """别班教师读别班问题的回答 → 403（旧行为：200 + 学号 + 真实姓名）"""
    _, qid, _ = other_teacher_question
    resp = teacher_client.get(f"/api/v1/student/questions/{qid}/answers")
    assert resp.status_code == 403
    assert resp.json()["message"] == "无权查看该问题的回答"
    assert "范围学生" not in resp.text


def test_foreign_teacher_gets_anonymous_view_of_global_question(
    admin_client: TestClient, teacher_client: TestClient, test_engine, seed_active_students
):
    """全局问题（无班级关联）：别班教师只能拿到匿名视图"""
    from app.models.question import Answer

    qid = admin_client.post("/api/v1/teacher/questions", json={
        "content": "全局问题",
    }).json()["data"]["question_id"]
    with Session(test_engine) as session:
        answer = Answer(question_id=qid, student_id=seed_active_students["三班"],
                        content="全局匿名回答", is_anonymous=True)
        session.add(answer)
        session.commit()

    data = teacher_client.get(f"/api/v1/student/questions/{qid}/answers").json()["data"]
    assert data[0]["student_id"] == ""
    assert data[0]["student_name"] == "匿名"


def test_student_cannot_read_answers_of_other_class_question(
    student_client: TestClient, other_teacher_question
):
    """一班学生读三班问题的回答 → 403（新增可见性校验）"""
    _, qid, _ = other_teacher_question
    resp = student_client.get(f"/api/v1/student/questions/{qid}/answers")
    assert resp.status_code == 403
    assert resp.json()["message"] == "无权查看该问题的回答"


def test_student_can_read_answers_of_own_class_question(
    student_client: TestClient, teacher_client: TestClient, seed_refs
):
    """回归：本班问题仍可读，学生视图不返回他人学号，自己的匿名回答能看到自己"""
    qid = teacher_client.post("/api/v1/teacher/questions", json={
        "content": "一班问题", "class_ids": [seed_refs["一班"]],
    }).json()["data"]["question_id"]
    student_client.post("/api/v1/student/answers", json={
        "question_id": qid, "content": "我的匿名回答", "is_anonymous": True,
    })

    data = student_client.get(f"/api/v1/student/questions/{qid}/answers").json()["data"]
    assert len(data) == 1
    assert data[0]["student_id"] == ""
    assert data[0]["student_name"] is not None


def test_student_can_read_global_question_answers(
    student_client: TestClient, admin_client: TestClient
):
    """回归：全局问题对所有班学生可见"""
    qid = admin_client.post("/api/v1/teacher/questions", json={
        "content": "全局问题",
    }).json()["data"]["question_id"]
    resp = student_client.get(f"/api/v1/student/questions/{qid}/answers")
    assert resp.status_code == 200, resp.json()
    assert resp.json()["data"] == []


def test_answers_of_missing_question_404(student_client: TestClient):
    """问题不存在仍是 404"""
    assert student_client.get(
        "/api/v1/student/questions/999999/answers"
    ).status_code == 404


# ---------- Q5：提交回答必须先对该问题可见（写侧，与 Q4 读侧对齐）----------

def test_student_cannot_answer_other_class_question(
    student_client: TestClient, other_teacher_question, test_engine
):
    """一班学生给「仅三班可见」的问题提交回答 → 403，且不落库

    与 Q4 对齐：此前可以提交、提交后自己又读不到（403），前后矛盾且污染别班问答板。
    """
    from app.models.question import Answer

    _, qid, _ = other_teacher_question
    resp = student_client.post("/api/v1/student/answers", json={
        "question_id": qid, "content": "越权回答",
    })
    assert resp.status_code == 403, resp.json()

    with Session(test_engine) as session:
        leaked = session.exec(select(Answer).where(
            Answer.question_id == qid,
            Answer.content == "越权回答",
        )).all()
    assert leaked == [], "越权回答不应落库"


def test_student_can_answer_own_class_question(
    student_client: TestClient, teacher_client: TestClient, seed_refs
):
    """回归：本班问题正常可答（不能误伤正常学生）"""
    qid = teacher_client.post("/api/v1/teacher/questions", json={
        "content": "一班问题", "class_ids": [seed_refs["一班"]],
    }).json()["data"]["question_id"]

    resp = student_client.post("/api/v1/student/answers", json={
        "question_id": qid, "content": "我的回答",
    })
    assert resp.status_code == 200, resp.json()
    assert resp.json()["data"]["answer_id"] > 0


def test_student_can_answer_global_question(
    student_client: TestClient, admin_client: TestClient
):
    """回归：全局问题（无关联行=所有班级可见）仍可回答"""
    qid = admin_client.post("/api/v1/teacher/questions", json={
        "content": "全局问题",
    }).json()["data"]["question_id"]

    resp = student_client.post("/api/v1/student/answers", json={
        "question_id": qid, "content": "全局回答",
    })
    assert resp.status_code == 200, resp.json()
