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
    status: str = Field(default="open", max_length=20, description="状态: open|claiming|closed")
    publisher_id: int = Field(..., foreign_key="users.id", description="发布教师ID", index=True)
    created_at: datetime = Field(default_factory=get_now, description="创建时间")
    updated_at: datetime = Field(default_factory=get_now, description="更新时间")


class LostFoundComment(SQLModel, table=True):
    """失物招领评论表（仅学生可评论）

    外键指向 students.student_id（学号字符串），不是 users.id：
    学生的 JWT `sub` 是学号，此前误按 int 存 users.id 导致写入必 500。
    """
    __tablename__ = "lost_found_comments"

    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: int = Field(..., foreign_key="lost_found_items.id", description="关联物品ID", index=True)
    student_id: str = Field(
        ..., foreign_key="students.student_id", description="留言学生学号", index=True,
    )
    content: str = Field(..., description="留言内容")
    created_at: datetime = Field(default_factory=get_now, description="创建时间")


class LostFoundClaim(SQLModel, table=True):
    """失物招领认领记录表（仅学生可认领）

    外键指向 students.student_id，理由同 LostFoundComment。
    """
    __tablename__ = "lost_found_claims"

    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: int = Field(..., foreign_key="lost_found_items.id", description="关联物品ID", index=True)
    student_id: str = Field(
        ..., foreign_key="students.student_id", description="认领学生学号", index=True,
    )
    contact: str = Field(..., max_length=200, description="联系方式")
    message: Optional[str] = Field(default=None, description="认领说明")
    status: str = Field(default="pending", max_length=20, description="状态: pending|confirmed|rejected")
    created_at: datetime = Field(default_factory=get_now, description="创建时间")


class LostFoundClass(SQLModel, table=True):
    """失物招领可见班级关联表

    复合主键 (item_id, class_id)。无关联行 = 所有班级可见。
    """
    __tablename__ = "lost_found_classes"
    item_id: int = Field(..., foreign_key="lost_found_items.id", primary_key=True, description="物品ID")
    class_id: int = Field(..., foreign_key="classes.id", primary_key=True, description="班级ID")


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
    """评论响应（含学生信息）"""
    id: int
    item_id: int
    student_id: str
    student_name: Optional[str] = None
    content: str
    created_at: datetime


class LostFoundClaimResponse(SQLModel):
    """认领响应（含学生信息）"""
    id: int
    item_id: int
    student_id: str
    student_name: Optional[str] = None
    contact: str
    message: Optional[str]
    status: str
    created_at: datetime
