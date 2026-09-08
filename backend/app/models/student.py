"""
学生模型 - SQLModel 版本
与现有 students 表结构兼容
"""
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Tuple
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Index, desc
from app.core.timezone import get_now


class StudentBase(SQLModel):
    """学生基础属性"""
    student_id: str = Field(..., description="学号", primary_key=True)
    name: str = Field(..., description="姓名")
    class_name: str = Field(default="未分班", description="班级（冗余快照）")
    class_id: Optional[int] = Field(
        default=None, foreign_key="classes.id", index=True,
        description="当前班级（冗余缓存，真源见 student_class_semesters）",
    )
    cohort_year: Optional[str] = Field(
        default=None, index=True, max_length=10,
        description="届（身份属性=入学年，不随转班更新）",
    )
    status: str = Field(
        default="active", max_length=20,
        description="学籍状态: active|suspended|withdrawn|graduated",
    )
    score: float = Field(default=0.0, index=True, description="分数（过渡期只读，Phase 4 废弃）")
    is_account_enabled: bool = Field(default=True, description="账户是否启用")


class Student(StudentBase, table=True):
    """学生表模型"""
    __tablename__ = "students"
    __table_args__ = (
        Index('idx_students_score', desc('score')),
        Index('idx_students_class_name', 'class_name'),
    )

    created_at: datetime = Field(default_factory=get_now, description="创建时间")
    last_login: Optional[datetime] = Field(default=None, description="最后登录时间")
    password_hash: Optional[str] = Field(default=None, description="密码哈希 (bcrypt)")
    login_fail_count: int = Field(default=0, description="登录失败次数")
    locked_until: Optional[datetime] = Field(default=None, description="锁定截止时间")
    version: int = Field(default=1, description="乐观锁版本号")
    
    def update_score(self, delta: float) -> Tuple[float, float]:
        """
        更新学生分数 - 领域方法

        封装业务规则：
        - 分数在 [min_score, max_score] 范围内
        - 使用 Decimal 避免浮点精度问题
        - 返回旧分数和新分数

        Args:
            delta: 分数变动值

        Returns:
            Tuple[float, float]: (旧分数, 新分数)
        """
        from app.core.config import get_settings
        settings = get_settings()

        # 使用 Decimal 进行精确计算
        old_score = Decimal(str(self.score))
        min_score = Decimal(str(settings.score.min_score))
        max_score = Decimal(str(settings.score.max_score))
        delta_dec = Decimal(str(delta))

        # 计算新分数并限制在范围内
        new_score_dec = old_score + delta_dec
        new_score_dec = max(min_score, min(max_score, new_score_dec))

        # 保留两位小数，四舍五入
        new_score_dec = new_score_dec.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        new_score = float(new_score_dec)
        self.score = new_score
        return float(old_score), new_score


class StudentCreate(StudentBase):
    """创建学生请求"""
    pass


class StudentUpdate(SQLModel):
    """更新学生请求"""
    name: Optional[str] = None
    class_name: Optional[str] = None
    score: Optional[float] = None


class StudentResponse(StudentBase):
    """学生响应"""
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True
