"""
统一配置管理系统
基于 Pydantic Settings，支持环境变量和配置文件
"""
import os
from typing import Optional, List
from functools import lru_cache
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """数据库配置"""
    model_config = SettingsConfigDict(
        env_prefix="DB_",
        extra="ignore"
    )
    
    # 数据库路径（默认项目根目录/data/class_system.db）
    path: Optional[str] = Field(
        default=None,
        description="SQLite数据库文件路径"
    )
    
    # 连接超时（秒）
    timeout: int = Field(default=30, description="数据库连接超时时间")
    
    # 连接池配置
    pool_size: int = Field(default=5, description="连接池大小")
    max_overflow: int = Field(default=10, description="连接池溢出大小")
    pool_timeout: int = Field(default=30, description="连接池获取超时时间")
    
    @validator('path', pre=True, always=True)
    def set_default_path(cls, v):
        """设置默认数据库路径"""
        if v is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            return os.path.join(base_dir, 'data', 'class_system.db')
        return v


class RedisSettings(BaseSettings):
    """Redis配置"""
    model_config = SettingsConfigDict(
        env_prefix="REDIS_",
        extra="ignore"
    )
    
    # Redis URL
    url: str = Field(
        default="redis://localhost:6379",
        description="Redis连接URL"
    )
    
    # 连接池配置
    pool_size: int = Field(default=10, description="连接池大小")
    
    # 编码设置
    encoding: str = Field(default="utf-8", description="字符编码")
    decode_responses: bool = Field(default=True, description="是否解码响应")


class CacheSettings(BaseSettings):
    """缓存配置"""
    model_config = SettingsConfigDict(
        env_prefix="CACHE_",
        extra="ignore"
    )
    
    # 是否启用缓存
    enabled: bool = Field(default=True, description="是否启用缓存")
    
    # 默认TTL（秒）
    ttl: int = Field(default=60, description="默认缓存TTL")
    
    # 各模块TTL配置
    student_list_ttl: int = Field(default=60, description="学生列表缓存TTL")
    student_detail_ttl: int = Field(default=300, description="学生详情缓存TTL")
    stats_ttl: int = Field(default=60, description="统计数据缓存TTL")
    user_list_ttl: int = Field(default=300, description="用户列表缓存TTL")
    class_list_ttl: int = Field(default=1800, description="班级列表缓存TTL")
    audit_stats_ttl: int = Field(default=300, description="审计统计缓存TTL")


class SecuritySettings(BaseSettings):
    """安全配置"""
    model_config = SettingsConfigDict(
        env_prefix="SECURITY_",
        extra="ignore"
    )
    
    # Session配置
    secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        description="Session加密密钥"
    )
    session_max_age: int = Field(default=86400, description="Session有效期（秒）")
    
    # 密码策略
    password_min_length: int = Field(default=6, description="密码最小长度")
    username_min_length: int = Field(default=3, description="用户名最小长度")
    name_min_length: int = Field(default=1, description="姓名最小长度")
    
    # 登录锁定
    max_login_failures: int = Field(default=5, description="最大登录失败次数")
    lockout_duration_minutes: int = Field(default=30, description="登录锁定持续时间")
    
    # CORS配置
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="CORS允许的来源"
    )
    cors_allow_credentials: bool = Field(default=True, description="CORS允许凭证")
    cors_allow_methods: List[str] = Field(default=["*"], description="CORS允许的方法")
    cors_allow_headers: List[str] = Field(default=["*"], description="CORS允许的头部")


class RateLimitSettings(BaseSettings):
    """限流配置"""
    model_config = SettingsConfigDict(
        env_prefix="RATE_LIMIT_",
        extra="ignore"
    )
    
    # 是否启用限流
    enabled: bool = Field(default=True, description="是否启用限流")
    
    # 限流倍数因子（测试时可设置为更大值如 10 或 100）
    multiplier: int = Field(default=1, description="限流倍数因子，用于测试环境放宽限制")
    
    # 各接口限流配置（次数/窗口秒数）
    login_max_requests: int = Field(default=5, description="登录接口限流次数")
    login_window_seconds: int = Field(default=60, description="登录接口限流窗口")
    
    checkin_max_requests: int = Field(default=10, description="签到接口限流次数")
    checkin_window_seconds: int = Field(default=60, description="签到接口限流窗口")
    
    score_change_max_requests: int = Field(default=10, description="分数修改限流次数")
    score_change_window_seconds: int = Field(default=60, description="分数修改限流窗口")
    
    user_search_max_requests: int = Field(default=10, description="用户查询限流次数")
    user_search_window_seconds: int = Field(default=60, description="用户查询限流窗口")
    
    default_max_requests: int = Field(default=60, description="默认限流次数")
    default_window_seconds: int = Field(default=60, description="默认限流窗口")


