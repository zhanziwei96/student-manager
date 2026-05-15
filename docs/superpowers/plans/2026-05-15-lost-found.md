# 失物招领功能实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现教师发布失物招领、学生匿名浏览/评论/认领、教师确认认领的完整功能。

**Architecture:** 三表数据模型（items/comments/claims），教师端和学生端分离的 API 路由，隐私规则在 API 层实现（学生端剥离敏感字段），前端使用 TanStack Query + Vue 3 Composition API。

**Tech Stack:** FastAPI, SQLModel, Alembic, Vue 3.5, TypeScript, TanStack Vue Query, Tailwind CSS v4

---

## 文件结构

### 后端（新建）
- `backend/app/models/lost_found.py` — 三个 SQLModel 表模型 + 响应模型
- `backend/app/crud/lost_found.py` — CRUD 操作函数
- `backend/app/api/routes/lost_found.py` — 教师端 + 学生端 API 路由
- `backend/alembic/versions/2026_05_15_add_lost_found_tables.py` — 数据库迁移
- `tests/unit/crud/test_lost_found.py` — CRUD 单元测试
- `tests/integration/test_lost_found_api.py` — API 集成测试

### 后端（修改）
- `backend/app/models/__init__.py` — 注册模型导出
- `backend/app/crud/__init__.py` — 注册 CRUD 导出
- `backend/app/api/routes/__init__.py` — 注册路由导出
- `backend/main.py:170-192` — 注册路由器

### 前端（新建）
- `frontend-v3/src/types/lostFound.ts` — 类型定义
- `frontend-v3/src/api/lostFound.ts` — API 客户端
- `frontend-v3/src/composables/useLostFound.ts` — 组合式函数
- `frontend-v3/src/views/teacher/LostFound.vue` — 教师列表页
- `frontend-v3/src/views/teacher/LostFoundDetail.vue` — 教师详情页
- `frontend-v3/src/views/teacher/LostFoundForm.vue` — 教师表单页
- `frontend-v3/src/views/student/LostFound.vue` — 学生列表页
- `frontend-v3/src/views/student/LostFoundDetail.vue` — 学生详情页
- `frontend-v3/test/views/LostFound.spec.ts` — 前端测试

### 前端（修改）
- `frontend-v3/src/api/index.ts` — 注册 API 导出
- `frontend-v3/src/composables/index.ts` — 注册 composable 导出
- `frontend-v3/src/router/index.ts` — 注册路由
- `frontend-v3/src/layouts/DashboardLayout.vue` — 侧边栏导航

---

## Task 1: 后端数据模型

**Files:**
- Create: `backend/app/models/lost_found.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: 创建数据模型文件**

```python
# backend/app/models/lost_found.py
"""
失物招领模型
"""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from app.core.timezone import get_now


class LostFoundItem(SQLModel, table=True):
    """失物招领物品表"""
    __tablename__ = "lost_found_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(..., max_length=200, description="物品名称")
    description: str = Field(..., description="详细描述")
    location: Optional[str] = Field(default=None, max_length=200, description="丢失/拾获地点")
    image_url: Optional[str] = Field(default=None, max_length=500, description="图片存储路径")
    status: str = Field(default="open", description="状态: open/claiming/closed")
    publisher_id: int = Field(..., foreign_key="users.id", description="发布教师ID", index=True)
    created_at: datetime = Field(default_factory=get_now, description="创建时间")
    updated_at: datetime = Field(default_factory=get_now, description="更新时间")


class LostFoundComment(SQLModel, table=True):
    """失物招领评论表"""
    __tablename__ = "lost_found_comments"

    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: int = Field(..., foreign_key="lost_found_items.id", description="关联物品ID", index=True)
    user_id: int = Field(..., foreign_key="users.id", description="留言用户ID", index=True)
    content: str = Field(..., description="留言内容")
    created_at: datetime = Field(default_factory=get_now, description="创建时间")


class LostFoundClaim(SQLModel, table=True):
    """失物招领认领记录表"""
    __tablename__ = "lost_found_claims"

    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: int = Field(..., foreign_key="lost_found_items.id", description="关联物品ID", index=True)
    student_id: int = Field(..., foreign_key="users.id", description="认领学生ID", index=True)
    contact: str = Field(..., max_length=200, description="联系方式")
    message: Optional[str] = Field(default=None, description="认领说明")
    status: str = Field(default="pending", description="状态: pending/confirmed/rejected")
    created_at: datetime = Field(default_factory=get_now, description="创建时间")

    __table_args__ = (
        {"sqlite_autoincrement": True},
    )


# Pydantic 响应模型
class LostFoundItemResponse(SQLModel):
    """物品响应"""
    id: int
    title: str
    description: str
    location: Optional[str]
    image_url: Optional[str]
    status: str
    publisher_id: int
    created_at: datetime
    updated_at: datetime


class LostFoundCommentResponse(SQLModel):
    """评论响应（含用户信息）"""
    id: int
    item_id: int
    user_id: int
    user_name: Optional[str] = None
    content: str
    created_at: datetime


class LostFoundClaimResponse(SQLModel):
    """认领响应（含学生信息）"""
    id: int
    item_id: int
    student_id: int
    student_name: Optional[str] = None
    contact: str
    message: Optional[str]
    status: str
    created_at: datetime
```

- [ ] **Step 2: 注册模型导出**

修改 `backend/app/models/__init__.py`，在 imports 区域添加：

```python
from app.models.lost_found import (
    LostFoundItem, LostFoundComment, LostFoundClaim,
    LostFoundItemResponse, LostFoundCommentResponse, LostFoundClaimResponse,
)
```

在 `__all__` 列表中添加：

```python
# Lost & Found
"LostFoundItem", "LostFoundComment", "LostFoundClaim",
"LostFoundItemResponse", "LostFoundCommentResponse", "LostFoundClaimResponse",
```

- [ ] **Step 3: 验证模型导入**

Run: `conda run -n student-manage python -c "from app.models.lost_found import LostFoundItem, LostFoundComment, LostFoundClaim; print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/app/models/lost_found.py backend/app/models/__init__.py
git commit -m "feat(lost-found): add data models for items, comments, and claims"
```

---

## Task 2: 数据库迁移

**Files:**
- Create: `backend/alembic/versions/2026_05_15_add_lost_found_tables.py`

- [ ] **Step 1: 生成迁移文件**

Run: `cd /home/yufeng/student-manage-v3-security/student-manager/backend && conda run -n student-manage alembic revision --autogenerate -m "add lost found tables"`

- [ ] **Step 2: 检查生成的迁移文件**

确认包含 `lost_found_items`、`lost_found_comments`、`lost_found_claims` 三张表的创建。如果自动生成的迁移不完整，手动编辑补充。确保使用 `render_as_batch=True`（SQLite 兼容）。

关键检查点：
- `lost_found_items` 表有 `publisher_id` 外键和索引
- `lost_found_comments` 表有 `item_id` 和 `user_id` 外键和索引
- `lost_found_claims` 表有 `item_id` 和 `student_id` 外键和索引

- [ ] **Step 3: 执行迁移**

Run: `cd /home/yufeng/student-manage-v3-security/student-manager/backend && conda run -n student-manage alembic upgrade head`
Expected: 迁移成功，无错误

- [ ] **Step 4: 验证表已创建**

Run: `conda run -n student-manage python -c "from sqlmodel import SQLModel; from app.core.db import engine; from app.models.lost_found import *; SQLModel.metadata.create_all(engine); print('Tables OK')"`
Expected: `Tables OK`

- [ ] **Step 5: Commit**

```bash
git add backend/alembic/versions/
git commit -m "feat(lost-found): add database migration for lost_found tables"
```

---

## Task 3: CRUD 操作

**Files:**
- Create: `backend/app/crud/lost_found.py`
- Modify: `backend/app/crud/__init__.py`

- [ ] **Step 1: 创建 CRUD 文件**

```python
# backend/app/crud/lost_found.py
"""
失物招领 CRUD 操作
"""
from typing import List, Optional
from sqlmodel import Session, select, func, col
from app.models.lost_found import LostFoundItem, LostFoundComment, LostFoundClaim
from app.core.timezone import get_now


