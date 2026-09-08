"""
问答 CRUD 单元测试
"""
import pytest
from sqlmodel import Session
from app.crud.question import (
    create_question, get_question, get_questions_by_teacher,
    get_questions_by_class, close_question, count_answers,
    create_answer, get_answers_by_question, update_answer,
    star_answer, delete_answer,
)


@pytest.fixture(autouse=True)
def _seed_teacher(session):
    """PG 强制 FK：questions.teacher_id → users.id，SQLite 时代无需此依赖"""
    from app.models import User
    from app.core.security import hash_password
    session.add_all([
        User(id=1, username="teacher1", name="教师1",
             password_hash=hash_password("pass123"), role="teacher"),
        User(id=2, username="teacher2", name="教师2",
             password_hash=hash_password("pass123"), role="teacher"),
    ])
    session.commit()


class TestQuestionCRUD:
    """测试问题 CRUD"""

    def test_create_question(self, session: Session):
        q = create_question(
            session, teacher_id=1, content="什么是Python？",
            class_name="软件1班", is_realtime=True,
        )
        assert q.teacher_id == 1
        assert q.content == "什么是Python？"
        assert q.class_name == "软件1班"
        assert q.status == "active"
        assert q.is_realtime is True

    def test_create_question_all_classes(self, session: Session):
        q = create_question(session, teacher_id=1, content="通用问题")
        assert q.class_name is None

    def test_get_questions_by_teacher(self, session: Session):
        create_question(session, teacher_id=1, content="Q1", class_name="软件1班")
        create_question(session, teacher_id=1, content="Q2", class_name="软件2班")
        create_question(session, teacher_id=2, content="Q3", class_name="软件1班")

        questions = get_questions_by_teacher(session, teacher_id=1)
        assert len(questions) == 2

    def test_get_questions_by_teacher_with_filter(self, session: Session):
        create_question(session, teacher_id=1, content="Q1", class_name="软件1班")
        q2 = create_question(session, teacher_id=1, content="Q2", class_name="软件1班")
        close_question(session, q2.id)

        active = get_questions_by_teacher(session, teacher_id=1, status="active")
        assert len(active) == 1
        assert active[0].content == "Q1"

    def test_get_questions_by_class(self, session: Session):
        create_question(session, teacher_id=1, content="班级问题", class_name="软件1班")
        create_question(session, teacher_id=1, content="通用问题")
        create_question(session, teacher_id=1, content="其他班级", class_name="软件2班")

        questions = get_questions_by_class(session, "软件1班")
        assert len(questions) == 2
        contents = {q.content for q in questions}
        assert "班级问题" in contents
        assert "通用问题" in contents
        assert "其他班级" not in contents

    def test_close_question(self, session: Session):
        q = create_question(session, teacher_id=1, content="Q1")
        assert q.status == "active"

        closed = close_question(session, q.id)
        assert closed.status == "closed"
        assert closed.closed_at is not None

    def test_count_answers(self, session: Session):
        q = create_question(session, teacher_id=1, content="Q1")
        assert count_answers(session, q.id) == 0

        create_answer(session, q.id, student_id="S001", content="A1")
        assert count_answers(session, q.id) == 1


class TestAnswerCRUD:
    """测试回答 CRUD"""

    def test_create_answer(self, session: Session):
        q = create_question(session, teacher_id=1, content="Q1")
        a = create_answer(session, q.id, student_id="S001", content="回答1", is_anonymous=True)
        assert a.question_id == q.id
        assert a.student_id == "S001"
        assert a.content == "回答1"
        assert a.is_anonymous is True
        assert a.parent_id is None

    def test_create_reply(self, session: Session):
        q = create_question(session, teacher_id=1, content="Q1")
        parent = create_answer(session, q.id, student_id="S001", content="回答1")
        reply = create_answer(session, q.id, student_id="S001", content="追问1", parent_id=parent.id)
        assert reply.parent_id == parent.id

    def test_get_answers_ordering(self, session: Session):
        q = create_question(session, teacher_id=1, content="Q1")
        a1 = create_answer(session, q.id, student_id="S001", content="A1")
        a2 = create_answer(session, q.id, student_id="S002", content="A2")
        r1 = create_answer(session, q.id, student_id="S001", content="R1", parent_id=a1.id)

        answers = get_answers_by_question(session, q.id)
        assert len(answers) == 3
        assert answers[0].id == a1.id
        assert answers[1].id == r1.id
        assert answers[2].id == a2.id

    def test_update_answer(self, session: Session):
        q = create_question(session, teacher_id=1, content="Q1")
        a = create_answer(session, q.id, student_id="S001", content="原始内容")
        updated = update_answer(session, a.id, "修改后内容")
        assert updated.content == "修改后内容"

    def test_star_answer(self, session: Session):
        q = create_question(session, teacher_id=1, content="Q1")
        a = create_answer(session, q.id, student_id="S001", content="A1")
        assert a.is_starred is False

        starred = star_answer(session, a.id, True)
        assert starred.is_starred is True

        unstarred = star_answer(session, a.id, False)
        assert unstarred.is_starred is False

    def test_delete_answer_with_replies(self, session: Session):
        q = create_question(session, teacher_id=1, content="Q1")
        a = create_answer(session, q.id, student_id="S001", content="A1")
        create_answer(session, q.id, student_id="S001", content="R1", parent_id=a.id)

        assert delete_answer(session, a.id) is True
        answers = get_answers_by_question(session, q.id)
        assert len(answers) == 0
