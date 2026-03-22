"""
日志配置
"""
import logging
import logging.handlers
import os
from app.core.config import get_settings


def setup_logging() -> logging.Logger:
    """
    设置应用日志
    
    Returns:
        配置好的日志记录器
    """
    settings = get_settings()
    
    # 获取日志级别
    level = getattr(logging, settings.log.level.upper(), logging.INFO)
    
    # 创建日志记录器
    logger = logging.getLogger("classhub")
    logger.setLevel(level)
    
    # 清除已有处理器
    logger.handlers.clear()
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器（如果配置了日志文件）
    if settings.log.file:
        log_dir = os.path.dirname(settings.log.file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            settings.log.file,
            maxBytes=settings.log.max_file_bytes,
            backupCount=settings.log.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# 全局日志记录器
logger = setup_logging()


# 便捷函数
def info(msg: str, *args, **kwargs):
    """记录INFO级别日志"""
    logger.info(msg, *args, **kwargs)


def debug(msg: str, *args, **kwargs):
    """记录DEBUG级别日志"""
    logger.debug(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs):
    """记录WARNING级别日志"""
    logger.warning(msg, *args, **kwargs)


def error(msg: str, *args, **kwargs):
    """记录ERROR级别日志"""
    logger.error(msg, *args, **kwargs)


def critical(msg: str, *args, **kwargs):
    """记录CRITICAL级别日志"""
    logger.critical(msg, *args, **kwargs)