# ============== 物品 ==============

def create_lost_found_item(
    session: Session,
    publisher_id: int,
    title: str,
    description: str,
    location: Optional[str] = None,
    image_url: Optional[str] = None,
) -> LostFoundItem:
    """创建失物招领物品"""
    item = LostFoundItem(
        title=title,
        description=description,
        location=location,
        image_url=image_url,
        publisher_id=publisher_id,
        status="open",
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def get_lost_found_item(session: Session, item_id: int) -> Optional[LostFoundItem]:
    """获取单个物品"""
    return session.get(LostFoundItem, item_id)


def get_lost_found_items(
    session: Session,
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[List[LostFoundItem], int]:
    """获取物品列表（分页），返回 (items, total)"""
    query = select(LostFoundItem)
    count_query = select(func.count()).select_from(LostFoundItem)

    if keyword:
        like_pattern = f"%{keyword}%"
        condition = (
            (LostFoundItem.title.contains(keyword))
            | (LostFoundItem.description.contains(keyword))
            | (LostFoundItem.location.contains(keyword))
        )
        query = query.where(condition)
        count_query = count_query.where(condition)

    if status:
        query = query.where(LostFoundItem.status == status)
        count_query = count_query.where(LostFoundItem.status == status)

    total = session.exec(count_query).one()
    query = query.order_by(LostFoundItem.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    items = list(session.exec(query).all())
    return items, total


def update_lost_found_item(
    session: Session,
    item_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
    image_url: Optional[str] = None,
) -> Optional[LostFoundItem]:
    """编辑物品"""
    item = session.get(LostFoundItem, item_id)
    if not item:
        return None
    if title is not None:
        item.title = title
    if description is not None:
        item.description = description
    if location is not None:
        item.location = location
    if image_url is not None:
        item.image_url = image_url
    item.updated_at = get_now()
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def delete_lost_found_item(session: Session, item_id: int) -> bool:
    """删除物品及其评论和认领"""
    item = session.get(LostFoundItem, item_id)
    if not item:
        return False
    # 删除关联的评论
    comments = session.exec(
        select(LostFoundComment).where(LostFoundComment.item_id == item_id)
    ).all()
    for c in comments:
        session.delete(c)
    # 删除关联的认领
    claims = session.exec(
        select(LostFoundClaim).where(LostFoundClaim.item_id == item_id)
    ).all()
    for cl in claims:
        session.delete(cl)
    session.delete(item)
    session.commit()
    return True


def count_claims_by_status(session: Session, item_id: int, status: str) -> int:
    """统计某物品指定状态的认领数"""
    query = select(func.count()).select_from(LostFoundClaim).where(
        LostFoundClaim.item_id == item_id,
        LostFoundClaim.status == status,
    )
    return session.exec(query).one()


# ============== 评论 ==============

def create_comment(
    session: Session,
    item_id: int,
    user_id: int,
    content: str,
) -> LostFoundComment:
    """发表评论"""
    comment = LostFoundComment(
        item_id=item_id,
        user_id=user_id,
        content=content,
    )
    session.add(comment)
    session.commit()
    session.refresh(comment)
    return comment


def get_comments_by_item(session: Session, item_id: int) -> List[LostFoundComment]:
    """获取物品的所有评论"""
    query = select(LostFoundComment).where(
        LostFoundComment.item_id == item_id
    ).order_by(LostFoundComment.created_at.asc())
    return list(session.exec(query).all())


# ============== 认领 ==============

class DuplicateClaimError(Exception):
    """重复认领异常"""
    pass


class ItemNotClaimableError(Exception):
    """物品不可认领异常"""
    pass


def create_claim(
    session: Session,
    item_id: int,
    student_id: int,
    contact: str,
    message: Optional[str] = None,
) -> LostFoundClaim:
    """认领物品"""
    # 检查物品状态
    item = session.get(LostFoundItem, item_id)
    if not item or item.status == "closed":
        raise ItemNotClaimableError("物品不存在或已关闭")

    # 检查是否重复认领
    existing = session.exec(
        select(LostFoundClaim).where(
            LostFoundClaim.item_id == item_id,
            LostFoundClaim.student_id == student_id,
        )
    ).first()
    if existing:
        raise DuplicateClaimError("您已认领过该物品")

    claim = LostFoundClaim(
        item_id=item_id,
        student_id=student_id,
        contact=contact,
        message=message,
        status="pending",
    )
    session.add(claim)

    # 更新物品状态为 claiming
    if item.status == "open":
        item.status = "claiming"
        item.updated_at = get_now()
        session.add(item)

    session.commit()
    session.refresh(claim)
    return claim


def get_claims_by_item(session: Session, item_id: int) -> List[LostFoundClaim]:
    """获取物品的所有认领"""
    query = select(LostFoundClaim).where(
        LostFoundClaim.item_id == item_id
    ).order_by(LostFoundClaim.created_at.desc())
    return list(session.exec(query).all())


def get_claim(session: Session, claim_id: int) -> Optional[LostFoundClaim]:
    """获取单个认领"""
    return session.get(LostFoundClaim, claim_id)


def get_student_claim(session: Session, item_id: int, student_id: int) -> Optional[LostFoundClaim]:
    """获取学生对某物品的认领"""
    return session.exec(
        select(LostFoundClaim).where(
            LostFoundClaim.item_id == item_id,
            LostFoundClaim.student_id == student_id,
        )
    ).first()


def confirm_claim(session: Session, item_id: int, claim_id: int) -> Optional[LostFoundClaim]:
    """确认认领：将该认领设为 confirmed，其他 pending 认领设为 rejected，物品设为 closed"""
    claim = session.get(LostFoundClaim, claim_id)
    if not claim or claim.item_id != item_id:
        return None
    if claim.status != "pending":
        return None

    # 确认该认领
    claim.status = "confirmed"
    session.add(claim)

    # 拒绝其他 pending 认领
    other_claims = session.exec(
        select(LostFoundClaim).where(
            LostFoundClaim.item_id == item_id,
            LostFoundClaim.id != claim_id,
            LostFoundClaim.status == "pending",
        )
    ).all()
    for oc in other_claims:
        oc.status = "rejected"
        session.add(oc)

    # 关闭物品
    item = session.get(LostFoundItem, item_id)
    if item:
        item.status = "closed"
        item.updated_at = get_now()
        session.add(item)

    session.commit()
    session.refresh(claim)
    return claim


def reject_claim(session: Session, item_id: int, claim_id: int) -> Optional[LostFoundClaim]:
    """拒绝认领"""
    claim = session.get(LostFoundClaim, claim_id)
    if not claim or claim.item_id != item_id:
        return None
    if claim.status != "pending":
        return None

    claim.status = "rejected"
    session.add(claim)

    # 检查是否还有其他 pending 认领，没有则将物品状态改回 open
    remaining = session.exec(
        select(func.count()).select_from(LostFoundClaim).where(
            LostFoundClaim.item_id == item_id,
            LostFoundClaim.status == "pending",
            LostFoundClaim.id != claim_id,
        )
    ).one()
    if remaining == 0:
        item = session.get(LostFoundItem, item_id)
        if item and item.status == "claiming":
            item.status = "open"
            item.updated_at = get_now()
            session.add(item)

    session.commit()
    session.refresh(claim)
    return claim
```

- [ ] **Step 2: 注册 CRUD 导出**

修改 `backend/app/crud/__init__.py`，在 imports 区域添加：

```python
from app.crud.lost_found import (
    create_lost_found_item, get_lost_found_item, get_lost_found_items,
    update_lost_found_item, delete_lost_found_item,
    create_comment, get_comments_by_item,
    create_claim, get_claims_by_item, get_claim, get_student_claim,
    confirm_claim, reject_claim, count_claims_by_status,
    DuplicateClaimError, ItemNotClaimableError,
)
```

在 `__all__` 列表中添加对应函数名。

- [ ] **Step 3: 验证导入**

Run: `conda run -n student-manage python -c "from app.crud.lost_found import create_lost_found_item; print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/app/crud/lost_found.py backend/app/crud/__init__.py
git commit -m "feat(lost-found): add CRUD operations for items, comments, and claims"
```

---

## Task 4: 教师端 API 路由

**Files:**
- Create: `backend/app/api/routes/lost_found.py`
- Modify: `backend/app/api/routes/__init__.py`
- Modify: `backend/main.py`

- [ ] **Step 1: 创建路由文件（教师端部分）**

```python
# backend/app/api/routes/lost_found.py
"""
失物招领 API
"""
import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, File, Form, UploadFile
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.core.db import get_session
from app.core.jwt import get_current_user
from app.core.config import get_settings, HttpStatus
from app.core.timezone import get_now
from app.api.deps import require_admin_or_teacher
from app.models.constants import ApiResponseConst
from app.models.lost_found import (
    LostFoundItemResponse, LostFoundCommentResponse, LostFoundClaimResponse,
)
from app.crud.lost_found import (
    create_lost_found_item, get_lost_found_item, get_lost_found_items,
    update_lost_found_item, delete_lost_found_item,
    create_comment, get_comments_by_item,
    create_claim, get_claims_by_item, get_claim, get_student_claim,
    confirm_claim, reject_claim, count_claims_by_status,
    DuplicateClaimError, ItemNotClaimableError,
)
from app.crud.user import get_user

router = APIRouter(tags=["lost_found"])


# ============== 请求/响应模型 ==============

class CreateItemRequest(BaseModel):
    title: str = Field(..., max_length=200, description="物品名称")
    description: str = Field(..., description="详细描述")
    location: Optional[str] = Field(default=None, max_length=200, description="地点")


class UpdateItemRequest(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None)
    location: Optional[str] = Field(default=None, max_length=200)


class CreateCommentRequest(BaseModel):
    content: str = Field(..., description="评论内容")


class CreateClaimRequest(BaseModel):
    contact: str = Field(..., max_length=200, description="联系方式")
    message: Optional[str] = Field(default=None, description="认领说明")


class TeacherItemDetail(BaseModel):
    id: int
    title: str
    description: str
    location: Optional[str]
    image_url: Optional[str]
    status: str
    publisher_id: int
    publisher_name: Optional[str] = None
    created_at: str
    updated_at: str
    comments: list
    claims: list
    pending_count: int = 0


class TeacherItemListItem(BaseModel):
    id: int
    title: str
    description: str
    location: Optional[str]
    image_url: Optional[str]
    status: str
    publisher_id: int
    created_at: str
    updated_at: str
    pending_count: int = 0
    total_claims: int = 0


class StudentItemDetail(BaseModel):
    id: int
    title: str
    description: str
    location: Optional[str]
    image_url: Optional[str]
    status: str
    publisher_name: Optional[str] = None
    created_at: str
    updated_at: str
    comments: list
    my_claim: Optional[dict] = None


class StudentItemListItem(BaseModel):
    id: int
    title: str
    description: str
    location: Optional[str]
    image_url: Optional[str]
    status: str
    publisher_name: Optional[str] = None
    created_at: str
    updated_at: str


# ============== 辅助函数 ==============

def _format_datetime(dt) -> str:
    """格式化时间为 ISO 字符串"""
    return dt.isoformat() if dt else ""


def _get_user_name(session: Session, user_id: int) -> Optional[str]:
    """获取用户真实姓名"""
    user = get_user(session, user_id)
    if user:
        from app.crud.student import get_student
        student = get_student(session, str(user_id))
        if student:
            return student.name
        return user.username
    return None


# ============== 教师端路由 ==============

@router.post("/teacher/lost-found")
async def teacher_create_item(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    location: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher),
):
    """教师创建失物招领物品"""
    publisher_id = int(user["sub"])
    image_url = None

    if file:
        from app.core.upload import save_upload_file_securely
        settings = get_settings()
        file_path, _ = await save_upload_file_securely(
            file,
            allowed_extensions=[".jpg", ".jpeg", ".png", ".gif", ".webp"],
            allowed_content_types=["image/jpeg", "image/png", "image/gif", "image/webp"],
            max_size_mb=5,
            use_uuid=True,
            upload_directory=os.path.join(settings.upload.directory, "lost-found"),
        )
        # 返回相对路径
        image_url = f"/uploads/lost-found/{os.path.basename(file_path)}"

    item = create_lost_found_item(
        session,
        publisher_id=publisher_id,
        title=title,
        description=description,
        location=location,
        image_url=image_url,
    )
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {"id": item.id},
    }


@router.get("/teacher/lost-found")
async def teacher_list_items(
    request: Request,
    keyword: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher),
):
    """教师获取物品列表"""
    items, total = get_lost_found_items(session, keyword=keyword, status=status, page=page, page_size=page_size)

    result = []
    for item in items:
        pending = count_claims_by_status(session, item.id, "pending")
        total_claims = len(get_claims_by_item(session, item.id))
        result.append(TeacherItemListItem(
            id=item.id,
            title=item.title,
            description=item.description,
            location=item.location,
            image_url=item.image_url,
            status=item.status,
            publisher_id=item.publisher_id,
            created_at=_format_datetime(item.created_at),
            updated_at=_format_datetime(item.updated_at),
            pending_count=pending,
            total_claims=total_claims,
        ))

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {"items": [r.model_dump() for r in result], "total": total},
    }


