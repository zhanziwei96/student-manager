"""
失物招领 CRUD 操作
"""
from typing import Dict, List, Optional
from sqlmodel import Session, select, func, or_
from app.models.lost_found import LostFoundItem, LostFoundComment, LostFoundClaim, LostFoundClass
from app.core.timezone import get_now


# ── 自定义异常 ──────────────────────────────────────────────


class DuplicateClaimError(Exception):
    """学生已认领过该物品"""
    pass


class ItemNotClaimableError(Exception):
    """物品不可认领（已关闭）"""
    pass


# ── Item CRUD ───────────────────────────────────────────────


def create_lost_found_item(
    session: Session,
    publisher_id: int,
    title: str,
    description: str,
    location: Optional[str] = None,
    image_url: Optional[str] = None,
    class_ids: Optional[List[int]] = None,
) -> LostFoundItem:
    """创建失物招领物品

    class_ids 为空/None = 所有班级可见（不写关联行）；非空则写 lost_found_classes 关联行。
    """
    item = LostFoundItem(
        publisher_id=publisher_id,
        title=title,
        description=description,
        location=location,
        image_url=image_url,
        status="open",
    )
    session.add(item)
    session.flush()  # 先拿到 item.id 再写关联行
    if class_ids:
        for class_id in class_ids:
            session.add(LostFoundClass(item_id=item.id, class_id=class_id))
    session.commit()
    session.refresh(item)
    return item


def get_lost_found_item(
    session: Session,
    item_id: int,
) -> Optional[LostFoundItem]:
    """获取单个物品"""
    return session.get(LostFoundItem, item_id)


def get_lost_found_items(
    session: Session,
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    viewer_class_id: Optional[int] = None,
    viewer_publisher_id: Optional[int] = None,
    viewer_class_ids: Optional[List[int]] = None,
) -> tuple[List[LostFoundItem], int]:
    """获取物品列表（支持关键词搜索、状态过滤、分页）

    三种可见性视角（互斥，按序判定；都不提供 = 不过滤，admin 用）：

    - viewer_class_ids（教师视角，需同时提供 viewer_publisher_id）：
      自己发布的 OR 可见范围含自己任一班级 OR 物品无任何关联行（全班级可见）；
      **空列表 = fail-closed，返回空结果**（教学班未关联班级的老师什么都看不到）。
    - viewer_class_id（学生视角）：关联表含本班 OR 物品无任何关联行（全班级可见）。
    """
    query = select(LostFoundItem)
    count_query = select(func.count()).select_from(LostFoundItem)

    if keyword:
        like_pattern = f"%{keyword}%"
        keyword_cond = or_(
            LostFoundItem.title.contains(keyword),
            LostFoundItem.description.contains(keyword),
            LostFoundItem.location.contains(keyword),
        )
        query = query.where(keyword_cond)
        count_query = count_query.where(keyword_cond)
    if status:
        query = query.where(LostFoundItem.status == status)
        count_query = count_query.where(LostFoundItem.status == status)

    has_any = select(LostFoundClass.item_id)

    if viewer_class_ids is not None:
        # 教师视角：可访问班级集合为空 → fail-closed，什么都不返回
        if not viewer_class_ids:
            return [], 0
        has_mine = select(LostFoundClass.item_id).where(
            LostFoundClass.class_id.in_(viewer_class_ids)
        )
        visibility = or_(
            LostFoundItem.publisher_id == viewer_publisher_id,
            LostFoundItem.id.in_(has_mine),
            ~LostFoundItem.id.in_(has_any),
        )
        query = query.where(visibility)
        count_query = count_query.where(visibility)
    elif viewer_class_id is not None:
        # 可见性：关联表含本班 OR 无关联行（与问答同一 or_/IN 模式）
        has_this = select(LostFoundClass.item_id).where(
            LostFoundClass.class_id == viewer_class_id
        )
        visibility = or_(
            LostFoundItem.id.in_(has_this),
            ~LostFoundItem.id.in_(has_any),
        )
        query = query.where(visibility)
        count_query = count_query.where(visibility)

    # 统计总数
    total = session.exec(count_query).one()

    # 分页
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
    class_ids: Optional[List[int]] = None,
) -> Optional[LostFoundItem]:
    """更新物品信息

    class_ids 为 None = 不动可见范围；提供（含空列表）= 整体替换关联行，
    空列表即恢复为所有班级可见。
    """
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

    if class_ids is not None:
        old_rows = session.exec(
            select(LostFoundClass).where(LostFoundClass.item_id == item_id)
        ).all()
        for row in old_rows:
            session.delete(row)
        for class_id in class_ids:
            session.add(LostFoundClass(item_id=item_id, class_id=class_id))

    item.updated_at = get_now()
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def get_item_class_ids(
    session: Session,
    item_ids: List[int],
) -> Dict[int, List[int]]:
    """批量获取物品的可见班级ID（供响应拼装；无关联行的物品不在结果中）"""
    if not item_ids:
        return {}
    rows = session.exec(
        select(LostFoundClass).where(LostFoundClass.item_id.in_(item_ids))
    ).all()
    result: Dict[int, List[int]] = {}
    for row in rows:
        result.setdefault(row.item_id, []).append(row.class_id)
    return result


