"""
敏感信息过滤器
自动脱敏日志中的敏感信息
"""
import re
import logging
from typing import Pattern, List, Optional, Tuple, Union


class SensitiveDataFilter(logging.Filter):
    """
    敏感数据过滤器
    
    自动识别并脱敏日志中的敏感信息：
    - 密码、密钥
    - 身份证号、手机号
    - 数据库路径
    - Session Cookie
    - 学生姓名等个人信息
    """
    
    # 敏感字段名（key）
    SENSITIVE_KEYS = [
        'password', 'passwd', 'pwd',
        'secret', 'secret_key', 'private_key',
        'token', 'access_token', 'refresh_token',
        'authorization', 'auth',
        'cookie', 'session',
        'credit_card', 'card_no',
        'id_card', 'id_number', 'identity',
        'phone', 'mobile', 'tel',
        'email', 'address',
        'database', 'db_path', 'db_file',
    ]
    
    # 需要脱敏的正则模式
    PATTERNS = [
        # 密码值 (password=xxx, "password": "xxx")
        (re.compile(r'(password|passwd|pwd)["\']?\s*[:=]\s*["\']?[^\s,}&\]]+', re.IGNORECASE), r'\1=***'),
        
        # 密钥值
        (re.compile(r'(secret[_-]?key|private[_-]?key|api[_-]?key)["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_\-]{16,}', re.IGNORECASE), r'\1=***'),
        
        # Token值
        (re.compile(r'(token|access_token|refresh_token)["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_\-\.]+', re.IGNORECASE), r'\1=***'),
        
        # 身份证号 (18位)
        (re.compile(r'\b(\d{6})\d{8}(\d{4})'), r'\1********\2'),
        
        # 手机号 (11位)
        (re.compile(r'(\b1[3-9]\d)(\d{4})(\d{4}\b)'), r'\1****\3'),
        
        # 邮箱地址
        (re.compile(r'(\b[a-zA-Z0-9._%+-]{2})[a-zA-Z0-9._%+-]*(@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b)'), r'\1***\2'),
        
        # 数据库文件路径
        (re.compile(r'(/[^\s]*)(class_system[^\s]*\.db)', re.IGNORECASE), r'***/\2'),
        
        # Session ID / Cookie
        (re.compile(r'(session[_-]?id|sid|cookie)["\']?\s*[:=]\s*["\']?[a-f0-9]{16,}', re.IGNORECASE), r'\1=***'),
        
        # IP地址
        (re.compile(r'(\d{1,3}\.\d{1,3}\.)(\d{1,3}\.\d{1,3})'), r'\1***.***'),
    ]
    
    def __init__(self, name: str = "", extra_patterns: Optional[List[Tuple]] = None):
        """
        初始化过滤器
        
        Args:
            name: 过滤器名称
            extra_patterns: 额外的正则模式 (pattern, replacement)
        """
        super().__init__(name)
        self.patterns = self.PATTERNS.copy()
        if extra_patterns:
            self.patterns.extend(extra_patterns)
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        过滤日志记录，脱敏敏感信息
        
        Args:
            record: 日志记录对象
            
        Returns:
            bool: 是否保留该记录
        """
        # 处理日志消息
        if isinstance(record.msg, str):
            record.msg = self._desensitize(record.msg)
        
        # 处理格式化参数
        if record.args:
            record.args = tuple(
                self._desensitize(str(arg)) if isinstance(arg, str) else arg
                for arg in record.args
            )
        
        return True
    
    def _desensitize(self, text: str) -> str:
        """
        脱敏文本中的敏感信息
        
        Args:
            text: 原始文本
            
        Returns:
            str: 脱敏后的文本
        """
        if not isinstance(text, str):
            return text
        
        result = text
        for pattern, replacement in self.patterns:
            try:
                result = pattern.sub(replacement, result)
            except re.error:
                continue
        
        return result


class ClassNameFilter(logging.Filter):
    """
    班级名称过滤器（可选）
    
    如果业务需要保护班级名称隐私，可以使用此过滤器
    """
    
    def __init__(self, name: str = "", mask_class_name: bool = False):
        super().__init__(name)
        self.mask_class_name = mask_class_name
        self.pattern = re.compile(r'班级[：:]\s*([^\s,;]+)')
    
    def filter(self, record: logging.LogRecord) -> bool:
        if not self.mask_class_name:
            return True
        
        if isinstance(record.msg, str):
            record.msg = self.pattern.sub(r'班级: ***', record.msg)
        
        return True


class StudentNameFilter(logging.Filter):
    """
    学生姓名过滤器
    
    脱敏学生姓名，保护隐私
    """
    
    def __init__(self, name: str = "", mask_names: bool = False):
        super().__init__(name)
        self.mask_names = mask_names
        # 匹配常见中文姓名（2-4个字）
        self.pattern = re.compile(r'([\u4e00-\u9fa5])[\u4e00-\u9fa5]{1,3}')
    
    def filter(self, record: logging.LogRecord) -> bool:
        if not self.mask_names:
            return True
        
        if isinstance(record.msg, str):
            record.msg = self.pattern.sub(r'\1**', record.msg)
        
        return True


def install_sensitive_filter(logger_name: Optional[str] = None) -> None:
    """
    安装敏感信息过滤器到指定 logger
    
    Args:
        logger_name: logger 名称，None 表示根 logger
    """
    logger = logging.getLogger(logger_name)
    
    # 检查是否已安装
    for f in logger.filters:
        if isinstance(f, SensitiveDataFilter):
            return
    
    logger.addFilter(SensitiveDataFilter())
    logging.getLogger(__name__).info(f"敏感信息过滤器已安装到 logger: {logger_name or 'root'}")


# 便捷函数
def desensitize_text(text: str) -> str:
    """
    脱敏文本（用于非日志场景）
    
    Args:
        text: 原始文本
        
    Returns:
        str: 脱敏后的文本
    """
    filter_instance = SensitiveDataFilter()
    return filter_instance._desensitize(text)