@router.get("/teacher/lost-found/{item_id}")
async def teacher_get_item(
    request: Request,
    item_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher),
):
    """教师获取物品详情（含认领者真实信息）"""
    item = get_lost_found_item(session, item_id)
    if not item:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="物品不存在")

    comments = get_comments_by_item(session, item_id)
    claims = get_claims_by_item(session, item_id)

    comment_list = []
    for c in comments:
        name = _get_user_name(session, c.user_id)
        comment_list.append(LostFoundCommentResponse(
            id=c.id, item_id=c.item_id, user_id=c.user_id,
            user_name=name, content=c.content,
            created_at=c.created_at,
        ).model_dump())

    claim_list = []
    for cl in claims:
        name = _get_user_name(session, cl.student_id)
        claim_list.append(LostFoundClaimResponse(
            id=cl.id, item_id=cl.item_id, student_id=cl.student_id,
            student_name=name, contact=cl.contact, message=cl.message,
            status=cl.status, created_at=cl.created_at,
        ).model_dump())

    pending = count_claims_by_status(session, item_id, "pending")

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: TeacherItemDetail(
            id=item.id, title=item.title, description=item.description,
            location=item.location, image_url=item.image_url, status=item.status,
            publisher_id=item.publisher_id,
            publisher_name=_get_user_name(session, item.publisher_id),
            created_at=_format_datetime(item.created_at),
            updated_at=_format_datetime(item.updated_at),
            comments=comment_list, claims=claim_list, pending_count=pending,
        ).model_dump(),
    }