class LogSettings(BaseSettings):
    """日志配置"""
    model_config = SettingsConfigDict(
        env_prefix="LOG_",
        extra="ignore"
    )
    
    # 日志级别
    level: str = Field(default="INFO", description="日志级别")
    
    # 文件配置
    max_file_bytes: int = Field(default=10*1024*1024, description="单个日志文件最大大小（字节）")
    backup_count: int = Field(default=5, description="备份文件数量")
    
    # 审计日志
    audit_retention_days: int = Field(default=90, description="审计日志保留天数")


class PaginationSettings(BaseSettings):
    """分页配置"""
    model_config = SettingsConfigDict(
        env_prefix="PAGINATION_",
        extra="ignore"
    )
    
    # 默认分页大小
    default_page_size: int = Field(default=20, description="默认每页数量")
    
    # 各模块最大限制
    max_audit_logs: int = Field(default=100, description="审计日志最大返回数量")
    max_checkin_records: int = Field(default=200, description="签到记录最大返回数量")
    max_score_logs: int = Field(default=100, description="分数日志最大返回数量")
    max_student_list: int = Field(default=1000, description="学生列表最大返回数量")
    
    # 分页参数
    audit_log_page_size: int = Field(default=100, description="审计日志默认分页大小")
    audit_log_max_page_size: int = Field(default=1000, description="审计日志最大分页大小")
    my_logs_page_size: int = Field(default=50, description="我的日志默认分页大小")
    my_logs_max_page_size: int = Field(default=200, description="我的日志最大分页大小")
    score_log_default_limit: int = Field(default=50, description="分数日志默认限制")
    score_log_max_limit: int = Field(default=100, description="分数日志最大限制")


class ScoreSettings(BaseSettings):
    """分数配置"""
    model_config = SettingsConfigDict(
        env_prefix="SCORE_",
        extra="ignore"
    )
    
    # 分数范围
    min_score: float = Field(default=0, description="最低分数")
    max_score: float = Field(default=100, description="最高分数")
    
    # 默认分数
    default_score: float = Field(default=70, description="学生默认分数")
    
    # 签到分数
    checkin_delta: float = Field(default=0.0, description="签到分数变动")
    checkin_reward: float = Field(default=0.5, description="签到奖励分数")
    late_penalty: float = Field(default=-0.2, description="迟到惩罚分数")


def _get_env_file_path() -> str:
    """获取环境配置文件路径"""
    # 如果设置了 ENV_FILE，直接使用
    env_file = os.getenv('ENV_FILE')
    if env_file:
        return env_file
    # 否则根据 ENV 环境变量选择
    env = os.getenv('ENV', 'production').lower()
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if env == 'testing':
        return os.path.join(base_dir, '.env.testing')
    elif env == 'development':
        return os.path.join(base_dir, '.env.development')
    return '.env'


