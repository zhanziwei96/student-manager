"""
课堂问答模型
"""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from app.core.timezone import get_now


class Question(SQLModel, table=True):
    """问题表"""
    __tablename__ = "questions"

    id: Optional[int] = Field(default=None, primary_key=True)
    teacher_id: int = Field(..., foreign_key="users.id", description="提问老师ID", index=True)
    class_id: Optional[int] = Field(
        default=None, foreign_key="classes.id", index=True,
        description="目标班级ID（None 表示所有班级可见）",
    )
    semester_id: Optional[int] = Field(
        default=None, foreign_key="semesters.id", index=True,
        description="学期ID（FK）",
    )
    content: str = Field(..., description="问题内容")
    status: str = Field(default="active", description="状态: active/closed")
    is_realtime: bool = Field(default=False, description="是否课堂实时提问")
    created_at: datetime = Field(default_factory=get_now, description="创建时间")
    closed_at: Optional[datetime] = Field(default=None, description="结束时间")


class Answer(SQLModel, table=True):
    """回答表"""
    __tablename__ = "answers"

    id: Optional[int] = Field(default=None, primary_key=True)
    question_id: int = Field(..., foreign_key="questions.id", description="所属问题ID", index=True)
    student_id: str = Field(..., description="回答者标识（学生学号或教师ID）", index=True)
    content: str = Field(..., description="回答内容")
    is_anonymous: bool = Field(default=False, description="是否匿名")
    is_starred: bool = Field(default=False, description="是否标记优秀")
    parent_id: Optional[int] = Field(default=None, foreign_key="answers.id", description="追问的父回答ID")
    created_at: datetime = Field(default_factory=get_now, description="创建时间")


# Pydantic 响应模型
class QuestionResponse(SQLModel):
    """问题响应"""
    id: int
    teacher_id: int
    class_name: Optional[str]
    content: str
    status: str
    is_realtime: bool
    created_at: datetime
    closed_at: Optional[datetime]


class AnswerResponse(SQLModel):
    """回答响应"""
    id: int
    question_id: int
    student_id: str
    student_name: Optional[str] = None
    content: str
    is_anonymous: bool
    is_starred: bool
    parent_id: Optional[int]
    created_at: datetime