@router.put("/teacher/lost-found/{item_id}")
async def teacher_update_item(
    request: Request,
    item_id: int,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher),
):
    """教师编辑物品"""
    existing = get_lost_found_item(session, item_id)
    if not existing:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="物品不存在")

    image_url = None
    if file:
        from app.core.upload import save_upload_file_securely
        settings = get_settings()
        file_path, _ = await save_upload_file_securely(
            file,
            allowed_extensions=[".jpg", ".jpeg", ".png", ".gif", ".webp"],
            allowed_content_types=["image/jpeg", "image/png", "image/gif", "image/webp"],
            max_size_mb=5,
            use_uuid=True,
            upload_directory=os.path.join(settings.upload.directory, "lost-found"),
        )
        image_url = f"/uploads/lost-found/{os.path.basename(file_path)}"

    item = update_lost_found_item(
        session, item_id,
        title=title, description=description,
        location=location, image_url=image_url,
    )
    return {ApiResponseConst.SUCCESS: True}


@router.delete("/teacher/lost-found/{item_id}")
async def teacher_delete_item(
    request: Request,
    item_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher),
):
    """教师删除物品"""
    ok = delete_lost_found_item(session, item_id)
    if not ok:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="物品不存在")
    return {ApiResponseConst.SUCCESS: True}


@router.put("/teacher/lost-found/{item_id}/claims/{claim_id}/confirm")
async def teacher_confirm_claim(
    request: Request,
    item_id: int,
    claim_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher),
):
    """教师确认认领"""
    claim = confirm_claim(session, item_id, claim_id)
    if not claim:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="认领不存在或状态不正确")
    return {ApiResponseConst.SUCCESS: True}


@router.put("/teacher/lost-found/{item_id}/claims/{claim_id}/reject")
async def teacher_reject_claim(
    request: Request,
    item_id: int,
    claim_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher),
):
    """教师拒绝认领"""
    claim = reject_claim(session, item_id, claim_id)
    if not claim:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="认领不存在或状态不正确")
    return {ApiResponseConst.SUCCESS: True}


# ============== 学生端路由 ==============

@router.get("/student/lost-found")
async def student_list_items(
    request: Request,
    keyword: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    """学生浏览物品列表"""
    items, total = get_lost_found_items(session, keyword=keyword, status=status, page=page, page_size=page_size)

    result = []
    for item in items:
        publisher_name = _get_user_name(session, item.publisher_id)
        result.append(StudentItemListItem(
            id=item.id, title=item.title, description=item.description,
            location=item.location, image_url=item.image_url, status=item.status,
            publisher_name=publisher_name,
            created_at=_format_datetime(item.created_at),
            updated_at=_format_datetime(item.updated_at),
        ).model_dump())

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {"items": result, "total": total},
    }


@router.get("/student/lost-found/{item_id}")
async def student_get_item(
    request: Request,
    item_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    """学生查看物品详情（匿名处理）"""
    item = get_lost_found_item(session, item_id)
    if not item:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="物品不存在")

    comments = get_comments_by_item(session, item_id)
    student_id = int(user["sub"])

    # 评论匿名处理
    comment_list = []
    for c in comments:
        comment_list.append({
            "id": c.id,
            "content": c.content,
            "user_name": "匿名用户",
            "created_at": _format_datetime(c.created_at),
        })

    # 自己的认领信息
    my_claim = get_student_claim(session, item_id, student_id)
    my_claim_data = None
    if my_claim:
        my_claim_data = {
            "id": my_claim.id,
            "status": my_claim.status,
            "created_at": _format_datetime(my_claim.created_at),
        }

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: StudentItemDetail(
            id=item.id, title=item.title, description=item.description,
            location=item.location, image_url=item.image_url, status=item.status,
            publisher_name=_get_user_name(session, item.publisher_id),
            created_at=_format_datetime(item.created_at),
            updated_at=_format_datetime(item.updated_at),
            comments=comment_list, my_claim=my_claim_data,
        ).model_dump(),
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
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="物品不存在")
    if item.status == "closed":
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="物品已关闭，无法评论")

    student_id = int(user["sub"])
    comment = create_comment(session, item_id=item_id, user_id=student_id, content=req.content)
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: {"id": comment.id}}


@router.post("/student/lost-found/{item_id}/claim")
async def student_claim_item(
    request: Request,
    item_id: int,
    req: CreateClaimRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    """学生认领物品"""
    student_id = int(user["sub"])
    try:
        claim = create_claim(
            session, item_id=item_id, student_id=student_id,
            contact=req.contact, message=req.message,
        )
    except DuplicateClaimError:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="您已认领过该物品")
    except ItemNotClaimableError:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="物品不存在或已关闭")

    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: {"id": claim.id}}
```

- [ ] **Step 2: 注册路由导出**

修改 `backend/app/api/routes/__init__.py`，添加：

```python
from app.api.routes.lost_found import router as lost_found_router
```

在 `__all__` 中添加 `"lost_found_router"`。

- [ ] **Step 3: 注册路由器**

修改 `backend/main.py`，在 imports 区域添加 `lost_found_router`，在路由注册区域添加：

```python
app.include_router(lost_found_router, prefix=API_V1_PREFIX)
```

- [ ] **Step 4: 验证服务启动**

Run: `make status` 或 `curl -s --max-time 5 http://localhost:8000/api/v1/health`
Expected: 服务正常运行

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/routes/lost_found.py backend/app/api/routes/__init__.py backend/main.py
git commit -m "feat(lost-found): add teacher and student API routes with privacy rules"
```

---

## Task 5: 后端单元测试

**Files:**
- Create: `tests/unit/crud/test_lost_found.py`

- [ ] **Step 1: 创建 CRUD 单元测试**

```python
# tests/unit/crud/test_lost_found.py
"""
失物招领 CRUD 单元测试
"""
import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.models.lost_found import LostFoundItem, LostFoundComment, LostFoundClaim
from app.models.user import User
from app.models.constants import UserRole
from app.crud.lost_found import (
    create_lost_found_item, get_lost_found_item, get_lost_found_items,
    update_lost_found_item, delete_lost_found_item,
    create_comment, get_comments_by_item,
    create_claim, get_claims_by_item, get_student_claim,
    confirm_claim, reject_claim, count_claims_by_status,
    DuplicateClaimError, ItemNotClaimableError,
)
from app.core.timezone import get_now


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


@pytest.fixture
def teacher(session):
    user = User(username="teacher1", hashed_password="x", role=UserRole.TEACHER.value)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def student(session):
    user = User(username="student1", hashed_password="x", role=UserRole.STUDENT.value)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def student2(session):
    user = User(username="student2", hashed_password="x", role=UserRole.STUDENT.value)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


class TestItemCRUD:
    def test_create_item(self, session, teacher):
        item = create_lost_found_item(
            session, publisher_id=teacher.id,
            title="一串钥匙", description="蓝色钥匙扣",
            location="操场",
        )
        assert item.id is not None
        assert item.title == "一串钥匙"
        assert item.status == "open"

    def test_get_item(self, session, teacher):
        item = create_lost_found_item(session, teacher.id, "钥匙", "描述")
        found = get_lost_found_item(session, item.id)
        assert found is not None
        assert found.title == "钥匙"

    def test_get_items_with_keyword(self, session, teacher):
        create_lost_found_item(session, teacher.id, "钥匙", "蓝色钥匙扣")
        create_lost_found_item(session, teacher.id, "手机", "iPhone")
        items, total = get_lost_found_items(session, keyword="钥匙")
        assert total == 1
        assert items[0].title == "钥匙"

    def test_get_items_with_status(self, session, teacher):
        item = create_lost_found_item(session, teacher.id, "钥匙", "描述")
        items, total = get_lost_found_items(session, status="open")
        assert total == 1
        items, total = get_lost_found_items(session, status="closed")
        assert total == 0

    def test_update_item(self, session, teacher):
        item = create_lost_found_item(session, teacher.id, "钥匙", "描述")
        updated = update_lost_found_item(session, item.id, title="新钥匙")
        assert updated.title == "新钥匙"

    def test_delete_item(self, session, teacher):
        item = create_lost_found_item(session, teacher.id, "钥匙", "描述")
        assert delete_lost_found_item(session, item.id) is True
        assert get_lost_found_item(session, item.id) is None


