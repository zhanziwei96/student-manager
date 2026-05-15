"""
失物招领 CRUD 单元测试
"""
import time
import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.models.lost_found import LostFoundItem, LostFoundComment, LostFoundClaim
from app.models.user import User
from app.models.constants import UserRoleConst
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
def lost_found_engine():
    """创建包含失物招领表的内存数据库引擎"""
    from app.models import (  # noqa: F401 — 触发所有模型注册到 metadata
        Student, User, CheckinRecord, CourseSession, ScoreLog,
        AuditLog, SecurityAlert, CourseSchedule, DeviceBind,
    )
    from app.models.question import Question, Answer  # noqa: F401

    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(test_engine)
    try:
        yield test_engine
    finally:
        test_engine.dispose()


@pytest.fixture
def session(lost_found_engine) -> Session:
    """数据库会话 fixture"""
    with Session(lost_found_engine) as s:
        yield s


@pytest.fixture
def teacher(session):
    user = User(
        username="teacher1",
        name="教师一",
        password_hash="x",
        role=UserRoleConst.TEACHER,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def student(session):
    user = User(
        username="student1",
        name="学生一",
        password_hash="x",
        role=UserRoleConst.STUDENT,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def student2(session):
    user = User(
        username="student2",
        name="学生二",
        password_hash="x",
        role=UserRoleConst.STUDENT,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


class TestItemCRUD:
    """测试物品 CRUD"""

    def test_create_item(self, session, teacher):
        item = create_lost_found_item(
            session,
            publisher_id=teacher.id,
            title="黑色钱包",
            description="在教室捡到一个黑色钱包",
            location="教学楼A301",
        )
        assert item.id is not None
        assert item.title == "黑色钱包"
        assert item.status == "open"
        assert item.publisher_id == teacher.id

    def test_get_item(self, session, teacher):
        created = create_lost_found_item(
            session,
            publisher_id=teacher.id,
            title="钥匙串",
            description="一串钥匙",
        )
        fetched = get_lost_found_item(session, created.id)
        assert fetched is not None
        assert fetched.title == "钥匙串"

    def test_get_item_not_found(self, session):
        result = get_lost_found_item(session, 9999)
        assert result is None

    def test_get_items_with_keyword(self, session, teacher):
        create_lost_found_item(session, teacher.id, "黑色钱包", "皮质钱包")
        create_lost_found_item(session, teacher.id, "红色雨伞", "折叠伞")
        create_lost_found_item(session, teacher.id, "钥匙串", "含黑色钥匙扣", "图书馆")

        # 关键词匹配标题
        items, total = get_lost_found_items(session, keyword="钱包")
        assert total == 1
        assert items[0].title == "黑色钱包"

        # 关键词匹配描述（"钥匙串"标题和"含黑色钥匙扣"描述都匹配，但属于同一物品）
        items, total = get_lost_found_items(session, keyword="钥匙")
        assert total == 1
        assert items[0].title == "钥匙串"

        # 关键词匹配地点
        items, total = get_lost_found_items(session, keyword="图书馆")
        assert total == 1
        assert items[0].title == "钥匙串"

    def test_get_items_with_status(self, session, teacher):
        item = create_lost_found_item(session, teacher.id, "物品A", "描述A")
        create_lost_found_item(session, teacher.id, "物品B", "描述B")

        # 手动将 item A 设为 closed
        item.status = "closed"
        session.add(item)
        session.commit()

        items, total = get_lost_found_items(session, status="open")
        assert total == 1
        assert items[0].title == "物品B"

        items, total = get_lost_found_items(session, status="closed")
        assert total == 1
        assert items[0].title == "物品A"

    def test_update_item(self, session, teacher):
        item = create_lost_found_item(session, teacher.id, "旧标题", "旧描述")
        old_updated_at = item.updated_at

        # 等待一小段时间确保时间戳不同
        time.sleep(0.01)

        updated = update_lost_found_item(
            session, item.id, title="新标题", description="新描述",
        )
        assert updated.title == "新标题"
        assert updated.description == "新描述"
        assert updated.updated_at >= old_updated_at

    def test_update_item_not_found(self, session):
        result = update_lost_found_item(session, 9999, title="不存在")
        assert result is None

    def test_delete_item(self, session, teacher, student):
        item = create_lost_found_item(session, teacher.id, "待删除", "描述")
        create_comment(session, item.id, student.id, "评论1")
        create_claim(session, item.id, student.id, "13800000000")

        result = delete_lost_found_item(session, item.id)
        assert result is True

        # 验证物品已删除
        assert get_lost_found_item(session, item.id) is None
        # 验证关联评论已级联删除
        assert get_comments_by_item(session, item.id) == []
        # 验证关联认领已级联删除
        assert get_claims_by_item(session, item.id) == []

    def test_delete_item_not_found(self, session):
        result = delete_lost_found_item(session, 9999)
        assert result is False


class TestCommentCRUD:
    """测试评论 CRUD"""

    def test_create_comment(self, session, teacher, student):
        item = create_lost_found_item(session, teacher.id, "钱包", "描述")
        comment = create_comment(session, item.id, student.id, "这是我的钱包！")
        assert comment.id is not None
        assert comment.content == "这是我的钱包！"
        assert comment.item_id == item.id
        assert comment.user_id == student.id

    def test_get_comments(self, session, teacher, student):
        item = create_lost_found_item(session, teacher.id, "钱包", "描述")
        c1 = create_comment(session, item.id, student.id, "第一条")
        # 确保时间戳不同
        time.sleep(0.01)
        c2 = create_comment(session, item.id, student.id, "第二条")

        comments = get_comments_by_item(session, item.id)
        assert len(comments) == 2
        # 按时间正序排列
        assert comments[0].id == c1.id
        assert comments[1].id == c2.id


class TestClaimCRUD:
    """测试认领 CRUD"""

    def test_create_claim(self, session, teacher, student):
        item = create_lost_found_item(session, teacher.id, "钱包", "描述")
        claim = create_claim(session, item.id, student.id, "13800000000", "这是我的")

        assert claim.id is not None
        assert claim.status == "pending"
        assert claim.contact == "13800000000"
        assert claim.message == "这是我的"

        # 物品状态应变为 claiming
        refreshed = get_lost_found_item(session, item.id)
        assert refreshed.status == "claiming"

    def test_duplicate_claim(self, session, teacher, student):
        item = create_lost_found_item(session, teacher.id, "钱包", "描述")
        create_claim(session, item.id, student.id, "13800000000")

        with pytest.raises(DuplicateClaimError):
            create_claim(session, item.id, student.id, "13900000000")

    def test_claim_closed_item(self, session, teacher, student):
        item = create_lost_found_item(session, teacher.id, "钱包", "描述")
        # 手动关闭物品
        item.status = "closed"
        session.add(item)
        session.commit()

        with pytest.raises(ItemNotClaimableError):
            create_claim(session, item.id, student.id, "13800000000")

    def test_confirm_claim(self, session, teacher, student, student2):
        item = create_lost_found_item(session, teacher.id, "钱包", "描述")
        claim1 = create_claim(session, item.id, student.id, "13800000000")
        claim2 = create_claim(session, item.id, student2.id, "13900000000")

        confirmed = confirm_claim(session, item.id, claim1.id)
        assert confirmed.status == "confirmed"

        # 另一条认领应被拒绝
        refreshed_c2 = session.get(LostFoundClaim, claim2.id)
        assert refreshed_c2.status == "rejected"

        # 物品应关闭
        refreshed_item = get_lost_found_item(session, item.id)
        assert refreshed_item.status == "closed"

    def test_reject_claim_restores_open(self, session, teacher, student):
        item = create_lost_found_item(session, teacher.id, "钱包", "描述")
        claim = create_claim(session, item.id, student.id, "13800000000")
        assert get_lost_found_item(session, item.id).status == "claiming"

        rejected = reject_claim(session, item.id, claim.id)
        assert rejected.status == "rejected"

        # 没有其他待处理认领，物品应恢复为 open
        refreshed_item = get_lost_found_item(session, item.id)
        assert refreshed_item.status == "open"

    def test_reject_claim_keeps_claiming(self, session, teacher, student, student2):
        item = create_lost_found_item(session, teacher.id, "钱包", "描述")
        claim1 = create_claim(session, item.id, student.id, "13800000000")
        claim2 = create_claim(session, item.id, student2.id, "13900000000")

        # 拒绝一条，但还有另一条 pending
        reject_claim(session, item.id, claim1.id)

        refreshed_item = get_lost_found_item(session, item.id)
        assert refreshed_item.status == "claiming"

    def test_count_pending_claims(self, session, teacher, student, student2):
        item = create_lost_found_item(session, teacher.id, "钱包", "描述")
        assert count_claims_by_status(session, item.id, "pending") == 0

        create_claim(session, item.id, student.id, "13800000000")
        assert count_claims_by_status(session, item.id, "pending") == 1

        create_claim(session, item.id, student2.id, "13900000000")
        assert count_claims_by_status(session, item.id, "pending") == 2

    def test_get_student_claim(self, session, teacher, student):
        item = create_lost_found_item(session, teacher.id, "钱包", "描述")
        claim = create_claim(session, item.id, student.id, "13800000000")

        found = get_student_claim(session, item.id, student.id)
        assert found is not None
        assert found.id == claim.id

    def test_get_student_claim_not_found(self, session, teacher, student):
        item = create_lost_found_item(session, teacher.id, "钱包", "描述")
        found = get_student_claim(session, item.id, student.id)
        assert found is None
