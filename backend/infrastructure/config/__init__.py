"""
配置模块
集中管理应用配置和常量

使用示例：
    from infrastructure.config import get_settings, AppConfig
    
    settings = get_settings()
    redis_url = settings.redis.url
"""
from infrastructure.config.settings import (
    # Settings 配置类
    AppSettings,
    DatabaseSettings,
    RedisSettings,
    CacheSettings,
    SecuritySettings,
    RateLimitSettings,
    LogSettings,
    PaginationSettings,
    ScoreSettings,
    # 常量配置类（兼容旧代码）
    AppConfig,
    AuthConfig,
    ScoreConfig,
    PaginationConfig,
    CacheConfig,
    RateLimitConfig,
    LogConfig,
    DatabaseConfig,
    HttpStatus,
    ImportExportConfig,
    RATE_LIMITS,
    # 配置获取函数
    get_settings,
    reload_settings,
    init_settings,
    get_db_settings,
    get_redis_settings,
    get_cache_settings,
    get_security_settings,
    get_rate_limit_settings,
    get_log_settings,
)

__all__ = [
    # Settings 配置类
    'AppSettings',
    'DatabaseSettings',
    'RedisSettings',
    'CacheSettings',
    'SecuritySettings',
    'RateLimitSettings',
    'LogSettings',
    'PaginationSettings',
    'ScoreSettings',
    # 常量配置类
    'AppConfig',
    'AuthConfig',
    'ScoreConfig',
    'PaginationConfig',
    'CacheConfig',
    'RateLimitConfig',
    'LogConfig',
    'DatabaseConfig',
    'HttpStatus',
    'ImportExportConfig',
    'RATE_LIMITS',
    # 配置获取函数
    'get_settings',
    'reload_settings',
    'init_settings',
    'get_db_settings',
    'get_redis_settings',
    'get_cache_settings',
    'get_security_settings',
    'get_rate_limit_settings',
    'get_log_settings',
]