class TestCommentCRUD:
    def test_create_comment(self, session, teacher, student):
        item = create_lost_found_item(session, teacher.id, "钥匙", "描述")
        comment = create_comment(session, item.id, student.id, "我看到了")
        assert comment.id is not None
        assert comment.content == "我看到了"

    def test_get_comments(self, session, teacher, student):
        item = create_lost_found_item(session, teacher.id, "钥匙", "描述")
        create_comment(session, item.id, student.id, "评论1")
        create_comment(session, item.id, student.id, "评论2")
        comments = get_comments_by_item(session, item.id)
        assert len(comments) == 2


class TestClaimCRUD:
    def test_create_claim(self, session, teacher, student):
        item = create_lost_found_item(session, teacher.id, "钥匙", "描述")
        claim = create_claim(session, item.id, student.id, "微信: stu1", "这是我的")
        assert claim.status == "pending"
        # 物品状态应变为 claiming
        updated_item = get_lost_found_item(session, item.id)
        assert updated_item.status == "claiming"

    def test_duplicate_claim(self, session, teacher, student):
        item = create_lost_found_item(session, teacher.id, "钥匙", "描述")
        create_claim(session, item.id, student.id, "微信: stu1")
        with pytest.raises(DuplicateClaimError):
            create_claim(session, item.id, student.id, "微信: stu1")

    def test_claim_closed_item(self, session, teacher, student):
        item = create_lost_found_item(session, teacher.id, "钥匙", "描述")
        item.status = "closed"
        session.add(item)
        session.commit()
        with pytest.raises(ItemNotClaimableError):
            create_claim(session, item.id, student.id, "微信: stu1")

    def test_confirm_claim(self, session, teacher, student, student2):
        item = create_lost_found_item(session, teacher.id, "钥匙", "描述")
        claim1 = create_claim(session, item.id, student.id, "微信: stu1")
        claim2 = create_claim(session, item.id, student2.id, "微信: stu2")

        confirmed = confirm_claim(session, item.id, claim1.id)
        assert confirmed.status == "confirmed"

        # 物品应关闭
        updated_item = get_lost_found_item(session, item.id)
        assert updated_item.status == "closed"

        # 其他认领应被拒绝
        updated_claim2 = get_claims_by_item(session, item.id)
        rejected = [c for c in updated_claim2 if c.id == claim2.id][0]
        assert rejected.status == "rejected"

    def test_reject_claim(self, session, teacher, student):
        item = create_lost_found_item(session, teacher.id, "钥匙", "描述")
        claim = create_claim(session, item.id, student.id, "微信: stu1")
        rejected = reject_claim(session, item.id, claim.id)
        assert rejected.status == "rejected"
        # 没有其他 pending 认领，物品应恢复 open
        updated_item = get_lost_found_item(session, item.id)
        assert updated_item.status == "open"

    def test_count_pending_claims(self, session, teacher, student, student2):
        item = create_lost_found_item(session, teacher.id, "钥匙", "描述")
        create_claim(session, item.id, student.id, "微信: stu1")
        create_claim(session, item.id, student2.id, "微信: stu2")
        assert count_claims_by_status(session, item.id, "pending") == 2
