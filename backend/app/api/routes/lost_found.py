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
from app.api.deps import (
    require_admin_or_teacher, get_teacher_accessible_classes,
    verify_teacher_class_access,
)
from app.crud.lost_found import (
    create_lost_found_item, get_lost_found_item, get_lost_found_items,
    update_lost_found_item, delete_lost_found_item, get_item_class_ids,
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
    """获取发布者显示名（物品发布者一律是教师/管理员，来自 users 表）

    旧实现拿同一个数字先在 users.id 查、又在 students.student_id 查，
    是「评论者标识被误当成 users.id」这个设计错误的残留，现已拆开。
    """
    user = get_user(session, user_id)
    return user.username if user else None


def _get_student_name(session: Session, student_id: str) -> Optional[str]:
    """获取学生姓名（评论者/认领者一律是学生，标识为学号）"""
    student = get_student(session, student_id)
    return student.name if student else None


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


def _resolve_viewer_class_id(session: Session, user: dict) -> int:
    """解析学生可见班级ID

    学生未分班返回 0（不存在的班级ID → 仅匹配无关联行的全班级可见物品）。
    """
    student = get_student(session, user["sub"])
    if student and student.class_id:
        return student.class_id
    return 0


def _check_item_visibility(session: Session, item_id: int, student_sub: str) -> None:
    """校验学生对物品的可见性：物品限定了可见班级且本班不在其中 → 404（不泄露存在性）"""
    visible_class_ids = get_item_class_ids(session, [item_id]).get(item_id, [])
    if not visible_class_ids:
        return
    student = get_student(session, student_sub)
    student_class_id = student.class_id if student else None
    if student_class_id not in visible_class_ids:
        raise HTTPException(status_code=404, detail="物品不存在")


# ============== 教师端路由 ==============

@router.post("/teacher/lost-found")
async def teacher_create_item(
    request: Request,
    title: str = Form(..., description="物品名称"),
    description: str = Form(..., description="详细描述"),
    location: Optional[str] = Form(default=None, description="丢失/拾获地点"),
    image: Optional[UploadFile] = File(default=None, description="物品图片"),
    class_ids: List[int] = Form(default=[], description="可见班级ID（可多选，重复字段）；空=admin 所有班级可见 / 教师收敛为自己可访问班级"),
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher),
):
    """教师发布失物招领（教师只能发布到自己可访问的班级；admin 空=所有班级）"""
    teacher_id = int(user["sub"])

    # 授权：教师的目标班级必须属于自己；空范围收敛为可访问班级，
    # 不再产生「无关联行 = 全校可见」的物品（admin 保持原语义）
    if user.get("role") != "admin":
        accessible = get_teacher_accessible_classes(user, session)
        if not accessible:
            raise HTTPException(status_code=403, detail="无可访问班级，无法发布失物招领")
        if class_ids:
            for class_id in class_ids:
                verify_teacher_class_access(user, class_id, session)
        else:
            class_ids = accessible

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
        class_ids=class_ids or None,
    )
    return {"success": True, "data": {"item_id": item.id}}


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
    """教师获取失物招领列表（含认领统计）

    可见范围：自己发布的 OR 可见范围含自己任一班级 OR 全班级可见的物品；
    admin 不限；教学班未关联班级的教师返回空（fail-closed）。
    """
    items, total = get_lost_found_items(
        session, keyword, status, page, page_size,
        viewer_publisher_id=int(user["sub"]),
        viewer_class_ids=get_teacher_accessible_classes(user, session),  # admin → None
    )

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

    # P0 修复：教师只能查看自己发布的物品详情（admin 不受限）
    # 详情含全部认领记录（学号 + 联系方式）与评论者真实姓名，不能按 item_id 越权读取
    if user.get("role") != "admin" and item.publisher_id != int(user.get("sub", 0)):
        raise HTTPException(status_code=403, detail="无权查看他人发布的物品")

    publisher_name = _get_user_name(session, item.publisher_id)

    # 获取评论（教师端显示真实姓名）
    comments = get_comments_by_item(session, item_id)
    comment_list = []
    for c in comments:
        user_name = _get_student_name(session, c.student_id)
        comment_list.append({
            "id": c.id,
            "item_id": c.item_id,
            "student_id": c.student_id,
            "student_name": user_name,
            "content": c.content,
            "created_at": _format_datetime(c.created_at),
        })

    # 获取所有认领记录（教师端完整信息）
    claims = get_claims_by_item(session, item_id)
    claim_list = []
    for claim in claims:
        student_name = _get_student_name(session, claim.student_id)
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
            # 可见班级（编辑回显用；空列表=所有班级可见）
            "class_ids": get_item_class_ids(session, [item.id]).get(item.id, []),
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
    class_ids: Optional[List[int]] = Form(default=None, description="可见班级ID（可多选，重复字段）；提供则整体替换"),
    clear_class_scope: bool = Form(default=False, description="清空可见班级限定（admin 恢复所有班级可见；教师收敛为可访问班级）"),
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher),
):
    """教师编辑失物招领"""
    item = get_lost_found_item(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="物品不存在")

    # P0 修复：教师只能操作自己发布的物品（admin 不受限）
    if user.get("role") != "admin" and item.publisher_id != int(user.get("sub", 0)):
        raise HTTPException(status_code=403, detail="无权操作他人发布的物品")

    image_url = None
    if image:
        image_url = await _save_image(image)

    # 显式清空优先于 class_ids 替换（恢复所有班级可见）
    if clear_class_scope:
        class_ids = []

    # 授权：教师只能把可见范围限定到自己可访问的班级；空范围收敛为可访问班级，
    # 否则「发布时收敛 + 编辑时放开」可绕过上面的发布限制（admin 保持原语义）
    if class_ids is not None and user.get("role") != "admin":
        if class_ids:
            for class_id in class_ids:
                verify_teacher_class_access(user, class_id, session)
        else:
            accessible = get_teacher_accessible_classes(user, session)
            if not accessible:
                raise HTTPException(status_code=403, detail="无可访问班级，无法设置可见范围")
            class_ids = accessible

    updated = update_lost_found_item(
        session,
        item_id,
        title=title,
        description=description,
        location=location,
        image_url=image_url,
        class_ids=class_ids,
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

    # P0 修复：教师只能操作自己发布的物品（admin 不受限）
    if user.get("role") != "admin" and item.publisher_id != int(user.get("sub", 0)):
        raise HTTPException(status_code=403, detail="无权操作他人发布的物品")

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

    # P0 修复：教师只能操作自己发布的物品（admin 不受限）
    if user.get("role") != "admin" and item.publisher_id != int(user.get("sub", 0)):
        raise HTTPException(status_code=403, detail="无权操作他人发布的物品")

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

    # P0 修复：教师只能操作自己发布的物品（admin 不受限）
    if user.get("role") != "admin" and item.publisher_id != int(user.get("sub", 0)):
        raise HTTPException(status_code=403, detail="无权操作他人发布的物品")

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
    """学生浏览失物招领列表（按可见班级过滤）"""
    items, total = get_lost_found_items(
        session, keyword, status, page, page_size,
        viewer_class_id=_resolve_viewer_class_id(session, user),
    )

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

    student_id = str(user["sub"])

    # 可见性校验：物品限定了可见班级且本班不在其中 → 404（不泄露物品存在性）
    _check_item_visibility(session, item_id, user["sub"])

    # 获取评论（学生端匿名显示）
    comments = get_comments_by_item(session, item_id)
    comment_list = []
    for c in comments:
        comment_list.append({
            "id": c.id,
            "item_id": c.item_id,
            "student_id": "",  # 隐藏真实学号
            "student_name": "匿名用户",
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

    _check_item_visibility(session, item_id, user["sub"])

    student_id = str(user["sub"])
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

    _check_item_visibility(session, item_id, user["sub"])

    student_id = str(user["sub"])
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
