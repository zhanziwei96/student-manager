"""
XSS防护工具
对用户输入/输出进行HTML转义，防止跨站脚本攻击
"""
import html
from typing import Dict, Any, Union


def escape_html(text: Union[str, None]) -> str:
    """
    转义HTML特殊字符
    
    Args:
        text: 原始文本
        
    Returns:
        转义后的文本
        
    Example:
        '<script>alert("xss")</script>' -> '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;'
    """
    if text is None:
        return ''
    return html.escape(str(text))


def sanitize_dict(data: Dict[str, Any], fields_to_escape: list = None) -> Dict[str, Any]:
    """
    对字典中的指定字段进行HTML转义
    
    Args:
        data: 原始数据字典
        fields_to_escape: 需要转义的字段列表，None表示转义所有字符串字段
        
    Returns:
        转义后的字典
    """
    if not isinstance(data, dict):
        return data
    
    result = {}
    for key, value in data.items():
        # 如果指定了字段列表，只转义列表中的字段
        if fields_to_escape and key not in fields_to_escape:
            result[key] = value
        # 对字符串值进行转义
        elif isinstance(value, str):
            result[key] = escape_html(value)
        # 递归处理嵌套字典
        elif isinstance(value, dict):
            result[key] = sanitize_dict(value, fields_to_escape)
        # 递归处理列表
        elif isinstance(value, list):
            result[key] = [sanitize_dict(item, fields_to_escape) if isinstance(item, dict) else escape_html(item) if isinstance(item, str) else item for item in value]
        else:
            result[key] = value
    
    return result


# 学生数据需要转义的字段
STUDENT_FIELDS_TO_ESCAPE = ['student_id', 'name', 'class_name']

# 用户数据需要转义的字段
USER_FIELDS_TO_ESCAPE = ['username', 'name']

# 签到记录需要转义的字段
CHECKIN_FIELDS_TO_ESCAPE = ['student_id', 'student_name', 'class_name']


def sanitize_student_data(student: Dict[str, Any]) -> Dict[str, Any]:
    """转义学生数据"""
    return sanitize_dict(student, STUDENT_FIELDS_TO_ESCAPE)


def sanitize_student_list(students: list) -> list:
    """转义学生列表"""
    return [sanitize_student_data(s) for s in students]


def sanitize_user_data(user: Dict[str, Any]) -> Dict[str, Any]:
    """转义用户数据"""
    return sanitize_dict(user, USER_FIELDS_TO_ESCAPE)


def sanitize_checkin_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """转义签到记录"""
    return sanitize_dict(record, CHECKIN_FIELDS_TO_ESCAPE)
