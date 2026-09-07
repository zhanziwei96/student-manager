"""
老师班级管理 API - 老师自己决定教哪些班级
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.core.db import get_session
from app.core.config import HttpStatus
from app.api.deps import get_current_user
from app.crud import get_all_classes
from app.models import User
from app.models.constants import ApiResponseConst, ApiResponse, ApiSuccessResponse

router = APIRouter(tags=["teacher-classes"])


class UpdateTeacherClassesRequest(BaseModel):
    """老师更新自己班级的请求"""
    class_names: List[str] = Field(..., description="班级名称列表")


@router.get("/teacher/classes", response_model=ApiResponse[List[str]])
def get_teacher_classes(
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    """获取当前老师教的班级列表（管理员看全部，教师看自己负责的）"""
    role = user.get("role", "")
    if role not in ("admin", "teacher"):
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="需要教师权限")

    if role == "admin":
        # 管理员看全部启用班级
        class_names = get_all_classes(session)
    else:
        # 教师看自己负责的班级
        user_id = user.get("sub")
        user_obj = session.get(User, int(user_id)) if user_id else None
        class_names = user_obj.get_assigned_classes() if user_obj else []

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: class_names,
    }


@router.put("/teacher/classes", response_model=ApiSuccessResponse)
def update_teacher_classes(
    data: UpdateTeacherClassesRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    """老师更新自己教的班级列表（添加/移除）"""
    role = user.get("role", "")
    if role != "teacher":
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="仅教师可管理自己的班级")

    user_id = user.get("sub")
    if not user_id:
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="无效的用户信息")

    user_obj = session.get(User, int(user_id))
    if not user_obj:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="教师不存在")

    user_obj.set_assigned_classes(data.class_names)
    session.add(user_obj)
    session.commit()

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: "班级列表已更新",
    }
