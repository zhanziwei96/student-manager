# backend/app/models/seat.py
"""座位系统模型：教室 / 座位 / 座位分配 / 会话级临时调座。"""
from datetime import datetime
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class Classroom(SQLModel, table=True):
    __tablename__ = "classrooms"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=50, unique=True, index=True)
    rows: int = Field(ge=1, le=50)
    cols: int = Field(ge=1, le=50)
    status: str = Field(default="active", max_length=20)  # active | archived
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Seat(SQLModel, table=True):
    __tablename__ = "seats"
    __table_args__ = (
        UniqueConstraint("classroom_id", "seat_no", name="uix_seat_no_per_classroom"),
        UniqueConstraint("classroom_id", "row", "col", name="uix_seat_pos_per_classroom"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    classroom_id: int = Field(foreign_key="classrooms.id", index=True)
    seat_no: str = Field(max_length=10)
    row: int = Field(ge=1)
    col: int = Field(ge=1)
    is_broken: bool = Field(default=False)


class SeatAssignment(SQLModel, table=True):
    """固定座位分配（每学期一份）。classroom_id 冗余自 seat.classroom_id，唯一约束需要。"""

    __tablename__ = "seat_assignments"
    __table_args__ = (
        UniqueConstraint("seat_id", "semester_id", name="uix_seat_semester"),
        UniqueConstraint("student_id", "semester_id", "classroom_id",
                         name="uix_student_semester_classroom"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    seat_id: int = Field(foreign_key="seats.id")
    student_id: str = Field(foreign_key="students.student_id", max_length=20, index=True)
    classroom_id: int = Field(foreign_key="classrooms.id")
    semester_id: int = Field(foreign_key="semesters.id")
    created_at: Optional[datetime] = None


class SeatSessionOverride(SQLModel, table=True):
    """教师临时调座：这节课有效，随 session 生命周期失效，不动固定分配。"""

    __tablename__ = "seat_session_overrides"

    session_id: int = Field(foreign_key="course_sessions.id", primary_key=True)
    student_id: str = Field(foreign_key="students.student_id", max_length=20, primary_key=True)
    seat_id: int = Field(foreign_key="seats.id")
    created_at: Optional[datetime] = None