class AppSettings(BaseSettings):
    """
    应用主配置类
    聚合所有子配置
    
    根据环境自动加载对应的配置文件:
    - export ENV=testing  -> 加载 .env.testing
    - export ENV=development -> 加载 .env.development
    - 默认 -> 加载 .env
    
    或者通过 ENV_FILE 指定配置文件:
    - export ENV_FILE=/path/to/.env.custom
    """
    # 动态选择配置文件（使用工厂函数）
    # 使用 '__' 作为嵌套配置的分隔符，如 DATABASE__PATH 映射到 database.path
    model_config = SettingsConfigDict(
        env_file=_get_env_file_path(),
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter='__'
    )
    
    # 应用基础配置
    name: str = Field(default="班级管理系统", description="应用名称")
    version: str = Field(default="2.0.0", description="应用版本")
    debug: bool = Field(default=False, description="调试模式")
    
    # 服务器配置
    host: str = Field(default="0.0.0.0", description="服务器监听地址")
    port: int = Field(default=8000, description="服务器端口")
    
    # 环境配置
    env: str = Field(default="production", description="运行环境")
    
    # 子配置
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    cache: CacheSettings = Field(default_factory=CacheSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)
    log: LogSettings = Field(default_factory=LogSettings)
    pagination: PaginationSettings = Field(default_factory=PaginationSettings)
    score: ScoreSettings = Field(default_factory=ScoreSettings)
    
    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.env.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.env.lower() == "production"


# ========== 常量配置（兼容旧代码，直接从 Settings 读取）==========

class AppConfig:
    """应用基础配置"""
    VERSION = AppSettings().version
    DEFAULT_PORT = AppSettings().port
    DEFAULT_HOST = AppSettings().host


class AuthConfig:
    """认证与安全配置"""
    _settings = SecuritySettings()
    SESSION_MAX_AGE_SECONDS = _settings.session_max_age
    PASSWORD_MIN_LENGTH = _settings.password_min_length
    USERNAME_MIN_LENGTH = _settings.username_min_length
    NAME_MIN_LENGTH = _settings.name_min_length
    MAX_LOGIN_FAILURES = _settings.max_login_failures
    LOCKOUT_DURATION_MINUTES = _settings.lockout_duration_minutes


class ScoreConfig:
    """分数相关配置"""
    _settings = ScoreSettings()
    MIN_SCORE = _settings.min_score
    MAX_SCORE = _settings.max_score
    DEFAULT_SCORE = _settings.default_score
    CHECKIN_SCORE_DELTA = _settings.checkin_delta


class PaginationConfig:
    """分页配置"""
    _settings = PaginationSettings()
    DEFAULT_PAGE_SIZE = _settings.default_page_size
    MAX_AUDIT_LOGS = _settings.max_audit_logs
    MAX_CHECKIN_RECORDS = _settings.max_checkin_records
    MAX_SCORE_LOGS = _settings.max_score_logs
    MAX_STUDENT_LIST = _settings.max_student_list
    AUDIT_LOG_PAGE_SIZE = _settings.audit_log_page_size
    AUDIT_LOG_MAX_PAGE_SIZE = _settings.audit_log_max_page_size
    MY_LOGS_PAGE_SIZE = _settings.my_logs_page_size
    MY_LOGS_MAX_PAGE_SIZE = _settings.my_logs_max_page_size
    SCORE_LOG_DEFAULT_LIMIT = _settings.score_log_default_limit
    SCORE_LOG_MAX_LIMIT = _settings.score_log_max_limit


class CacheConfig:
    """缓存配置"""
    _settings = CacheSettings()
    DEFAULT_TTL_SECONDS = _settings.ttl
    STUDENT_LIST_TTL_SECONDS = _settings.student_list_ttl
    STUDENT_DETAIL_TTL_SECONDS = _settings.student_detail_ttl
    STATS_TTL_SECONDS = _settings.stats_ttl
    USER_LIST_TTL_SECONDS = _settings.user_list_ttl
    CLASS_LIST_TTL_SECONDS = _settings.class_list_ttl
    AUDIT_STATS_TTL_SECONDS = _settings.audit_stats_ttl
    CACHE_DECORATOR_DEFAULT_TTL = 300  # 默认5分钟
    CACHE_MIDDLEWARE_TTL = _settings.ttl


