"""
失物招领 API
"""
import os
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File, Form
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.core.db import get_session
from app.core.jwt import get_current_user
from app.core.config import get_settings
from app.api.deps import require_admin_or_teacher
from app.crud.lost_found import (
    create_lost_found_item, get_lost_found_item, get_lost_found_items,
    update_lost_found_item, delete_lost_found_item,
    create_comment, get_comments_by_item,
    create_claim, get_claims_by_item, get_claim, get_student_claim,
    confirm_claim, reject_claim, count_claims_by_status,
    DuplicateClaimError, ItemNotClaimableError,
)
from app.crud.user import get_user
from app.crud.student import get_student
from app.core.upload import save_upload_file_securely

router = APIRouter(tags=["lost-found"])


# ============== 请求/响应模型 ==============

class CreateCommentRequest(BaseModel):
    content: str = Field(..., description="评论内容")


class CreateClaimRequest(BaseModel):
    contact: str = Field(..., max_length=200, description="联系方式")
    message: Optional[str] = Field(default=None, description="认领说明")


# ============== 辅助函数 ==============

def _format_datetime(dt) -> str:
    """格式化日期时间"""
    return dt.isoformat() if dt else ""


def _get_user_name(session: Session, user_id: int) -> Optional[str]:
    """获取用户真实姓名：优先从学生表获取，否则使用用户名"""
    user = get_user(session, user_id)
    if user:
        student = get_student(session, str(user_id))
        if student:
            return student.name
        return user.username
    return None


async def _save_image(file: UploadFile) -> Optional[str]:
    """保存图片并返回URL路径"""
    if not file:
        return None
    settings = get_settings()
    file_path, _ = await save_upload_file_securely(
        file,
        allowed_extensions=[".jpg", ".jpeg", ".png", ".gif", ".webp"],
        allowed_content_types=["image/jpeg", "image/png", "image/gif", "image/webp"],
        max_size_mb=5,
        use_uuid=True,
        upload_directory=os.path.join(settings.upload.directory, "lost-found"),
    )
    return f"/uploads/lost-found/{os.path.basename(file_path)}"


# ============== 教师端路由 ==============

@router.post("/teacher/lost-found")
async def teacher_create_item(
    request: Request,
    title: str = Form(..., description="物品名称"),
    description: str = Form(..., description="详细描述"),
    location: Optional[str] = Form(default=None, description="丢失/拾获地点"),
    image: Optional[UploadFile] = File(default=None, description="物品图片"),
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher),
):
    """教师发布失物招领"""
    teacher_id = int(user["sub"])

    image_url = None
    if image:
        image_url = await _save_image(image)

    item = create_lost_found_item(
        session,
        publisher_id=teacher_id,
        title=title,
        description=description,
        location=location,
        image_url=image_url,
    )
    return {"success": True, "data": {"id": item.id}}


@router.get("/teacher/lost-found")
async def teacher_list_items(
    request: Request,
    keyword: Optional[str] = Query(default=None, description="搜索关键词"),
    status: Optional[str] = Query(default=None, description="状态过滤"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher),
):
    """教师获取失物招领列表（含认领统计）"""
    items, total = get_lost_found_items(session, keyword, status, page, page_size)

    result = []
    for item in items:
        publisher_name = _get_user_name(session, item.publisher_id)
        pending_count = count_claims_by_status(session, item.id, "pending")
        confirmed_count = count_claims_by_status(session, item.id, "confirmed")

        result.append({
            "id": item.id,
            "title": item.title,
            "description": item.description,
            "location": item.location,
            "image_url": item.image_url,
            "status": item.status,
            "publisher_id": item.publisher_id,
            "publisher_name": publisher_name,
            "pending_claims": pending_count,
            "confirmed_claims": confirmed_count,
            "created_at": _format_datetime(item.created_at),
            "updated_at": _format_datetime(item.updated_at),
        })

    return {
        "success": True,
        "data": {
            "items": result,
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.get("/teacher/lost-found/{item_id}")
async def teacher_get_item(
    request: Request,
    item_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher),
):
    """教师获取物品详情（含真实姓名、联系方式、所有认领记录）"""
    item = get_lost_found_item(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="物品不存在")

    publisher_name = _get_user_name(session, item.publisher_id)

    # 获取评论（教师端显示真实姓名）
    comments = get_comments_by_item(session, item_id)
    comment_list = []
    for c in comments:
        user_name = _get_user_name(session, c.user_id)
        comment_list.append({
            "id": c.id,
            "item_id": c.item_id,
            "user_id": c.user_id,
            "user_name": user_name,
            "content": c.content,
            "created_at": _format_datetime(c.created_at),
        })

    # 获取所有认领记录（教师端完整信息）
    claims = get_claims_by_item(session, item_id)
    claim_list = []
    for claim in claims:
        student_name = _get_user_name(session, claim.student_id)
        claim_list.append({
            "id": claim.id,
            "item_id": claim.item_id,
            "student_id": claim.student_id,
            "student_name": student_name,
            "contact": claim.contact,
            "message": claim.message,
            "status": claim.status,
            "created_at": _format_datetime(claim.created_at),
        })

    return {
        "success": True,
        "data": {
            "id": item.id,
            "title": item.title,
            "description": item.description,
            "location": item.location,
            "image_url": item.image_url,
            "status": item.status,
            "publisher_id": item.publisher_id,
            "publisher_name": publisher_name,
            "comments": comment_list,
            "claims": claim_list,
            "created_at": _format_datetime(item.created_at),
            "updated_at": _format_datetime(item.updated_at),
        },
    }


@router.put("/teacher/lost-found/{item_id}")
async def teacher_update_item(
    request: Request,
    item_id: int,
    title: Optional[str] = Form(default=None, description="物品名称"),
    description: Optional[str] = Form(default=None, description="详细描述"),
    location: Optional[str] = Form(default=None, description="丢失/拾获地点"),
    image: Optional[UploadFile] = File(default=None, description="物品图片"),
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher),
):
    """教师编辑失物招领"""
    item = get_lost_found_item(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="物品不存在")

    image_url = None
    if image:
        image_url = await _save_image(image)

    updated = update_lost_found_item(
        session,
        item_id,
        title=title,
        description=description,
        location=location,
        image_url=image_url,
    )
    return {"success": True, "data": {"item_id": updated.id}}


