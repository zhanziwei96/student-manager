"""
签到记录仓储接口
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from domain.entities.checkin import Checkin
# Domain 层硬编码默认值（不依赖 Infrastructure 层）
DEFAULT_MAX_CHECKIN_RECORDS = 200


class CheckinRepository(ABC):
    """签到记录仓储接口"""
    
    @abstractmethod
    def find_by_id(self, checkin_id: int) -> Optional[Checkin]:
        """根据ID查找签到记录"""
        pass
    
    @abstractmethod
    def find_by_student_and_date(self, student_id: str, date: str) -> Optional[Checkin]:
        """查找学生某天的签到记录"""
        pass
    
    @abstractmethod
    def find_by_filters(
        self,
        student_id: Optional[str] = None,
        class_name: Optional[str] = None,
        date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = DEFAULT_MAX_CHECKIN_RECORDS
    ) -> List[Checkin]:
        """
        根据条件查询签到记录
        
        Args:
            student_id: 学生学号
            class_name: 班级名称
            date: 具体日期
            start_date: 开始日期
            end_date: 结束日期
            limit: 最大返回数量
        """
        pass
    
    @abstractmethod
    def find_by_class_today(self, class_name: str) -> List[Checkin]:
        """获取班级今日签到记录"""
        pass
    
    @abstractmethod
    def save(self, checkin: Checkin) -> Checkin:
        """保存签到记录"""
        pass
    
    @abstractmethod
    def count_by_student_and_date_range(
        self,
        student_id: str,
        start_date: str,
        end_date: str
    ) -> int:
        """统计学生在日期范围内的签到次数"""
        pass
    
    @abstractmethod
    def count_by_class_and_date(self, class_name: str, date: str) -> int:
        """统计班级某天的签到人数"""
        pass