class RateLimitConfig:
    """限流配置 - 注意：在模块导入时初始化，如需动态配置请直接使用 get_settings().rate_limit"""
    _settings = RateLimitSettings()
    ENABLED = _settings.enabled
    MULTIPLIER = _settings.multiplier
    LOGIN_MAX_REQUESTS = _settings.login_max_requests
    LOGIN_WINDOW_SECONDS = _settings.login_window_seconds
    CHECKIN_MAX_REQUESTS = _settings.checkin_max_requests
    CHECKIN_WINDOW_SECONDS = _settings.checkin_window_seconds
    SCORE_CHANGE_MAX_REQUESTS = _settings.score_change_max_requests
    SCORE_CHANGE_WINDOW_SECONDS = _settings.score_change_window_seconds
    USER_SEARCH_MAX_REQUESTS = _settings.user_search_max_requests
    USER_SEARCH_WINDOW_SECONDS = _settings.user_search_window_seconds
    DEFAULT_MAX_REQUESTS = _settings.default_max_requests
    DEFAULT_WINDOW_SECONDS = _settings.default_window_seconds


class LogConfig:
    """日志配置"""
    _settings = LogSettings()
    MAX_LOG_FILE_BYTES = _settings.max_file_bytes
    BACKUP_COUNT = _settings.backup_count
    AUDIT_LOG_RETENTION_DAYS = _settings.audit_retention_days
    DEFAULT_LOG_LEVEL = _settings.level


class DatabaseConfig:
    """数据库配置"""
    _settings = DatabaseSettings()
    CONNECTION_TIMEOUT = _settings.timeout
    DEFAULT_DB_NAME = "class_system.db"


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


class ImportExportConfig:
    """导入导出配置"""
    EXCEL_START_ROW = 2
    MAX_IMPORT_ERRORS_DISPLAY = 10
    MAX_IMPORT_BATCH_SIZE = 1000


# 限流配置字典（兼容旧代码）
RATE_LIMITS = {
    'login': (RateLimitConfig.LOGIN_MAX_REQUESTS, RateLimitConfig.LOGIN_WINDOW_SECONDS),
    'checkin': (RateLimitConfig.CHECKIN_MAX_REQUESTS, RateLimitConfig.CHECKIN_WINDOW_SECONDS),
    'score_change': (RateLimitConfig.SCORE_CHANGE_MAX_REQUESTS, RateLimitConfig.SCORE_CHANGE_WINDOW_SECONDS),
    'user_search': (RateLimitConfig.USER_SEARCH_MAX_REQUESTS, RateLimitConfig.USER_SEARCH_WINDOW_SECONDS),
    'default': (RateLimitConfig.DEFAULT_MAX_REQUESTS, RateLimitConfig.DEFAULT_WINDOW_SECONDS),
}


# ========== 配置获取函数 ==========

_settings: Optional[AppSettings] = None


def get_settings() -> AppSettings:
    """获取应用配置（单例）"""
    global _settings
    if _settings is None:
        _settings = AppSettings()
    return _settings


def reload_settings() -> AppSettings:
    """重新加载配置（用于配置热更新）"""
    global _settings
    _settings = AppSettings()
    return _settings


def init_settings(env_file: Optional[str] = None) -> AppSettings:
    """初始化配置（指定环境文件）"""
    global _settings
    if env_file and os.path.exists(env_file):
        _settings = AppSettings(_env_file=env_file)
    else:
        _settings = AppSettings()
    return _settings


def get_test_settings() -> AppSettings:
    """获取测试环境配置
    
    自动加载 backend/.env.testing 配置文件
    包含测试优化的配置：
    - 使用测试数据库
    - 放宽限流限制
    - 启用调试模式
    """
    global _settings
    if _settings is None:
        # 获取 backend 目录下的 .env.testing
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        test_env_file = os.path.join(base_dir, '.env.testing')
        
        if os.path.exists(test_env_file):
            _settings = AppSettings(_env_file=test_env_file)
        else:
            # 如果测试配置文件不存在，使用默认配置
            _settings = AppSettings()
    return _settings


def get_db_settings() -> DatabaseSettings:
    """获取数据库配置"""
    return get_settings().database


def get_redis_settings() -> RedisSettings:
    """获取Redis配置"""
    return get_settings().redis


def get_cache_settings() -> CacheSettings:
    """获取缓存配置"""
    return get_settings().cache


def get_security_settings() -> SecuritySettings:
    """获取安全配置"""
    return get_settings().security


def get_rate_limit_settings() -> RateLimitSettings:
    """获取限流配置"""
    return get_settings().rate_limit


def get_log_settings() -> LogSettings:
    """获取日志配置"""
    return get_settings().log
