"""
成绩排行榜 API — 教师 4 榜（个人/小组 × 班内/跨班）+ 学生本班科目榜
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.api.deps import get_teacher_accessible_classes, verify_teacher_class_access
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
    class_id: Optional[int] = Query(None, description="行政班ID（教师 scope=class 时）"),
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    """成绩排行榜

    教师：可查自己授课科目的个人/小组榜，且结果**收敛到本人可访问的行政班**
    （class_id 传入时校验归属；未传入时按可访问班级集合过滤，集合为空即空榜）。
    学生：只能查本班（class_id 强制取学生自己的行政班，scope 强制 class）。
    admin：不限。
    """
    role = user.get("role", "")
    course = session.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="课程不存在")

    # 班级范围：None = 不额外限制（admin/学生沿用旧语义）；序列 = 只允许这些班级（空集=空榜）
    allowed_class_ids: Optional[list] = None

    if role == "teacher":
        offering = session.exec(select(CourseOffering).where(
            CourseOffering.course_id == course_id,
            CourseOffering.teacher_id == int(user.get("sub")),
        ).limit(1)).first()
        if offering is None:
            raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="只能查看自己授课科目的排行榜")
        if class_id is not None:
            # 指定班级必须属于本人可访问班级（fail-closed → 403）
            verify_teacher_class_access(user, class_id, session)
            allowed_class_ids = [class_id]
        else:
            # scope=all（或不带 class_id）：收敛到本人可访问班级集合，
            # 否则可读到同科目其他教师教学班的学生/小组数据
            allowed_class_ids = get_teacher_accessible_classes(user, session) or []
    elif role == "student":
        student = session.get(Student, user.get("sub"))
        if student is None:
            raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="学生不存在")
        scope = "class"  # 学生只能看班内榜
        class_id = student.class_id
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
        entries = get_individual_ranking(session, course_id, scope, class_id, semester_id,
                                         class_ids=allowed_class_ids)
    else:
        entries = get_group_ranking(session, course_id, scope, class_id, semester_id,
                                    class_ids=allowed_class_ids)

    # 教师 scope=class 时的班级下拉选项：该科目名单中的行政班（展示名）
    if role == "teacher":
        classes = sorted({e["class_name"] for e in entries if e.get("class_name")})
    else:
        from app.core.class_cache import get_class_display_name_by_id
        my_class_name = get_class_display_name_by_id(session, class_id)
        classes = [my_class_name] if my_class_name else []

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