```

- [ ] **Step 2: 运行测试**

Run: `cd /home/yufeng/student-manage-v3-security/student-manager && conda run -n student-manage pytest tests/unit/crud/test_lost_found.py -v`
Expected: 全部 PASS

- [ ] **Step 3: Commit**

```bash
git add tests/unit/crud/test_lost_found.py
git commit -m "test(lost-found): add CRUD unit tests"
```

---

## Task 6: 后端集成测试

**Files:**
- Create: `tests/integration/test_lost_found_api.py`

- [ ] **Step 1: 创建集成测试**

```python
# tests/integration/test_lost_found_api.py
"""
失物招领 API 集成测试
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from datetime import datetime

from main import create_app
from app.core.db import get_session
from app.core.jwt import create_access_token
from app.models.user import User
from app.models.student import Student
from app.models.constants import UserRole
from app.core.timezone import get_now


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


@pytest.fixture
def app(session):
    def override():
        yield session
    a = create_app()
    a.dependency_overrides[get_session] = override
    return a


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def teacher_token(session):
    user = User(username="teacher1", hashed_password="x", role=UserRole.TEACHER.value)
    session.add(user)
    session.commit()
    session.refresh(user)
    student = Student(student_id=str(user.id), name="李老师", class_name="测试班")
    session.add(student)
    session.commit()
    return create_access_token({"sub": str(user.id), "role": UserRole.TEACHER.value})


@pytest.fixture
def student_token(session):
    user = User(username="student1", hashed_password="x", role=UserRole.STUDENT.value)
    session.add(user)
    session.commit()
    session.refresh(user)
    student = Student(student_id=str(user.id), name="张三", class_name="测试班")
    session.add(student)
    session.commit()
    return create_access_token({"sub": str(user.id), "role": UserRole.STUDENT.value})


class TestTeacherAPI:
    def test_create_item(self, client, teacher_token):
        resp = client.post(
            "/api/v1/teacher/lost-found",
            data={"title": "钥匙", "description": "蓝色钥匙扣", "location": "操场"},
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "id" in data["data"]

    def test_list_items(self, client, teacher_token):
        # 先创建
        client.post(
            "/api/v1/teacher/lost-found",
            data={"title": "钥匙", "description": "描述"},
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        resp = client.get(
            "/api/v1/teacher/lost-found",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["total"] >= 1

    def test_get_item_detail(self, client, teacher_token):
        create_resp = client.post(
            "/api/v1/teacher/lost-found",
            data={"title": "钥匙", "description": "描述"},
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        item_id = create_resp.json()["data"]["id"]
        resp = client.get(
            f"/api/v1/teacher/lost-found/{item_id}",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["title"] == "钥匙"

    def test_delete_item(self, client, teacher_token):
        create_resp = client.post(
            "/api/v1/teacher/lost-found",
            data={"title": "钥匙", "description": "描述"},
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        item_id = create_resp.json()["data"]["id"]
        resp = client.delete(
            f"/api/v1/teacher/lost-found/{item_id}",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert resp.status_code == 200

    def test_student_cannot_access_teacher_api(self, client, student_token):
        resp = client.post(
            "/api/v1/teacher/lost-found",
            data={"title": "钥匙", "description": "描述"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert resp.status_code == 403


class TestStudentAPI:
    def _create_item(self, client, teacher_token):
        resp = client.post(
            "/api/v1/teacher/lost-found",
            data={"title": "钥匙", "description": "蓝色钥匙扣", "location": "操场"},
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        return resp.json()["data"]["id"]

    def test_list_items(self, client, student_token, teacher_token):
        self._create_item(client, teacher_token)
        resp = client.get(
            "/api/v1/student/lost-found",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["total"] >= 1

    def test_get_item_detail_anonymous(self, client, student_token, teacher_token):
        item_id = self._create_item(client, teacher_token)
        resp = client.get(
            f"/api/v1/student/lost-found/{item_id}",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["title"] == "钥匙"
        # 评论者应匿名
        assert data["comments"] == []

    def test_create_comment(self, client, student_token, teacher_token):
        item_id = self._create_item(client, teacher_token)
        resp = client.post(
            f"/api/v1/student/lost-found/{item_id}/comments",
            json={"content": "我看到了"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert resp.status_code == 200

    def test_claim_item(self, client, student_token, teacher_token):
        item_id = self._create_item(client, teacher_token)
        resp = client.post(
            f"/api/v1/student/lost-found/{item_id}/claim",
            json={"contact": "微信: stu1", "message": "这是我的"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert resp.status_code == 200

    def test_duplicate_claim(self, client, student_token, teacher_token):
        item_id = self._create_item(client, teacher_token)
        client.post(
            f"/api/v1/student/lost-found/{item_id}/claim",
            json={"contact": "微信: stu1"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        resp = client.post(
            f"/api/v1/student/lost-found/{item_id}/claim",
            json={"contact": "微信: stu1"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert resp.status_code == 400

    def test_privacy_student_sees_no_claim_info(self, client, student_token, teacher_token):
        """学生端详情不应包含认领者信息"""
        item_id = self._create_item(client, teacher_token)
        # 学生认领
        client.post(
            f"/api/v1/student/lost-found/{item_id}/claim",
            json={"contact": "微信: stu1"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        # 学生查看详情
        resp = client.get(
            f"/api/v1/student/lost-found/{item_id}",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        data = resp.json()["data"]
        # 不应有 claims 字段
        assert "claims" not in data
        # 应有 my_claim 字段
        assert data["my_claim"] is not None
        assert data["my_claim"]["status"] == "pending"

    def test_teacher_sees_claim_info(self, client, student_token, teacher_token):
        """教师端详情应包含认领者真实信息"""
        item_id = self._create_item(client, teacher_token)
        client.post(
            f"/api/v1/student/lost-found/{item_id}/claim",
            json={"contact": "微信: stu1", "message": "这是我的"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        resp = client.get(
            f"/api/v1/teacher/lost-found/{item_id}",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        data = resp.json()["data"]
        assert len(data["claims"]) == 1
        assert data["claims"][0]["contact"] == "微信: stu1"
        assert data["claims"][0]["student_name"] == "张三"

    def test_confirm_claim_flow(self, client, student_token, teacher_token):
        item_id = self._create_item(client, teacher_token)
        claim_resp = client.post(
            f"/api/v1/student/lost-found/{item_id}/claim",
            json={"contact": "微信: stu1"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        claim_id = claim_resp.json()["data"]["id"]

        resp = client.put(
            f"/api/v1/teacher/lost-found/{item_id}/claims/{claim_id}/confirm",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert resp.status_code == 200

        # 物品应关闭
        detail = client.get(
            f"/api/v1/teacher/lost-found/{item_id}",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert detail.json()["data"]["status"] == "closed"
```

- [ ] **Step 2: 运行测试**

Run: `cd /home/yufeng/student-manage-v3-security/student-manager && conda run -n student-manage pytest tests/integration/test_lost_found_api.py -v`
Expected: 全部 PASS

- [ ] **Step 3: Commit**

```bash
git add tests/integration/test_lost_found_api.py
git commit -m "test(lost-found): add API integration tests with privacy verification"
```

---

## Task 7: 前端类型定义与 API 客户端

**Files:**
- Create: `frontend-v3/src/types/lostFound.ts`
- Create: `frontend-v3/src/api/lostFound.ts`
- Modify: `frontend-v3/src/api/index.ts`
- Modify: `frontend-v3/src/types/index.ts`

- [ ] **Step 1: 创建类型定义**

```typescript
// frontend-v3/src/types/lostFound.ts
/**
 * 失物招领类型定义
 */

/** 物品状态 */
export type LostFoundStatus = 'open' | 'claiming' | 'closed'

/** 认领状态 */
export type ClaimStatus = 'pending' | 'confirmed' | 'rejected'

/** 物品列表项（教师端） */
export interface TeacherLostFoundItem {
  id: number
  title: string
  description: string
  location?: string
  image_url?: string
  status: LostFoundStatus
  publisher_id: number
  created_at: string
  updated_at: string
  pending_count: number
  total_claims: number
}

/** 物品详情（教师端） */
export interface TeacherLostFoundDetail {
  id: number
  title: string
  description: string
  location?: string
  image_url?: string
  status: LostFoundStatus
  publisher_id: number
  publisher_name?: string
  created_at: string
  updated_at: string
  comments: LostFoundComment[]
  claims: LostFoundClaim[]
  pending_count: number
}

/** 物品列表项（学生端） */
export interface StudentLostFoundItem {
  id: number
  title: string
  description: string
  location?: string
  image_url?: string
  status: LostFoundStatus
  publisher_name?: string
  created_at: string
  updated_at: string
}

/** 物品详情（学生端） */
export interface StudentLostFoundDetail {
  id: number
  title: string
  description: string
  location?: string
  image_url?: string
  status: LostFoundStatus
  publisher_name?: string
  created_at: string
  updated_at: string
  comments: LostFoundCommentAnonymous[]
  my_claim?: MyClaimInfo
}

/** 评论（教师端，含真实姓名） */
export interface LostFoundComment {
  id: number
  item_id: number
  user_id: number
  user_name?: string
  content: string
  created_at: string
}

/** 评论（学生端，匿名） */
export interface LostFoundCommentAnonymous {
  id: number
  content: string
  user_name: string
  created_at: string
}

/** 认领记录（教师端） */
export interface LostFoundClaim {
  id: number
  item_id: number
  student_id: number
  student_name?: string
  contact: string
  message?: string
  status: ClaimStatus
  created_at: string
}

/** 我的认领信息（学生端） */
export interface MyClaimInfo {
  id: number
  status: ClaimStatus
  created_at: string
}

/** 创建评论请求 */
export interface CreateLostFoundCommentRequest {
  content: string
}

/** 认领请求 */
export interface CreateLostFoundClaimRequest {
  contact: string
  message?: string
}

/** 列表查询参数 */
export interface LostFoundQueryParams {
  keyword?: string
  status?: LostFoundStatus
  page?: number
  page_size?: number
}

/** 列表响应 */
export interface LostFoundListResponse<T> {
  items: T[]
  total: number
}
```

- [ ] **Step 2: 创建 API 客户端**

```typescript
// frontend-v3/src/api/lostFound.ts
/**
 * 失物招领 API
 */
import { get, post, put, del } from '@/lib/api'
import type {
  TeacherLostFoundItem,
  TeacherLostFoundDetail,
  StudentLostFoundItem,
  StudentLostFoundDetail,
  LostFoundListResponse,
  CreateLostFoundCommentRequest,
  CreateLostFoundClaimRequest,
  LostFoundQueryParams,
} from '@/types/lostFound'

// ============== 教师端 API ==============

/** 教师创建物品（multipart/form-data） */
export async function createLostFoundItem(data: {
  title: string
  description: string
  location?: string
  file?: File
}): Promise<{ id: number }> {
  const formData = new FormData()
  formData.append('title', data.title)
  formData.append('description', data.description)
  if (data.location) formData.append('location', data.location)
  if (data.file) formData.append('file', data.file)

  return post('/teacher/lost-found', formData)
}

/** 教师获取物品列表 */
export function getTeacherLostFoundItems(params?: LostFoundQueryParams): Promise<LostFoundListResponse<TeacherLostFoundItem>> {
  return get('/teacher/lost-found', params)
}

/** 教师获取物品详情 */
export function getTeacherLostFoundDetail(id: number): Promise<TeacherLostFoundDetail> {
  return get(`/teacher/lost-found/${id}`)
}

/** 教师编辑物品 */
export async function updateLostFoundItem(id: number, data: {
  title?: string
  description?: string
  location?: string
  file?: File
}): Promise<void> {
  const formData = new FormData()
  if (data.title) formData.append('title', data.title)
  if (data.description) formData.append('description', data.description)
  if (data.location) formData.append('location', data.location)
  if (data.file) formData.append('file', data.file)

  return put(`/teacher/lost-found/${id}`, formData)
}

/** 教师删除物品 */
export function deleteLostFoundItem(id: number): Promise<void> {
  return del(`/teacher/lost-found/${id}`)
}

/** 教师确认认领 */
export function confirmClaim(itemId: number, claimId: number): Promise<void> {
  return put(`/teacher/lost-found/${itemId}/claims/${claimId}/confirm`)
}

/** 教师拒绝认领 */
export function rejectClaim(itemId: number, claimId: number): Promise<void> {
  return put(`/teacher/lost-found/${itemId}/claims/${claimId}/reject`)
}

// ============== 学生端 API ==============

/** 学生浏览物品列表 */
export function getStudentLostFoundItems(params?: LostFoundQueryParams): Promise<LostFoundListResponse<StudentLostFoundItem>> {
  return get('/student/lost-found', params)
}

/** 学生查看物品详情 */
export function getStudentLostFoundDetail(id: number): Promise<StudentLostFoundDetail> {
  return get(`/student/lost-found/${id}`)
}

/** 学生发表评论 */
export function createLostFoundComment(itemId: number, data: CreateLostFoundCommentRequest): Promise<{ id: number }> {
  return post(`/student/lost-found/${itemId}/comments`, data)
}

/** 学生认领物品 */
export function claimLostFoundItem(itemId: number, data: CreateLostFoundClaimRequest): Promise<{ id: number }> {
  return post(`/student/lost-found/${itemId}/claim`, data)
}
```

- [ ] **Step 3: 注册导出**

修改 `frontend-v3/src/api/index.ts`，添加：

```typescript
export * as lostFoundApi from './lostFound'
```

修改 `frontend-v3/src/types/index.ts`，添加：

```typescript
export * from './lostFound'
```

- [ ] **Step 4: 验证类型检查**

Run: `cd /home/yufeng/student-manage-v3-security/student-manager/frontend-v3 && pnpm exec vue-tsc --noEmit 2>&1 | head -20`
Expected: 无 lostFound 相关类型错误

- [ ] **Step 5: Commit**

```bash
git add frontend-v3/src/types/lostFound.ts frontend-v3/src/api/lostFound.ts frontend-v3/src/api/index.ts frontend-v3/src/types/index.ts
git commit -m "feat(lost-found): add frontend types and API client"
```

---

## Task 8: 前端 Composable

**Files:**
- Create: `frontend-v3/src/composables/useLostFound.ts`
- Modify: `frontend-v3/src/composables/index.ts`

- [ ] **Step 1: 创建 Composable**

```typescript
// frontend-v3/src/composables/useLostFound.ts
/**
 * 失物招领 Composable
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { computed, ref } from 'vue'
import { lostFoundApi } from '@/api'
import { useToast } from './useToast'
import type {
  LostFoundQueryParams,
  CreateLostFoundCommentRequest,
  CreateLostFoundClaimRequest,
} from '@/types/lostFound'

// ============== 教师端 ==============

/** 教师获取物品列表 */
export function useTeacherLostFoundItems(params?: () => LostFoundQueryParams) {
  const queryClient = useQueryClient()

  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['teacher-lost-found', params?.()],
    queryFn: async () => {
      return await lostFoundApi.getTeacherLostFoundItems(params?.())
    },
    staleTime: 1000 * 60 * 2,
  })

  return { data, isPending, error, refetch }
}

/** 教师获取物品详情 */
export function useTeacherLostFoundDetail(id: () => number | undefined) {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['teacher-lost-found-detail', id()],
    queryFn: async () => {
      return await lostFoundApi.getTeacherLostFoundDetail(id()!)
    },
    enabled: () => !!id(),
    staleTime: 1000 * 60 * 2,
  })

  return { data, isPending, error, refetch }
}

/** 教师创建物品 */
export function useCreateLostFoundItem() {
  const queryClient = useQueryClient()
  const { showSuccess, showError } = useToast()

  return useMutation({
    mutationFn: async (data: { title: string; description: string; location?: string; file?: File }) => {
      return await lostFoundApi.createLostFoundItem(data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teacher-lost-found'] })
      showSuccess('发布成功')
    },
    onError: () => {
      showError('发布失败')
    },
  })
}

/** 教师删除物品 */
export function useDeleteLostFoundItem() {
  const queryClient = useQueryClient()
  const { showSuccess, showError } = useToast()

  return useMutation({
    mutationFn: async (id: number) => {
      return await lostFoundApi.deleteLostFoundItem(id)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teacher-lost-found'] })
      showSuccess('删除成功')
    },
    onError: () => {
      showError('删除失败')
    },
  })
}

/** 教师确认认领 */
export function useConfirmClaim() {
  const queryClient = useQueryClient()
  const { showSuccess, showError } = useToast()

  return useMutation({
    mutationFn: async ({ itemId, claimId }: { itemId: number; claimId: number }) => {
      return await lostFoundApi.confirmClaim(itemId, claimId)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teacher-lost-found'] })
      queryClient.invalidateQueries({ queryKey: ['teacher-lost-found-detail'] })
      showSuccess('已确认认领')
    },
    onError: () => {
      showError('确认失败')
    },
  })
}

/** 教师拒绝认领 */
export function useRejectClaim() {
  const queryClient = useQueryClient()
  const { showSuccess, showError } = useToast()

  return useMutation({
    mutationFn: async ({ itemId, claimId }: { itemId: number; claimId: number }) => {
      return await lostFoundApi.rejectClaim(itemId, claimId)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teacher-lost-found'] })
      queryClient.invalidateQueries({ queryKey: ['teacher-lost-found-detail'] })
      showSuccess('已拒绝认领')
    },
    onError: () => {
      showError('拒绝失败')
    },
  })
}

// ============== 学生端 ==============

/** 学生浏览物品列表 */
export function useStudentLostFoundItems(params?: () => LostFoundQueryParams) {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['student-lost-found', params?.()],
    queryFn: async () => {
      return await lostFoundApi.getStudentLostFoundItems(params?.())
    },
    staleTime: 1000 * 60 * 2,
  })

  return { data, isPending, error, refetch }
}

/** 学生查看物品详情 */
export function useStudentLostFoundDetail(id: () => number | undefined) {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['student-lost-found-detail', id()],
    queryFn: async () => {
      return await lostFoundApi.getStudentLostFoundDetail(id()!)
    },
    enabled: () => !!id(),
    staleTime: 1000 * 60 * 2,
  })

  return { data, isPending, error, refetch }
}

/** 学生发表评论 */
export function useCreateLostFoundComment() {
  const queryClient = useQueryClient()
  const { showSuccess, showError } = useToast()

  return useMutation({
    mutationFn: async ({ itemId, data }: { itemId: number; data: CreateLostFoundCommentRequest }) => {
      return await lostFoundApi.createLostFoundComment(itemId, data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['student-lost-found-detail'] })
      showSuccess('评论成功')
    },
    onError: () => {
      showError('评论失败')
    },
  })
}

/** 学生认领物品 */
export function useClaimLostFoundItem() {
  const queryClient = useQueryClient()
  const { showSuccess, showError } = useToast()

  return useMutation({
    mutationFn: async ({ itemId, data }: { itemId: number; data: CreateLostFoundClaimRequest }) => {
      return await lostFoundApi.claimLostFoundItem(itemId, data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['student-lost-found'] })
      queryClient.invalidateQueries({ queryKey: ['student-lost-found-detail'] })
      showSuccess('认领成功')
    },
    onError: () => {
      showError('认领失败')
    },
  })
}
```

- [ ] **Step 2: 注册导出**

修改 `frontend-v3/src/composables/index.ts`，添加：

```typescript
export {
  useTeacherLostFoundItems,
  useTeacherLostFoundDetail,
  useCreateLostFoundItem,
  useDeleteLostFoundItem,
  useConfirmClaim,
  useRejectClaim,
  useStudentLostFoundItems,
  useStudentLostFoundDetail,
  useCreateLostFoundComment,
  useClaimLostFoundItem,
} from './useLostFound'
```

- [ ] **Step 3: Commit**

```bash
git add frontend-v3/src/composables/useLostFound.ts frontend-v3/src/composables/index.ts
git commit -m "feat(lost-found): add TanStack Query composables"
```

---

## Task 9: 前端教师页面

**Files:**
- Create: `frontend-v3/src/views/teacher/LostFound.vue`
- Create: `frontend-v3/src/views/teacher/LostFoundDetail.vue`
- Create: `frontend-v3/src/views/teacher/LostFoundForm.vue`

- [ ] **Step 1: 创建教师列表页 LostFound.vue**

参考 `frontend-v3/src/views/teacher/TeacherQuestion.vue` 的布局模式，使用卡片视图展示物品列表，包含状态筛选、搜索框、创建按钮。

关键功能：
- 搜索框 + 状态筛选下拉
- 卡片列表展示物品（标题、描述、地点、状态标签、认领统计）
- 点击卡片跳转详情页
- 「发布新物品」按钮跳转表单页
- 分页

- [ ] **Step 2: 创建教师详情页 LostFoundDetail.vue**

参考 `frontend-v3/src/views/teacher/TeacherQuestion.vue` 的详情模式。

关键功能：
- 物品完整信息展示（标题、描述、地点、图片、状态）
- 编辑/删除按钮
- 评论区（显示真实姓名）
- 认领列表（显示认领者姓名、联系方式、认领说明、状态）
- 确认/拒绝认领按钮

- [ ] **Step 3: 创建教师表单页 LostFoundForm.vue**

关键功能：
- 标题输入框
- 描述文本域
- 地点输入框
- 图片上传（文件选择 + 预览）
- 表单验证
- 提交按钮（创建/编辑模式复用）

- [ ] **Step 4: 验证前端编译**

Run: `cd /home/yufeng/student-manage-v3-security/student-manager/frontend-v3 && pnpm build 2>&1 | tail -5`
Expected: 构建成功

- [ ] **Step 5: Commit**

```bash
git add frontend-v3/src/views/teacher/LostFound.vue frontend-v3/src/views/teacher/LostFoundDetail.vue frontend-v3/src/views/teacher/LostFoundForm.vue
git commit -m "feat(lost-found): add teacher pages for lost and found management"
```

---

## Task 10: 前端学生页面

**Files:**
- Create: `frontend-v3/src/views/student/LostFound.vue`
- Create: `frontend-v3/src/views/student/LostFoundDetail.vue`

- [ ] **Step 1: 创建学生列表页 LostFound.vue**

关键功能：
- 搜索框 + 状态筛选
- 卡片视图展示物品（标题、描述、地点、发布教师、状态标签）
- 点击卡片跳转详情页
- 分页

- [ ] **Step 2: 创建学生详情页 LostFoundDetail.vue**

关键功能：
- 物品信息展示（标题、描述、地点、图片、发布教师）
- 评论区（匿名显示，只有「匿名用户」）
- 评论输入框 + 提交按钮
- 认领按钮（弹窗填写联系方式和说明）
- 查看自己的认领状态

- [ ] **Step 3: 验证前端编译**

Run: `cd /home/yufeng/student-manage-v3-security/student-manager/frontend-v3 && pnpm build 2>&1 | tail -5`
Expected: 构建成功

- [ ] **Step 4: Commit**

```bash
git add frontend-v3/src/views/student/LostFound.vue frontend-v3/src/views/student/LostFoundDetail.vue
git commit -m "feat(lost-found): add student pages for lost and found browsing"
```

---

## Task 11: 路由与侧边栏注册

**Files:**
- Modify: `frontend-v3/src/router/index.ts`
- Modify: `frontend-v3/src/layouts/DashboardLayout.vue`

- [ ] **Step 1: 注册路由**

在 `frontend-v3/src/router/index.ts` 的教师路由 children 中添加：

```typescript
{ path: 'lost-found', name: 'TeacherLostFound', component: () => import('@/views/teacher/LostFound.vue') },
{ path: 'lost-found/create', name: 'TeacherLostFoundCreate', component: () => import('@/views/teacher/LostFoundForm.vue') },
{ path: 'lost-found/:id', name: 'TeacherLostFoundDetail', component: () => import('@/views/teacher/LostFoundDetail.vue') },
{ path: 'lost-found/:id/edit', name: 'TeacherLostFoundEdit', component: () => import('@/views/teacher/LostFoundForm.vue') },
```

在学生路由 children 中添加：

```typescript
{ path: 'lost-found', name: 'StudentLostFound', component: () => import('@/views/student/LostFound.vue') },
{ path: 'lost-found/:id', name: 'StudentLostFoundDetail', component: () => import('@/views/student/LostFoundDetail.vue') },
```

- [ ] **Step 2: 添加侧边栏导航**

在 `frontend-v3/src/layouts/DashboardLayout.vue` 的 `navItems` computed 中，教师导航添加：

```typescript
{ name: '失物招领', path: '/teacher/lost-found', icon: Search }
```

学生导航添加：

```typescript
{ name: '失物招领', path: '/student/lost-found', icon: Search }
```

注意：需要 import `Search` 图标（从 lucide-vue-next）。

- [ ] **Step 3: 验证前端编译和路由**

Run: `cd /home/yufeng/student-manage-v3-security/student-manager/frontend-v3 && pnpm build 2>&1 | tail -5`
Expected: 构建成功

- [ ] **Step 4: Commit**

```bash
git add frontend-v3/src/router/index.ts frontend-v3/src/layouts/DashboardLayout.vue
git commit -m "feat(lost-found): register routes and sidebar navigation"
```

---

## Task 12: 前端测试

**Files:**
- Create: `frontend-v3/test/views/LostFound.spec.ts`

- [ ] **Step 1: 创建前端测试**

```typescript
// frontend-v3/test/views/LostFound.spec.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { createRouter, createWebHistory } from 'vue-router'

// 基础冒烟测试
describe('LostFound Pages', () => {
  it('teacher LostFound page mounts', async () => {
    const { default: LostFound } = await import('@/views/teacher/LostFound.vue')
    const wrapper = mount(LostFound, {
      global: {
        plugins: [createTestingPinia()],
      },
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('student LostFound page mounts', async () => {
    const { default: LostFound } = await import('@/views/student/LostFound.vue')
    const wrapper = mount(LostFound, {
      global: {
        plugins: [createTestingPinia()],
      },
    })
    expect(wrapper.exists()).toBe(true)
  })
})
```

- [ ] **Step 2: 运行前端测试**

Run: `cd /home/yufeng/student-manage-v3-security/student-manager/frontend-v3 && pnpm test:run 2>&1 | tail -20`
Expected: 测试通过

- [ ] **Step 3: Commit**

```bash
git add frontend-v3/test/views/LostFound.spec.ts
git commit -m "test(lost-found): add frontend smoke tests"
```

---

## Task 13: 端到端验证

- [ ] **Step 1: 启动后端服务**

Run: `cd /home/yufeng/student-manage-v3-security/student-manager && make dev-backend`

- [ ] **Step 2: 启动前端服务**

Run: `cd /home/yufeng/student-manage-v3-security/student-manager && make dev-frontend`

- [ ] **Step 3: 运行全部后端测试**

Run: `cd /home/yufeng/student-manage-v3-security/student-manager && conda run -n student-manage pytest tests/ -v --tb=short 2>&1 | tail -30`
Expected: 全部通过

- [ ] **Step 4: 运行全部前端测试**

Run: `cd /home/yufeng/student-manage-v3-security/student-manager/frontend-v3 && pnpm test:run 2>&1 | tail -20`
Expected: 全部通过

- [ ] **Step 5: 浏览器验证**

1. 以教师身份登录，访问「失物招领」页面
2. 创建一个新物品（含图片）
3. 以学生身份登录，查看物品列表
4. 发表评论、认领物品
5. 以教师身份查看认领详情，确认认领
6. 验证隐私规则：学生看不到认领者信息

- [ ] **Step 6: 最终 Commit**

```bash
git add -A
git commit -m "feat(lost-found): complete lost and found feature implementation"
```
