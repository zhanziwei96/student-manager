"""
应用配置 - 支持多环境和嵌套配置
"""
import os
from datetime import date
from pathlib import Path
from typing import Optional, List
from functools import lru_cache
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_env_file_path() -> str:
    """获取环境文件的完整路径

    根据 ENV 环境变量返回对应的环境文件完整路径。
    如果文件不存在，返回默认的 .env 文件路径。
    """
    env = os.getenv('ENV', 'production').lower()
    # config.py 在 app/core/，所以需要上溯两级到 backend 目录
    base_dir = Path(__file__).parent.parent.parent
    env_files = {
        'development': base_dir / '.env.development',
        'testing': base_dir / '.env.testing',
        'production': base_dir / '.env.production'
    }
    env_file = env_files.get(env, base_dir / '.env')
    return str(env_file) if env_file.exists() else str(base_dir / '.env')


def configure_environment() -> None:
    """配置环境 - 在应用启动前调用

    根据 ENV 环境变量设置 ENV_FILE 环境变量，确保配置加载使用正确的环境文件。
    如果 ENV_FILE 已设置，则不会覆盖。
    """
    if 'ENV_FILE' not in os.environ:
        os.environ['ENV_FILE'] = get_env_file_path()


def _get_env_file() -> str:
    """获取环境文件路径 - 供 Settings 类使用

    优先使用已设置的 ENV_FILE 环境变量，否则根据 ENV 计算。
    保持向后兼容性。
    """
    # 如果已通过 configure_environment() 设置，直接使用
    if 'ENV_FILE' in os.environ:
        return os.environ['ENV_FILE']
    # 否则根据 ENV 计算（向后兼容）
    return get_env_file_path()


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

    url: Optional[str] = Field(default=None, description="数据库连接URL（优先使用）")
    path: Optional[str] = Field(default=None, description="数据库文件路径（SQLite备用）")
    timeout: int = Field(default=30, description="连接超时（秒）")


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

    # Cookie 安全设置 (BE-006 修复)
    cookie_secure: bool = Field(default=False, description="Cookie Secure标志（生产环境应设为True）")

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """校验密钥强度 - SEC-004: 生产环境强制使用强密钥"""
        env = os.getenv("ENV", "production").lower()

        if env == "production":
            if v == "dev-secret-key-change-in-production":
                raise ValueError(
                    "生产环境 SECURITY_SECRET_KEY 必须使用自定义密钥，"
                    "当前使用的是默认开发密钥。请设置环境变量 SECURITY_SECRET_KEY"
                )
            if len(v) < 32:
                raise ValueError(
                    f"生产环境 SECURITY_SECRET_KEY 长度必须至少32字符，"
                    f"当前长度：{len(v)}"
                )

        return v


class RateLimitSettings(BaseSettings):
    """限流配置"""
    model_config = SettingsConfigDict(env_prefix="RATE_LIMIT_")

    enabled: bool = Field(default=True, description="是否启用限流（内存存储）")
    multiplier: int = Field(default=1, description="限流倍数因子")
    login_max_requests: int = Field(default=5, description="登录接口限流次数")
    login_window_seconds: int = Field(default=60, description="登录接口限流窗口")
    checkin_max_requests: int = Field(default=100, description="签到接口限流次数")
    checkin_window_seconds: int = Field(default=10, description="签到接口限流窗口")


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


class UploadSettings(BaseSettings):
    """文件上传配置 - SEC-001: 文件上传安全控制"""
    model_config = SettingsConfigDict(env_prefix="UPLOAD_")

    # 允许的文件扩展名白名单
    allowed_extensions: List[str] = Field(
        default=[".xlsx", ".xls"],
        description="允许上传的文件扩展名"
    )

    # 允许的文件MIME类型白名单
    allowed_content_types: List[str] = Field(
        default=[
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel",
        ],
        description="允许上传的文件MIME类型"
    )

    # 文件大小限制 (MB)
    max_file_size_mb: int = Field(default=10, description="最大文件大小(MB)")

    # 上传目录
    directory: str = Field(default="uploads", description="上传文件存储目录")

    # 是否使用UUID重命名
    use_uuid_filename: bool = Field(default=True, description="使用UUID重命名文件")


class TermSettings(BaseSettings):
    """学期配置 - 第二学期引入（semester 软归档 + 周次统一基准）"""
    model_config = SettingsConfigDict(env_prefix="TERM_")

    label: str = Field(default="2026-2027-1", description="当前学期标识（学年+学期号：1=秋季 2=春季）")
    start_date: date = Field(default=date(2026, 9, 7), description="学期开始日期（第1周周一）")
    total_weeks: int = Field(default=20, description="学期总周数")


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
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)
    log: LogSettings = Field(default_factory=LogSettings)
    pagination: PaginationSettings = Field(default_factory=PaginationSettings)
    score: ScoreSettings = Field(default_factory=ScoreSettings)
    upload: UploadSettings = Field(default_factory=UploadSettings)
    term: TermSettings = Field(default_factory=TermSettings, validation_alias="term_cfg")

    @property
    def is_development(self) -> bool:
        return self.app.env.lower() == "development"

    @property
    def is_testing(self) -> bool:
        return self.app.env.lower() == "testing"

    @property
    def is_production(self) -> bool:
        return self.app.env.lower() == "production"

    def get_database_url(self) -> str:
        """获取数据库连接 URL"""
        if self.database.url:
            return self.database.url
        return f"sqlite:///{self.get_database_path()}"

    def get_database_path(self) -> str:
        """获取数据库路径（SQLite 备用）"""
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
        # 临时修改环境变量来加载指定配置文件
        original_env_file = os.environ.get('ENV_FILE')
        os.environ['ENV_FILE'] = env_file
        try:
            _settings = Settings()
        finally:
            # 恢复原始环境变量
            if original_env_file is not None:
                os.environ['ENV_FILE'] = original_env_file
            elif 'ENV_FILE' in os.environ:
                del os.environ['ENV_FILE']
    else:
        _settings = Settings()
    return _settings


# ========== 便捷访问函数 ==========

def get_db_settings() -> DatabaseSettings:
    """获取数据库配置"""
    return get_settings().database


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
    TOO_MANY_REQUESTS = 429  # 限流状态码
    INTERNAL_ERROR = 500
    SERVICE_UNAVAILABLE = 503
