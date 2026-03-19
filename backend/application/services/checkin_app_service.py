"""
签到应用服务
"""
from datetime import datetime
from typing import List, Optional, Tuple

from domain.entities.checkin import Checkin, CheckinType
from domain.entities.student import Student
from domain.repositories.checkin_repository import CheckinRepository
from domain.repositories.student_repository import StudentRepository


class CheckinAppService:
    """签到应用服务"""
    
    # 签到奖励/惩罚配置
    CHECKIN_REWARD = 0.5  # 签到奖励分数
    LATE_PENALTY = -0.2   # 迟到惩罚（预留）
    
    def __init__(
        self,
        checkin_repo: CheckinRepository,
        student_repo: StudentRepository
    ):
        self._checkin_repo = checkin_repo
        self._student_repo = student_repo
    
    def student_checkin(
        self,
        student_id: str,
        name: str
    ) -> Tuple[bool, str, Optional[Checkin]]:
        """
        学生自主签到
        
        Args:
            student_id: 学号
            name: 姓名
            
        Returns:
            (success, message, checkin_record)
        """
        # 验证学生存在
        student = self._student_repo.find_by_id_str(student_id)
        if not student:
            return False, "学生不存在，请联系老师添加", None
        
        # 验证姓名匹配
        if student.name != name:
            return False, "学号与姓名不匹配", None
        
        # 检查今天是否已签到
        today = datetime.now().strftime('%Y-%m-%d')
        existing = self._checkin_repo.find_by_student_and_date(student_id, today)
        if existing:
            return False, f"今天({today})已经签到过了，请勿重复签到", existing
        
        # 创建签到记录
        checkin = Checkin(
            student_id=student_id,
            student_name=student.name,
            class_name=student.class_name,
            checkin_type=CheckinType.SELF,
            checkin_date=today,
            score_delta=self.CHECKIN_REWARD
        )
        
        # 保存签到记录
        self._checkin_repo.save(checkin)
        
        # 更新学生分数（加分奖励）
        student.change_score(self.CHECKIN_REWARD, f"签到奖励 +{self.CHECKIN_REWARD}")
        self._student_repo.save(student)
        
        return True, f"签到成功！获得{self.CHECKIN_REWARD}分奖励", checkin
    
    def teacher_checkin(
        self,
        student_identifier: str,
        created_by: int,
        is_student_id: bool = True
    ) -> Tuple[bool, str, Optional[Checkin], Optional[Student]]:
        """
        老师代签到
        
        Args:
            student_identifier: 学生学号或姓名
            created_by: 老师用户ID
            is_student_id: 是否通过学号查找
            
        Returns:
            (success, message, checkin_record, student)
        """
        # 查找学生
        if is_student_id:
            student = self._student_repo.find_by_id_str(student_identifier)
        else:
            # 通过姓名查找（可能返回多个，取第一个）
            students = self._student_repo.find_by_name(student_identifier)
            student = students[0] if students else None
        
        if not student:
            return False, "学生不存在", None, None
        
        # 检查今天是否已签到
        today = datetime.now().strftime('%Y-%m-%d')
        existing = self._checkin_repo.find_by_student_and_date(
            student.student_id.value, today
        )
        if existing:
            return False, f"{student.name}今天已经签到过了", existing, student
        
        # 创建签到记录
        checkin = Checkin(
            student_id=student.student_id.value,
            student_name=student.name,
            class_name=student.class_name,
            checkin_type=CheckinType.TEACHER,
            checkin_date=today,
            score_delta=self.CHECKIN_REWARD,
            created_by=created_by
        )
        
        self._checkin_repo.save(checkin)
        
        # 更新学生分数
        student.change_score(self.CHECKIN_REWARD, f"老师代签奖励 +{self.CHECKIN_REWARD}")
        self._student_repo.save(student)
        
        return True, f"代签成功！{student.name}获得{self.CHECKIN_REWARD}分奖励", checkin, student
    
    def get_checkin_records(
        self,
        student_id: Optional[str] = None,
        class_name: Optional[str] = None,
        date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[Checkin]:
        """获取签到记录"""
        return self._checkin_repo.find_by_filters(
            student_id=student_id,
            class_name=class_name,
            date=date,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
    
    def get_class_today_checkins(self, class_name: str) -> List[Checkin]:
        """获取班级今日签到列表"""
        return self._checkin_repo.find_by_class_today(class_name)
    
    def get_student_checkin_stats(
        self,
        student_id: str,
        month: Optional[str] = None
    ) -> dict:
        """
        获取学生签到统计
        
        Args:
            student_id: 学生学号
            month: 月份（YYYY-MM格式）
            
        Returns:
            统计信息字典
        """
        if month is None:
            month = datetime.now().strftime('%Y-%m')
        
        # 获取该月第一天和最后一天
        year, mon = month.split('-')
        start_date = f"{month}-01"
        
        # 计算月末日期
        if mon == '12':
            end_date = f"{int(year)+1}-01-01"
        else:
            end_date = f"{year}-{int(mon)+1:02d}-01"
        
        # 获取签到次数
        checkin_count = self._checkin_repo.count_by_student_and_date_range(
            student_id, start_date, end_date
        )
        
        return {
            'student_id': student_id,
            'month': month,
            'checkin_count': checkin_count,
            'total_reward': checkin_count * self.CHECKIN_REWARD
        }
