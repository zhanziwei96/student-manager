"""
班级管理系统 - 数据脱敏与隐私保护模块
Phase 2: 数据安全

根据用户角色返回不同脱敏级别的数据
"""

from typing import Dict, List, Any, Optional


# 脱敏规则配置
# role: 角色
# field: 字段名
# rule: 脱敏规则 (full-完整, partial-部分, mask-完全脱敏, self_only-只能看自己)
MASKING_RULES = {
    # 学生ID/学号
    'student_id': {
        'admin': 'full',          # 管理员：完整显示
        'teacher': 'partial',     # 老师：部分脱敏
        'student': 'self_only'    # 学生：只能看自己的
    },
    # 姓名
    'name': {
        'admin': 'full',
        'teacher': 'partial',     # 姓氏保留，名字脱敏
        'student': 'self_only'
    },
    # 班级
    'class_name': {
        'admin': 'full',
        'teacher': 'full',        # 老师需要看完整班级
        'student': 'full'         # 学生可以看自己班级
    },
    # 分数
    'score': {
        'admin': 'full',
        'teacher': 'full',
        'student': 'self_only'    # 学生只能看自己的分数
    },
    # 签到记录
    'checkin_records': {
        'admin': 'full',
        'teacher': 'class_only',  # 只能看本班学生的
        'student': 'self_only'
    }
}


def mask_string(s: str, keep_prefix: int = 2, keep_suffix: int = 2) -> str:
    """
    字符串脱敏
    保留前keep_prefix个字符和后keep_suffix个字符，中间用*代替
    
    例: mask_string("2513010101", 4, 2) -> "2513****01"
    """
    if not s or len(s) <= keep_prefix + keep_suffix:
        return s
    
    prefix = s[:keep_prefix]
    suffix = s[-keep_suffix:]
    middle = '*' * (len(s) - keep_prefix - keep_suffix)
    
    return prefix + middle + suffix


def mask_name(name: str) -> str:
    """
    姓名脱敏
    保留姓氏，名字用*代替
    
    例: mask_name("张三") -> "张*"
        mask_name("欧阳小明") -> "欧阳**"
    """
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
    else:
        return name


def apply_masking(value: Any, rule: str, user_role: str = None, 
                  current_user_id: str = None, data_owner_id: str = None) -> Any:
    """
    应用脱敏规则
    
    Args:
        value: 原始值
        rule: 脱敏规则
        user_role: 当前用户角色
        current_user_id: 当前用户ID
        data_owner_id: 数据所属用户ID
    
    Returns:
        脱敏后的值
    """
    if rule == 'full':
        return value
    
    if rule == 'mask':
        return '****'
    
    if rule == 'self_only':
        # 只能看自己的数据
        if current_user_id and data_owner_id and str(current_user_id) == str(data_owner_id):
            return value
        return '****'  # 不是自己的数据，完全脱敏
    
    if rule == 'partial':
        if isinstance(value, str):
            # 根据值的长度决定脱敏方式
            if len(value) >= 10:  # 学号类
                return mask_string(value, 4, 2)
            else:  # 姓名类
                return mask_name(value)
        return value
    
    if rule == 'class_only':
        # 班级权限检查由上层处理，这里只返回数据
        return value
    
    return value


def filter_student_data(student: Dict[str, Any], user_role: str = 'teacher',
                       current_user_id: str = None) -> Dict[str, Any]:
    """
    过滤单个学生数据，根据角色进行脱敏
    
    Args:
        student: 学生数据字典
        user_role: 当前用户角色 (admin/teacher/student)
        current_user_id: 当前用户ID（学生角色时需要）
    
    Returns:
        脱敏后的学生数据
    """
    if not student:
        return student
    
    # 创建副本，不修改原数据
    filtered = student.copy()
    data_owner_id = str(student.get('student_id', ''))
    
    # 应用脱敏规则
    for field, rules in MASKING_RULES.items():
        if field not in filtered:
            continue
        
        rule = rules.get(user_role, 'mask')
        original_value = filtered[field]
        
        filtered[field] = apply_masking(
            original_value, 
            rule, 
            user_role, 
            current_user_id, 
            data_owner_id
        )
    
    return filtered


