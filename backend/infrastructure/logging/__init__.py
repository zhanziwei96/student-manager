"""
日志模块
提供结构化日志和敏感信息脱敏
"""
from infrastructure.logging.logger import (
    logger,
    setup_logger,
    debug,
    info,
    warning,
    error,
    critical,
    exception,
    safe_log,
)
from infrastructure.logging.sensitive_filter import (
    SensitiveDataFilter,
    ClassNameFilter,
    StudentNameFilter,
    install_sensitive_filter,
    desensitize_text,
)

__all__ = [
    # 日志记录器
    'logger',
    'setup_logger',
    # 便捷函数
    'debug',
    'info',
    'warning',
    'error',
    'critical',
    'exception',
    'safe_log',
    # 过滤器
    'SensitiveDataFilter',
    'ClassNameFilter',
    'StudentNameFilter',
    'install_sensitive_filter',
    'desensitize_text',
]