@router.delete("/teacher/lost-found/{item_id}")
async def teacher_delete_item(
    request: Request,
    item_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher),
):
    """教师删除失物招领"""
    item = get_lost_found_item(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="物品不存在")

    delete_lost_found_item(session, item_id)
    return {"success": True}


@router.put("/teacher/lost-found/{item_id}/claims/{claim_id}/confirm")
async def teacher_confirm_claim(
    request: Request,
    item_id: int,
    claim_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher),
):
    """教师确认认领"""
    item = get_lost_found_item(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="物品不存在")

    claim = confirm_claim(session, item_id, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="认领记录不存在")

    return {"success": True}


@router.put("/teacher/lost-found/{item_id}/claims/{claim_id}/reject")
async def teacher_reject_claim(
    request: Request,
    item_id: int,
    claim_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher),
):
    """教师拒绝认领"""
    item = get_lost_found_item(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="物品不存在")

    claim = reject_claim(session, item_id, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="认领记录不存在")

    return {"success": True}


# ============== 学生端路由 ==============

@router.get("/student/lost-found")
async def student_list_items(
    request: Request,
    keyword: Optional[str] = Query(default=None, description="搜索关键词"),
    status: Optional[str] = Query(default=None, description="状态过滤"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    """学生浏览失物招领列表"""
    items, total = get_lost_found_items(session, keyword, status, page, page_size)

    result = []
    for item in items:
        result.append({
            "id": item.id,
            "title": item.title,
            "description": item.description,
            "location": item.location,
            "image_url": item.image_url,
            "status": item.status,
            "created_at": _format_datetime(item.created_at),
        })

    return {
        "success": True,
        "data": {
            "items": result,
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.get("/student/lost-found/{item_id}")
async def student_get_item(
    request: Request,
    item_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    """学生获取物品详情（匿名评论，仅显示自己的认领状态）"""
    item = get_lost_found_item(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="物品不存在")

    student_id = int(user["sub"])

    # 获取评论（学生端匿名显示）
    comments = get_comments_by_item(session, item_id)
    comment_list = []
    for c in comments:
        comment_list.append({
            "id": c.id,
            "item_id": c.item_id,
            "user_id": 0,  # 隐藏真实用户ID
            "user_name": "匿名用户",
            "content": c.content,
            "created_at": _format_datetime(c.created_at),
        })

    # 仅获取当前学生的认领状态
    my_claim = get_student_claim(session, item_id, student_id)
    my_claim_data = None
    if my_claim:
        my_claim_data = {
            "id": my_claim.id,
            "status": my_claim.status,
            "created_at": _format_datetime(my_claim.created_at),
        }

    return {
        "success": True,
        "data": {
            "id": item.id,
            "title": item.title,
            "description": item.description,
            "location": item.location,
            "image_url": item.image_url,
            "status": item.status,
            "comments": comment_list,
            "my_claim": my_claim_data,
            "created_at": _format_datetime(item.created_at),
        },
    }


@router.post("/student/lost-found/{item_id}/comments")
async def student_create_comment(
    request: Request,
    item_id: int,
    req: CreateCommentRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    """学生发表评论"""
    item = get_lost_found_item(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="物品不存在")

    student_id = int(user["sub"])
    comment = create_comment(session, item_id, student_id, req.content)

    return {"success": True, "data": {"comment_id": comment.id}}


@router.post("/student/lost-found/{item_id}/claim")
async def student_claim_item(
    request: Request,
    item_id: int,
    req: CreateClaimRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    """学生认领物品"""
    item = get_lost_found_item(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="物品不存在")

    student_id = int(user["sub"])
    try:
        claim = create_claim(
            session,
            item_id=item_id,
            student_id=student_id,
            contact=req.contact,
            message=req.message,
        )
    except DuplicateClaimError:
        raise HTTPException(status_code=400, detail="您已认领过该物品")
    except ItemNotClaimableError:
        raise HTTPException(status_code=400, detail="该物品已关闭，不可认领")

    return {"success": True, "data": {"claim_id": claim.id}}
