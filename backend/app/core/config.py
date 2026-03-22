"""
应用配置 - 支持多环境和嵌套配置
"""
import os
from typing import Optional, List
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _get_env_file() -> str:
    """根据 ENV 环境变量获取对应的环境文件"""
    env = os.getenv('ENV', 'production').lower()
    env_files = {
        'development': '.env.development',
        'testing': '.env.testing',
        'production': '.env.production'
    }
    return env_files.get(env, '.env')


class AppSettings(BaseSettings):
    """应用基础配置"""
    name: str = Field(default="班级管理系统", description="应用名称")
    version: str = Field(default="2.0.0", description="应用版本")
    debug: bool = Field(default=False, description="调试模式")
    env: str = Field(default="production", description="运行环境")
    host: str = Field(default="0.0.0.0", description="服务器监听地址")
    port: int = Field(default=8000, description="服务器端口")


class DatabaseSettings(BaseSettings):
    """数据库配置"""
    model_config = SettingsConfigDict(env_prefix="DATABASE_")
    
    path: Optional[str] = Field(default=None, description="数据库文件路径")
    timeout: int = Field(default=30, description="连接超时（秒）")


class RedisSettings(BaseSettings):
    """Redis配置 - 用于限流"""
    model_config = SettingsConfigDict(env_prefix="REDIS_")
    
    url: str = Field(default="redis://localhost:6379", description="Redis连接URL")
    pool_size: int = Field(default=10, description="连接池大小")


class SecuritySettings(BaseSettings):
    """安全配置"""
    model_config = SettingsConfigDict(env_prefix="SECURITY_")
    
    secret_key: str = Field(default="dev-secret-key-change-in-production", description="Session密钥")
    session_max_age: int = Field(default=86400, description="Session有效期（秒）")
    password_min_length: int = Field(default=6, description="密码最小长度")
    cors_origins: List[str] = Field(default=["http://localhost:3000"], description="CORS允许的来源")
    
    # 登录安全设置
    max_login_failures: int = Field(default=10, description="最大登录失败次数")
    lockout_duration_minutes: int = Field(default=30, description="账号锁定时间（分钟）")


class RateLimitSettings(BaseSettings):
    """限流配置"""
    model_config = SettingsConfigDict(env_prefix="RATE_LIMIT_")
    
    enabled: bool = Field(default=True, description="是否启用限流（需要Redis）")
    multiplier: int = Field(default=1, description="限流倍数因子")
    login_max_requests: int = Field(default=5, description="登录接口限流次数")
    login_window_seconds: int = Field(default=60, description="登录接口限流窗口")


class LogSettings(BaseSettings):
    """日志配置"""
    model_config = SettingsConfigDict(env_prefix="LOG_")
    
    level: str = Field(default="INFO", description="日志级别")
    file: Optional[str] = Field(default=None, description="日志文件路径")
    max_file_bytes: int = Field(default=10*1024*1024, description="单个日志文件最大大小")
    backup_count: int = Field(default=5, description="备份文件数量")


class PaginationSettings(BaseSettings):
    """分页配置"""
    model_config = SettingsConfigDict(env_prefix="PAGINATION_")
    
    default_page_size: int = Field(default=20, description="默认每页数量")
    score_log_default_limit: int = Field(default=50, description="分数日志默认查询条数")


class ScoreSettings(BaseSettings):
    """分数配置"""
    model_config = SettingsConfigDict(env_prefix="SCORE_")
    
    min_score: float = Field(default=0, description="最低分数")
    max_score: float = Field(default=100, description="最高分数")
    default_score: float = Field(default=70, description="学生默认分数")


class Settings(BaseSettings):
    """应用主配置类"""
    model_config = SettingsConfigDict(
        env_file=_get_env_file(),
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter='__'
    )
    
    # 应用基础配置
    app: AppSettings = Field(default_factory=AppSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)
    log: LogSettings = Field(default_factory=LogSettings)
    pagination: PaginationSettings = Field(default_factory=PaginationSettings)
    score: ScoreSettings = Field(default_factory=ScoreSettings)
    
    @property
    def is_development(self) -> bool:
        return self.app.env.lower() == "development"
    
    @property
    def is_testing(self) -> bool:
        return self.app.env.lower() == "testing"
    
    @property
    def is_production(self) -> bool:
        return self.app.env.lower() == "production"
    
    def get_database_path(self) -> str:
        """获取数据库路径"""
        if self.database.path:
            return self.database.path
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_dir, 'data', 'class_system.db')


# ========== 配置获取函数 ==========

_settings: Optional[Settings] = None


@lru_cache()
def get_settings() -> Settings:
    """获取应用配置（单例）"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """重新加载配置（用于配置热更新）"""
    global _settings
    _settings = Settings()
    return _settings


def init_settings(env_file: Optional[str] = None) -> Settings:
    """初始化配置（指定环境文件）"""
    global _settings
    if env_file and os.path.exists(env_file):
        _settings = Settings(_env_file=env_file)
    else:
        _settings = Settings()
    return _settings


# ========== 便捷访问函数 ==========

def get_db_settings() -> DatabaseSettings:
    """获取数据库配置"""
    return get_settings().database


def get_redis_settings() -> RedisSettings:
    """获取Redis配置"""
    return get_settings().redis


def get_security_settings() -> SecuritySettings:
    """获取安全配置"""
    return get_settings().security


# ========== 兼容性常量类 ==========

class AppConfig:
    """应用配置常量"""
    VERSION = "2.0.0"
    DEFAULT_PORT = 8000
    DEFAULT_HOST = "0.0.0.0"


class HttpStatus:
    """HTTP 状态码"""
    OK = 200
    CREATED = 201
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    INTERNAL_ERROR = 500
    SERVICE_UNAVAILABLE = 503
