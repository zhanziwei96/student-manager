"""semester 字段测试：学期标识已由字符串列改为 semester_id 外键（FK 锚点）

旧机制（模型构造时自动填充当前学期字符串）已随 schema 重构删除，本文件改为
验证：字符串列已移除、显式 semester_id 赋值保留、必填 FK 缺失即报错。
"""
from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.models import (
    CheckinRecord, CourseSchedule, CourseSession, Group,
    ScheduleAdjustment, Semester, Student,
)
from app.models.student import StudentResponse
from app.models.question import Question

# 已删除 semester 字符串列的业务表（改用 semester_id FK 锚定）
BUSINESS_MODELS = (CourseSchedule, CourseSession, ScheduleAdjustment,
                   CheckinRecord, Group, Question)


@pytest.mark.parametrize("model", BUSINESS_MODELS, ids=lambda m: m.__name__)
def test_semester_string_column_removed(model):
    """业务表不再有 semester 字符串列（学期只以 semester_id 锚定）"""
    assert "semester" not in model.model_fields


def test_retained_snapshot_columns_keep_defaults():
    """保留列不受影响：students.class_id 可空（未分班），class_name 改为响应层运行时解析"""
    student = Student(student_id="TEST001", name="测试学生")
    assert student.class_id is None
    assert StudentResponse.model_fields["class_name"].default is None


def test_group_requires_semester_id(session: Session, seed_refs):
    """Group 的 class_id / semester_id 必填（纯 FK 锚点）：缺一列即被 NOT NULL 拒绝"""
    assert Group.model_fields["class_id"].is_required() is True
    assert Group.model_fields["semester_id"].is_required() is True

    session.add(Group(name="缺学期组", leader_student_id="TEST001",
                      class_id=seed_refs["一班"]))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

    group = Group(class_id=seed_refs["一班"], semester_id=seed_refs["semester_id"],
                  name="第一组", leader_student_id="TEST001")
    assert group.class_id == seed_refs["一班"]
    assert group.semester_id == seed_refs["semester_id"]


def test_checkin_and_question_semester_id_are_optional():
    """checkins/questions 的 FK 可空（历史签到、面向全班的提问）"""
    checkin = CheckinRecord(student_id="TEST001")
    assert checkin.semester_id is None
    assert checkin.class_id is None

    question = Question(teacher_id=1, content="今天讲了什么？")
    assert question.semester_id is None
    assert question.class_id is None


def test_explicit_semester_id_preserved(session: Session, seed_refs):
    """显式指定 semester_id 时保留指定值（不因当前学期被改写）"""
    refs = seed_refs
    sched = CourseSchedule(course_name="数学", class_id=refs["一班"],
                           semester_id=refs["semester_id"], day_of_week=1,
                           start_time="08:00", end_time="09:40")
    assert sched.semester_id == refs["semester_id"]

    session.add(sched)
    session.commit()
    session.refresh(sched)
    assert sched.semester_id == refs["semester_id"]


def test_explicit_archived_semester_id_preserved(session: Session, seed_refs):
    """显式指定非当前学期时保留该 FK（归档脚本回填历史数据用）"""
    refs = seed_refs
    old_sem = Semester(label="2025-2026-2", start_date=date(2026, 2, 23),
                       total_weeks=20, is_current=False)
    session.add(old_sem)
    session.commit()
    session.refresh(old_sem)

    sess = CourseSession(session_code="TEST001", class_id=refs["一班"],
                         semester_id=old_sem.id, teacher_id=1)
    assert sess.semester_id == old_sem.id

    session.add(sess)
    session.commit()
    session.refresh(sess)
    assert sess.semester_id == old_sem.id
