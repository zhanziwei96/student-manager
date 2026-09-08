"""
课程线模型 — 课程目录 / 教学班 / 选课
（方案 docs/SEMESTER_COHORT_REFACTOR_PLAN.md 2.2 课程线）
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Index, desc
from sqlmodel import SQLModel, Field, UniqueConstraint

from app.core.timezone import get_now


class CourseBase(SQLModel):
    """课程基础属性"""
    code: str = Field(..., description="课程编码（如 MATH1001，第一身份）", max_length=20)
    name: str = Field(..., description="课程名称（不唯一：同名不同层次常见）", max_length=100)
    department: str = Field(default="", description="开课院系", max_length=50)
    status: str = Field(default="active", description="状态: active|archived", max_length=20)


class Course(CourseBase, table=True):
    """课程目录表模型 — 一门课程一条记录（跨学期稳定）"""
    __tablename__ = "courses"
    __table_args__ = (
        UniqueConstraint('code', name='uix_course_code'),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=get_now, description="创建时间")


class CourseCreate(SQLModel):
    """创建课程请求"""
    code: str
    name: str
    department: str = ""


class CourseUpdate(SQLModel):
    """更新课程请求（全部 Optional）"""
    name: Optional[str] = None
    department: Optional[str] = None
    status: Optional[str] = None


class CourseResponse(CourseBase):
    """课程响应"""
    id: int


class CourseOfferingBase(SQLModel):
    """教学班基础属性"""
    course_id: int = Field(..., foreign_key="courses.id", description="课程ID", index=True)
    semester_id: int = Field(..., foreign_key="semesters.id", description="学期ID", index=True)
    teacher_id: Optional[int] = Field(
        default=None, foreign_key="users.id", index=True,
        description="教师ID（可空：先排课后定教师）",
    )
    teacher_name: str = Field(default="", description="教师姓名（冗余快照，免 JOIN 显示）", max_length=50)
    class_scope: str = Field(..., description="面向范围（如 计科1-2班，展示用）", max_length=100)
    capacity: Optional[int] = Field(default=None, description="容量")
    status: str = Field(default="active", description="状态: active|ended", max_length=20)


class CourseOffering(CourseOfferingBase, table=True):
    """教学班表模型 — 某学期某教师上某课程的一个班"""
    __tablename__ = "course_offerings"
    __table_args__ = (
        UniqueConstraint('course_id', 'semester_id', 'teacher_id', 'class_scope',
                         name='uix_offering'),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=get_now, description="创建时间")


class CourseOfferingCreate(SQLModel):
    """创建教学班请求"""
    course_id: int
    semester_id: int
    teacher_id: Optional[int] = None
    teacher_name: str = ""
    class_scope: str
    capacity: Optional[int] = None


class CourseOfferingUpdate(SQLModel):
    """更新教学班请求（全部 Optional）"""
    teacher_id: Optional[int] = None
    teacher_name: Optional[str] = None
    class_scope: Optional[str] = None
    capacity: Optional[int] = None
    status: Optional[str] = None


class CourseOfferingResponse(CourseOfferingBase):
    """教学班响应"""
    id: int


class EnrollmentBase(SQLModel):
    """选课基础属性"""
    student_id: str = Field(..., foreign_key="students.student_id", description="学号", index=True)
    offering_id: int = Field(..., foreign_key="course_offerings.id", description="教学班ID", index=True)
    semester_id: int = Field(..., foreign_key="semesters.id", description="学期ID（冗余第二 FK）", index=True)
    status: str = Field(default="enrolled", description="状态: enrolled|dropped（退课保留历史）", max_length=20)
    score: float = Field(default=0.0, index=True, description="个人成绩（该科目平时分，授课教师修改）")
    final_score: Optional[float] = Field(
        default=None, index=True,
        description="期末成绩（试卷=个人分；任务=小组同分；独立于个人成绩/小组成绩）",
    )


class Enrollment(EnrollmentBase, table=True):
    """选课表模型 — 成绩直接挂选课记录（吸收 student_subject_scores）"""
    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint('student_id', 'offering_id', name='uix_enrollment'),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    version: int = Field(default=1, description="乐观锁版本号（打分并发）")
    created_at: datetime = Field(default_factory=get_now, description="创建时间")
    updated_at: datetime = Field(default_factory=get_now, description="更新时间")


class EnrollmentResponse(EnrollmentBase):
    """选课响应"""
    id: int
    version: int


class EnrollmentScoreLog(SQLModel, table=True):
    """选课成绩变更日志（个人成绩/期末成绩）"""
    __tablename__ = "enrollment_score_logs"
    __table_args__ = (
        Index('idx_enrollment_score_logs_enrollment_created', 'enrollment_id', desc('created_at')),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    enrollment_id: int = Field(..., description="选课ID", index=True)
    old_score: Optional[float] = Field(default=None, description="旧分数")
    new_score: Optional[float] = Field(default=None, description="新分数")
    delta: Optional[float] = Field(default=None, description="变化值")
    reason: Optional[str] = Field(default=None, description="原因", max_length=200)
    operator: Optional[str] = Field(default=None, description="操作人", max_length=50)
    semester_id: Optional[int] = Field(
        default=None, foreign_key="semesters.id", index=True, description="学期ID",
    )
    created_at: datetime = Field(default_factory=get_now, description="创建时间")
