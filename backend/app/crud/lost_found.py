"""
失物招领 CRUD 操作
"""
from typing import List, Optional
from sqlmodel import Session, select, func, or_
from app.models.lost_found import LostFoundItem, LostFoundComment, LostFoundClaim
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
) -> LostFoundItem:
    """创建失物招领物品"""
    item = LostFoundItem(
        publisher_id=publisher_id,
        title=title,
        description=description,
        location=location,
        image_url=image_url,
        status="open",
    )
    session.add(item)
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
) -> tuple[List[LostFoundItem], int]:
    """获取物品列表（支持关键词搜索、状态过滤、分页）"""
    query = select(LostFoundItem)

    if keyword:
        like_pattern = f"%{keyword}%"
        query = query.where(
            or_(
                LostFoundItem.title.contains(keyword),
                LostFoundItem.description.contains(keyword),
                LostFoundItem.location.contains(keyword),
            )
        )
    if status:
        query = query.where(LostFoundItem.status == status)

    # 统计总数
    count_query = select(func.count()).select_from(LostFoundItem)
    if keyword:
        count_query = count_query.where(
            or_(
                LostFoundItem.title.contains(keyword),
                LostFoundItem.description.contains(keyword),
                LostFoundItem.location.contains(keyword),
            )
        )
    if status:
        count_query = count_query.where(LostFoundItem.status == status)
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
) -> Optional[LostFoundItem]:
    """更新物品信息"""
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
