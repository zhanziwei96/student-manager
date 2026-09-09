"""
成绩排行榜 API — 教师 4 榜（个人/小组 × 班内/跨班）+ 学生本班科目榜
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.core.config import HttpStatus
from app.core.db import get_session
from app.core.jwt import get_current_user
from app.core.term import get_current_semester_id
from app.crud.ranking import get_group_ranking, get_individual_ranking
from app.models import Course, CourseOffering, Enrollment, Student
from app.models.constants import ApiResponseConst, ApiResponse

router = APIRouter(tags=["rankings"])


@router.get("/rankings", response_model=ApiResponse[dict])
def get_rankings(
    type: str = Query(..., pattern="^(individual|group)$", description="个人/小组"),
    course_id: int = Query(..., description="课程ID（科目）"),
    scope: str = Query("class", pattern="^(class|all)$", description="班内/跨班"),
    class_name: Optional[str] = Query(None, description="行政班名（教师 scope=class 时）"),
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    """成绩排行榜

    教师：可查自己授课科目的个人/小组榜；scope=class 需指定行政班。
    学生：只能查本班（class_name 强制取学生自己的行政班，scope 强制 class）。
    """
    role = user.get("role", "")
    course = session.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="课程不存在")

    if role == "teacher":
        offering = session.exec(select(CourseOffering).where(
            CourseOffering.course_id == course_id,
            CourseOffering.teacher_id == int(user.get("sub")),
        ).limit(1)).first()
        if offering is None:
            raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="只能查看自己授课科目的排行榜")
    elif role == "student":
        student = session.get(Student, user.get("sub"))
        if student is None:
            raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="学生不存在")
        scope = "class"  # 学生只能看班内榜
        class_name = student.class_name
        # 学生只能看自己选过的课
        enrolled = session.exec(select(Enrollment).join(CourseOffering).where(
            Enrollment.student_id == student.student_id,
            CourseOffering.course_id == course_id,
        ).limit(1)).first()
        if enrolled is None:
            raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="只能查看自己已选课程的排行榜")

    semester_id = get_current_semester_id(session)
    if semester_id is None:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="当前学期未设置")

    if type == "individual":
        entries = get_individual_ranking(session, course_id, scope, class_name, semester_id)
    else:
        entries = get_group_ranking(session, course_id, scope, class_name, semester_id)

    # 教师 scope=class 时的班级下拉选项：该科目名单中的行政班
    if role == "teacher":
        classes = sorted({e["class_name"] for e in entries})
    else:
        classes = [class_name] if class_name else []

    my_rank = None
    if role == "student" and type == "individual":
        my_rank = next((e for e in entries if e["student_id"] == user.get("sub")), None)

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {
            "type": type, "scope": scope, "course_name": course.name,
            "classes": classes, "entries": entries, "my_rank": my_rank,
        },
    }