def delete_lost_found_item(session: Session, item_id: int) -> bool:
    """删除物品（同时删除关联的评论和认领记录）"""
    item = session.get(LostFoundItem, item_id)
    if not item:
        return False

    # 删除关联评论
    comments = session.exec(
        select(LostFoundComment).where(LostFoundComment.item_id == item_id)
    ).all()
    for comment in comments:
        session.delete(comment)

    # 删除关联认领
    claims = session.exec(
        select(LostFoundClaim).where(LostFoundClaim.item_id == item_id)
    ).all()
    for claim in claims:
        session.delete(claim)

    # 删除可见班级关联行（与评论/认领一致显式删除，不依赖 DB 级联）
    class_rows = session.exec(
        select(LostFoundClass).where(LostFoundClass.item_id == item_id)
    ).all()
    for row in class_rows:
        session.delete(row)

    session.delete(item)
    session.commit()
    return True


def count_claims_by_status(session: Session, item_id: int, status: str) -> int:
    """统计指定物品在指定状态下的认领数量"""
    query = select(func.count()).select_from(LostFoundClaim).where(
        LostFoundClaim.item_id == item_id,
        LostFoundClaim.status == status,
    )
    return session.exec(query).one()


# ── Comment CRUD ────────────────────────────────────────────


def create_comment(
    session: Session,
    item_id: int,
    user_id: int,
    content: str,
) -> LostFoundComment:
    """创建评论"""
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
    """获取物品的所有评论（按时间正序）"""
    query = (
        select(LostFoundComment)
        .where(LostFoundComment.item_id == item_id)
        .order_by(LostFoundComment.created_at.asc())
    )
    return list(session.exec(query).all())


# ── Claim CRUD ──────────────────────────────────────────────


def create_claim(
    session: Session,
    item_id: int,
    student_id: int,
    contact: str,
    message: Optional[str] = None,
) -> LostFoundClaim:
    """创建认领（同一学生对同一物品只能认领一次，已关闭物品不可认领）"""
    # 检查物品是否存在
    item = session.get(LostFoundItem, item_id)
    if not item:
        raise ValueError("物品不存在")

    # 检查物品是否可认领
    if item.status == "closed":
        raise ItemNotClaimableError("该物品已关闭，不可认领")

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

    # 如果物品当前状态为 open，更新为 claiming
    if item.status == "open":
        item.status = "claiming"
        item.updated_at = get_now()
        session.add(item)

    session.commit()
    session.refresh(claim)
    return claim


def get_claims_by_item(session: Session, item_id: int) -> List[LostFoundClaim]:
    """获取物品的所有认领记录（按时间倒序）"""
    query = (
        select(LostFoundClaim)
        .where(LostFoundClaim.item_id == item_id)
        .order_by(LostFoundClaim.created_at.desc())
    )
    return list(session.exec(query).all())


def get_claim(session: Session, claim_id: int) -> Optional[LostFoundClaim]:
    """获取单个认领记录"""
    return session.get(LostFoundClaim, claim_id)


def get_student_claim(
    session: Session,
    item_id: int,
    student_id: int,
) -> Optional[LostFoundClaim]:
    """获取学生对指定物品的认领记录"""
    query = select(LostFoundClaim).where(
        LostFoundClaim.item_id == item_id,
        LostFoundClaim.student_id == student_id,
    )
    return session.exec(query).first()


def confirm_claim(
    session: Session,
    item_id: int,
    claim_id: int,
) -> Optional[LostFoundClaim]:
    """确认认领（拒绝其他待处理认领，关闭物品）"""
    claim = session.get(LostFoundClaim, claim_id)
    if not claim or claim.item_id != item_id:
        return None

    # 确认该认领
    claim.status = "confirmed"
    session.add(claim)

    # 拒绝其他待处理的认领
    other_claims = session.exec(
        select(LostFoundClaim).where(
            LostFoundClaim.item_id == item_id,
            LostFoundClaim.id != claim_id,
            LostFoundClaim.status == "pending",
        )
    ).all()
    for other in other_claims:
        other.status = "rejected"
        session.add(other)

    # 关闭物品
    item = session.get(LostFoundItem, item_id)
    if item:
        item.status = "closed"
        item.updated_at = get_now()
        session.add(item)

    session.commit()
    session.refresh(claim)
    return claim


def reject_claim(
    session: Session,
    item_id: int,
    claim_id: int,
) -> Optional[LostFoundClaim]:
    """拒绝认领（若无其他待处理认领则恢复物品为 open）"""
    claim = session.get(LostFoundClaim, claim_id)
    if not claim or claim.item_id != item_id:
        return None

    claim.status = "rejected"
    session.add(claim)

    # 检查是否还有其他待处理认领（排除当前认领）
    other_pending = session.exec(
        select(func.count()).select_from(LostFoundClaim).where(
            LostFoundClaim.item_id == item_id,
            LostFoundClaim.id != claim_id,
            LostFoundClaim.status == "pending",
        )
    ).one()
    if other_pending == 0:
        item = session.get(LostFoundItem, item_id)
        if item:
            item.status = "open"
            item.updated_at = get_now()
            session.add(item)

    session.commit()
    session.refresh(claim)
    return claim
