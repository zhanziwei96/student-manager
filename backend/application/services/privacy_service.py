"""
数据隐私服务 - 负责数据脱敏和权限控制
"""
from typing import Dict, List, Any, Optional


class PrivacyService:
    """数据隐私服务"""
    
    # 脱敏规则配置
    MASKING_RULES = {
        'student_id': {
            'admin': 'full',
            'teacher': 'partial',
            'student': 'self_only'
        },
        'name': {
            'admin': 'full',
            'teacher': 'partial',
            'student': 'self_only'
        },
        'class_name': {
            'admin': 'full',
            'teacher': 'full',
            'student': 'full'
        },
        'score': {
            'admin': 'full',
            'teacher': 'full',
            'student': 'self_only'
        }
    }
    
    def mask_string(self, s: str, keep_prefix: int = 2, keep_suffix: int = 2) -> str:
        """字符串脱敏"""
        if not s or len(s) <= keep_prefix + keep_suffix:
            return s
        
        prefix = s[:keep_prefix]
        suffix = s[-keep_suffix:]
        middle = '*' * (len(s) - keep_prefix - keep_suffix)
        return prefix + middle + suffix
    
    def mask_name(self, name: str) -> str:
        """姓名脱敏"""
        if not name:
            return name
        
        # 复姓处理
        compound_surnames = ['欧阳', '司马', '上官', '东方', '诸葛', '公孙', '慕容']
        for surname in compound_surnames:
            if name.startswith(surname):
                return surname + '*' * (len(name) - len(surname))
        
        # 单姓
        if len(name) == 2:
            return name[0] + '*'
        elif len(name) > 2:
            return name[0] + '*' * (len(name) - 1)
        return name
    
    def mask_student_id(self, student_id: str) -> str:
        """学号脱敏"""
        if len(student_id) >= 8:
            return self.mask_string(student_id, 4, 2)
        return self.mask_string(student_id, 2, 2)
    
    def mask_student_data(
        self,
        student: Dict[str, Any],
        is_admin: bool = False,
        current_user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        脱敏学生数据
        
        Args:
            student: 学生数据字典
            is_admin: 是否是管理员
            current_user_id: 当前用户ID（学生角色时用于判断只能看自己的数据）
        """
        if not student:
            return student
        
        result = student.copy()
        student_id = str(student.get('student_id', ''))
        
        # 管理员看所有
        if is_admin:
            return result
        
        # 判断是否是查看自己的数据
        is_self = current_user_id and str(current_user_id) == student_id
        
        if not is_self:
            # 非自己的数据进行脱敏
            if 'student_id' in result:
                result['student_id'] = self.mask_student_id(result['student_id'])
            if 'name' in result:
                result['name'] = self.mask_name(result['name'])
        
        return result
    
    def mask_checkin_record(
        self,
        record: Dict[str, Any],
        is_admin: bool = False,
        assigned_classes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        脱敏签到记录
        
        Args:
            record: 签到记录字典
            is_admin: 是否是管理员
            assigned_classes: 老师管理的班级列表
        """
        if not record:
            return record
        
        result = record.copy()
        record_class = record.get('class_name', '')
        
        # 管理员看所有
        if is_admin:
            return result
        
        # 检查班级权限
        if assigned_classes and record_class not in assigned_classes:
            # 无权查看，完全脱敏
            result['student_id'] = '****'
            result['student_name'] = '****'
            return result
        
        # 对学号和姓名脱敏
        if 'student_id' in result:
            result['student_id'] = self.mask_student_id(result['student_id'])
        if 'student_name' in result:
            result['student_name'] = self.mask_name(result['student_name'])
        
        return result
    
    def filter_by_class_permission(
        self,
        items: List[Dict[str, Any]],
        is_admin: bool = False,
        assigned_classes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        根据班级权限过滤数据
        
        Args:
            items: 数据列表（必须有class_name字段）
            is_admin: 是否是管理员
            assigned_classes: 老师管理的班级列表
        """
        if is_admin or not assigned_classes:
            return items
        
        return [
            item for item in items
            if item.get('class_name') in assigned_classes
        ]
