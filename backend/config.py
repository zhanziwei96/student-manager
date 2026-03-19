"""
Flask 配置文件
支持开发环境、测试环境、生产环境
"""

import os

import secrets

class Config:
    """基础配置"""
    # 从环境变量获取 SECRET_KEY，未设置时生成随机密钥
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 3600  # 1小时
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 最大16MB
    UPLOAD_FOLDER = 'uploads'
    
    # 数据库配置
    DB_ENV = os.environ.get('FLASK_ENV') or os.environ.get('DB_ENV', 'production')
    
class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    DB_ENV = 'development'
    
class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True
    DB_ENV = 'testing'
    
class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    TESTING = False
    DB_ENV = 'production'
    
    # 生产环境强制要求设置 SECRET_KEY 环境变量
    @classmethod
    def init_app(cls, app):
        if not os.environ.get('SECRET_KEY'):
            raise ValueError(
                "生产环境必须设置 SECRET_KEY 环境变量！\n"
                "请执行: export SECRET_KEY=$(openssl rand -hex 32)\n"
                "或在启动脚本中设置。"
            )
    
    # 生产环境 Session 配置
    # 如果设置了 DISABLE_SECURE_COOKIE 环境变量（用于本地测试），则允许非 HTTPS
    SESSION_COOKIE_SECURE = False if os.environ.get('DISABLE_SECURE_COOKIE') else True
    SESSION_COOKIE_HTTPONLY = True  # 防止 XSS
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF 保护
    
    # 生产环境建议配置
    # REMEMBER_COOKIE_SECURE = True
    # REMEMBER_COOKIE_HTTPONLY = True

# 配置映射
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
}