def filter_students_list(students: List[Dict[str, Any]], user_role: str = 'teacher',
                        current_user_id: str = None) -> List[Dict[str, Any]]:
    """
    过滤学生列表数据
    
    Args:
        students: 学生数据列表
        user_role: 当前用户角色
        current_user_id: 当前用户ID
    
    Returns:
        脱敏后的学生列表
    """
    return [
        filter_student_data(student, user_role, current_user_id)
        for student in students
    ]


def filter_stats_data(stats: Dict[str, Any], user_role: str = 'teacher',
                     assigned_classes: List[str] = None) -> Dict[str, Any]:
    """
    过滤统计数据
    
    - admin: 看所有班级统计
    - teacher: 只看绑定班级的统计
    - student: 看全校概况，但班级详情只显示自己的班级
    """
    if not stats:
        return stats
    
    filtered = stats.copy()
    
    # 如果是老师，过滤班级统计
    if user_role == 'teacher' and assigned_classes and 'class_stats' in filtered:
        filtered['class_stats'] = [
            cs for cs in filtered['class_stats']
            if cs.get('class_name') in assigned_classes
        ]
        # 重新计算学生数
        filtered['student_count'] = sum(
            cs.get('student_count', 0) 
            for cs in filtered['class_stats']
        )
    
    # 学生只能看自己的排名信息
    if user_role == 'student' and 'top_students' in filtered:
        # 隐藏具体学生姓名，只显示排名和分数
        for i, student in enumerate(filtered['top_students']):
            student['name'] = f'第{i+1}名'
            student['student_id'] = mask_string(student.get('student_id', ''), 2, 2)
    
    return filtered


def filter_checkin_records(records: List[Dict[str, Any]], user_role: str = 'teacher',
                          current_user_id: str = None, 
                          assigned_classes: List[str] = None) -> List[Dict[str, Any]]:
    """
    过滤签到记录
    
    - admin: 看所有记录
    - teacher: 看本班记录
    - student: 只看自己的记录
    """
    if not records:
        return records
    
    filtered_records = []
    
    for record in records:
        # 获取记录所属的班级
        record_class = record.get('class_name', '')
        record_student_id = str(record.get('student_id', ''))
        
        # 权限检查
        if user_role == 'admin':
            # 管理员看所有
            filtered_records.append(record)
        
        elif user_role == 'teacher':
            # 老师看本班
            if not assigned_classes or record_class in assigned_classes:
                # 对学号和姓名脱敏
                filtered_record = record.copy()
                filtered_record['student_id'] = mask_string(record_student_id, 4, 2)
                filtered_record['student_name'] = mask_name(record.get('student_name', ''))
                filtered_records.append(filtered_record)
        
        elif user_role == 'student':
            # 学生只看自己的
            if str(current_user_id) == record_student_id:
                filtered_records.append(record)
    
    return filtered_records


def get_allowed_classes(user_role: str, assigned_classes_str: str = None) -> List[str]:
    """
    获取用户允许查看的班级列表
    
    Args:
        user_role: 用户角色
        assigned_classes_str: 老师绑定的班级字符串（逗号分隔）
    
    Returns:
        班级名称列表，None表示所有班级
    """
    if user_role == 'admin':
        return None  # None 表示允许所有班级
    
    if user_role == 'teacher' and assigned_classes_str:
        return [c.strip() for c in assigned_classes_str.split(',') if c.strip()]
    
    return []


# 辅助函数：检查用户是否有权限访问某条数据
def can_access_student(student: Dict[str, Any], user_role: str,
                      current_user_id: str = None, 
                      assigned_classes: List[str] = None) -> bool:
    """
    检查用户是否有权限访问某个学生的数据
    """
    if user_role == 'admin':
        return True
    
    student_class = student.get('class_name', '')
    student_id = str(student.get('student_id', ''))
    
    if user_role == 'teacher':
        # 老师只能看本班学生
        if assigned_classes:
            return student_class in assigned_classes
        return True  # 如果没有绑定班级，允许看所有（兼容旧数据）
    
    if user_role == 'student':
        # 学生只能看自己
        return str(current_user_id) == student_id
    
    return False
