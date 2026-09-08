"""
核心实体初始化脚本 - semesters / cohorts / 课程线（幂等可重跑）

用法:
    cd backend
    DATABASE__URL="postgresql+psycopg2://..." python scripts/seed_core_entities.py

流程:
    1. upsert semesters 当前学期行（label 冲突则跳过，is_current=true）
    2. upsert cohorts 当前届行（year=学期 label 前 4 位），绑定 entry_semester_id
    3. 课程线回填（仅当前学期，历史学期数据保留旧字段）：
       - courses：subjects.name ∪ course_schedules.course_name 去重推导，code 生成 C<id>
       - course_offerings：当前学期课表按 (课程, 教师) 推导，class_scope 聚合班名
       - enrollments：当前学期 student_subject_scores 迁移（score/version 继承）
       - student_class_semesters：students.class_id 非空者写入当前学期归属
       - groups.course_id：subject_id → subjects.name → courses.name 桥接
"""
import os
import sys

# 保证以 backend 为工作目录运行时能 import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Session, select

from app.core.config import get_settings
from app.core.db import engine
from app.models import (
    Cohort, Course, CourseOffering, Enrollment, Group, Semester,
    Student, StudentClassSemester, StudentSubjectScore, Subject,
)


def seed_semesters_and_cohorts(session: Session, term_label: str) -> Semester:
    """upsert 当前学期与当前届，返回当前学期行"""
    settings = get_settings()
    term = settings.term
    cohort_year = term_label.split("-")[0]

    session.execute(
        insert(Semester).values(
            label=term.label,
            start_date=term.start_date,
            total_weeks=term.total_weeks,
            is_current=True,
            status="active",
        ).on_conflict_do_nothing(index_elements=["label"])
    )
    session.commit()

    sem = session.exec(select(Semester).where(Semester.label == term.label)).first()
    if sem is None:
        raise RuntimeError(f"学期 {term.label} 未写入 semesters 表")

    session.execute(
        insert(Cohort).values(
            year=cohort_year,
            label=f"{cohort_year}届",
            entry_semester_id=sem.id,
            status="active",
        ).on_conflict_do_nothing(index_elements=["year"])
    )
    session.commit()
    return sem


def backfill_courses(session: Session) -> None:
    """courses 回填：subjects ∪ 课表课程名去重推导，code 生成 C<id>（存在则跳过）"""
    names = session.exec(text("""
        SELECT name FROM (
            SELECT DISTINCT name FROM subjects
            UNION
            SELECT DISTINCT course_name FROM course_schedules
        ) src
        ORDER BY name
    """)).all()

    for (name,) in names:
        exists = session.exec(select(Course).where(Course.name == name)).first()
        if exists:
            continue
        course = Course(code="", name=name)
        session.add(course)
        session.flush()
        course.code = f"C{course.id}"
        session.commit()


def backfill_offerings(session: Session, sem: Semester, term_label: str) -> None:
    """offerings 回填（仅当前学期）：课表按 (课程, 教师) 分组推导，class_scope 聚合班名"""
    rows = session.exec(text("""
        SELECT course_name, teacher_id, teacher_name,
               string_agg(DISTINCT class_name, ', ' ORDER BY class_name) AS scope
        FROM course_schedules
        WHERE semester = :t
        GROUP BY course_name, teacher_id, teacher_name
    """), params={"t": term_label}).all()

    for course_name, teacher_id, teacher_name, scope in rows:
        course = session.exec(select(Course).where(Course.name == course_name)).first()
        if course is None:
            continue
        exists = session.exec(select(CourseOffering).where(
            CourseOffering.course_id == course.id,
            CourseOffering.semester_id == sem.id,
            CourseOffering.teacher_id == teacher_id,
            CourseOffering.class_scope == scope,
        )).first()
        if exists:
            continue
        session.add(CourseOffering(
            course_id=course.id,
            semester_id=sem.id,
            teacher_id=teacher_id,
            teacher_name=teacher_name or "",
            class_scope=scope,
        ))
    session.commit()


def backfill_enrollments(session: Session, sem: Semester, term_label: str) -> None:
    """enrollments 回填（仅当前学期）：student_subject_scores 迁移，score/version 继承"""
    scores = session.exec(
        select(StudentSubjectScore).where(StudentSubjectScore.semester == term_label)
    ).all()

    for sss in scores:
        subject = session.get(Subject, sss.subject_id)
        if subject is None:
            continue
        course = session.exec(select(Course).where(Course.name == subject.name)).first()
        if course is None:
            continue

        # 匹配教学班：优先 class_scope 包含学生班名，退化取该教师首个教学班
        student = session.get(Student, sss.student_id)
        offering = None
        candidates = session.exec(select(CourseOffering).where(
            CourseOffering.course_id == course.id,
            CourseOffering.semester_id == sem.id,
            CourseOffering.teacher_id == sss.teacher_id,
        )).all()
        if student is not None:
            offering = next(
                (o for o in candidates if student.class_name in o.class_scope), None
            )
        if offering is None and candidates:
            offering = candidates[0]
        if offering is None:
            continue

        exists = session.exec(select(Enrollment).where(
            Enrollment.student_id == sss.student_id,
            Enrollment.offering_id == offering.id,
        )).first()
        if exists:
            continue
        session.add(Enrollment(
            student_id=sss.student_id,
            offering_id=offering.id,
            semester_id=sem.id,
            status="enrolled",
            score=sss.score,
            version=sss.version,
        ))
    session.commit()


