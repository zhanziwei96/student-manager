"""
统一日志配置
替代 print 语句，提供结构化日志和敏感信息脱敏
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler

from infrastructure.logging.sensitive_filter import SensitiveDataFilter

# 日志格式
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DETAILED_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"


def setup_logger(name: str = "student_manage", level: int = logging.INFO) -> logging.Logger:
    """
    配置并返回日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别
        
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 添加敏感信息过滤器
    logger.addFilter(SensitiveDataFilter())
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(LOG_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器（按日期轮转）
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(DETAILED_FORMAT)
    file_handler.setFormatter(file_formatter)
    # 文件日志也添加脱敏
    file_handler.addFilter(SensitiveDataFilter())
    logger.addHandler(file_handler)
    
    # 轮转文件处理器（按大小）
    rotating_handler = RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    rotating_handler.setLevel(logging.INFO)
    rotating_handler.setFormatter(file_formatter)
    rotating_handler.addFilter(SensitiveDataFilter())
    logger.addHandler(rotating_handler)
    
    return logger


# 全局日志实例
logger = setup_logger()


# 便捷函数
def debug(msg: str, *args, **kwargs):
    """调试日志"""
    logger.debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs):
    """信息日志"""
    logger.info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs):
    """警告日志"""
    logger.warning(msg, *args, **kwargs)


def error(msg: str, *args, **kwargs):
    """错误日志"""
    logger.error(msg, *args, **kwargs)


def critical(msg: str, *args, **kwargs):
    """严重错误日志"""
    logger.critical(msg, *args, **kwargs)


def exception(msg: str, *args, **kwargs):
    """异常日志（自动记录堆栈）"""
    logger.exception(msg, *args, **kwargs)


# 脱敏便捷函数
def safe_log(msg: str, sensitive: bool = False) -> str:
    """
    返回脱敏后的日志消息
    
    Args:
        msg: 原始消息
        sensitive: 是否包含敏感信息
        
    Returns:
        str: 脱敏后的消息
    """
    if not sensitive:
        return msg
    
    from infrastructure.logging.sensitive_filter import desensitize_text
    return desensitize_text(msg)
