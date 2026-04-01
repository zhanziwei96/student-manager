"""
时区工具模块 - 统一时区处理

解决时区不一致问题：
- 所有模型使用 Asia/Shanghai 时区
- 提供统一的获取当前时间函数
"""
from datetime import datetime
from zoneinfo import ZoneInfo

# 应用默认时区：Asia/Shanghai
APP_TIMEZONE = ZoneInfo("Asia/Shanghai")


def get_now() -> datetime:
    """获取应用默认时区的当前时间

    Returns:
        datetime: 带时区信息的当前时间

    Example:
        >>> from app.core.timezone import get_now
        >>> now = get_now()
        >>> print(now)
        2026-04-01 15:30:00+08:00
    """
    return datetime.now(APP_TIMEZONE)


def get_now_naive() -> datetime:
    """获取当前时间（无时区信息，用于兼容旧代码）

    WARNING: 尽可能使用 get_now() 获取带时区的时间

    Returns:
        datetime: 无时区的当前时间
    """
    return datetime.now()


def convert_to_app_timezone(dt: datetime) -> datetime:
    """将时间转换为应用默认时区

    Args:
        dt: 输入的时间（可能带或不带时区）

    Returns:
        datetime: 带应用时区的时间
    """
    if dt.tzinfo is None:
        # 无时区，假定为应用时区
        return dt.replace(tzinfo=APP_TIMEZONE)
    # 有时区，转换到应用时区
    return dt.astimezone(APP_TIMEZONE)


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化时间为字符串

    Args:
        dt: 时间对象
        fmt: 格式字符串

    Returns:
        str: 格式化后的时间字符串
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=APP_TIMEZONE)
    return dt.strftime(fmt)