def backfill_student_class_semesters(session: Session, sem: Semester) -> None:
    """学生行政班归属回填：students.class_id 非空者写入当前学期（冲突跳过）"""
    session.execute(text("""
        INSERT INTO student_class_semesters (student_id, class_id, semester_id, created_at)
        SELECT student_id, class_id, :sem_id, now()
        FROM students
        WHERE class_id IS NOT NULL
        ON CONFLICT (student_id, semester_id) DO NOTHING
    """), {"sem_id": sem.id})
    session.commit()


def backfill_group_course_id(session: Session, term_label: str) -> None:
    """groups.course_id 回填：subject_id → subjects.name → courses.name（仅当前学期）"""
    session.execute(text("""
        UPDATE groups g
        SET course_id = c.id
        FROM subjects s
        JOIN courses c ON c.name = s.name
        WHERE g.subject_id = s.id
          AND g.course_id IS NULL
          AND g.semester = :t
    """), {"t": term_label})
    session.commit()


def backfill_business_table_fks(session: Session, sem: Semester, term_label: str) -> None:
    """业务表 FK 回填（仅当前学期，幂等：WHERE FK 列为 NULL）

    - 带班名+学期的表：semester_id=当前学期，class_id 按 (class_name, 当前学年届) 匹配
    - 仅学期的表：semester_id=当前学期
    - audit_logs（无 semester 列）：按 created_at >= 学期开始日期近似回填
    - class_group_settings：从 classes 派生当前学期默认设置
    """
    cohort_year = term_label.split("-")[0]

    class_tables = [
        'course_schedules', 'course_sessions', 'checkin_records', 'groups', 'questions',
    ]
    for table in class_tables:
        session.execute(text(f"""
            UPDATE {table} t
            SET semester_id = :sid,
                class_id = c.id
            FROM classes c
            WHERE t.semester = :label
              AND t.class_name = c.name
              AND c.cohort_year = :cohort
              AND t.semester_id IS NULL
        """), {"sid": sem.id, "label": term_label, "cohort": cohort_year})

    semester_tables = ['score_logs', 'schedule_adjustments', 'group_score_logs']
    for table in semester_tables:
        session.execute(text(f"""
            UPDATE {table}
            SET semester_id = :sid
            WHERE semester = :label AND semester_id IS NULL
        """), {"sid": sem.id, "label": term_label})

    # audit_logs 无 semester 列：按学期开始日期近似回填
    session.execute(text("""
        UPDATE audit_logs
        SET semester_id = :sid
        WHERE semester_id IS NULL AND created_at >= :start
    """), {"sid": sem.id, "start": sem.start_date})

    # class_group_settings：每个班级一条当前学期默认设置
    # （主键仍是 class_name 过渡期，Phase 2 切换复合主键后改冲突目标）
    session.execute(text("""
        INSERT INTO class_group_settings (class_id, semester_id, class_name,
                                          max_members_per_group, updated_at)
        SELECT id, :sid, name, 5, now()
        FROM classes
        ON CONFLICT (class_name) DO NOTHING
    """), {"sid": sem.id})
    session.commit()


def main() -> None:
    settings = get_settings()
    term_label = settings.term.label

    with Session(engine) as session:
        sem = seed_semesters_and_cohorts(session, term_label)
        backfill_courses(session)
        backfill_offerings(session, sem, term_label)
        backfill_enrollments(session, sem, term_label)
        backfill_student_class_semesters(session, sem)
        backfill_group_course_id(session, term_label)
        backfill_business_table_fks(session, sem, term_label)

        counts = {
            "semesters": len(session.exec(select(Semester)).all()),
            "cohorts": len(session.exec(select(Cohort)).all()),
            "courses": len(session.exec(select(Course)).all()),
            "offerings": len(session.exec(select(CourseOffering)).all()),
            "enrollments": len(session.exec(select(Enrollment)).all()),
            "scs": len(session.exec(select(StudentClassSemester)).all()),
            "groups_with_course": len(session.exec(
                select(Group).where(Group.course_id.is_not(None))
            ).all()),
        }
        print("种子数据就绪:", ", ".join(f"{k}={v}" for k, v in counts.items()))


if __name__ == "__main__":
    main()
