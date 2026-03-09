"""
Flask 配置文件
支持开发环境、测试环境、生产环境
"""

import os

class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here-change-in-production'
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
    
    # 生产环境必须使用环境变量设置的 SECRET_KEY（如果没有则使用默认值）
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'student-manage-v2-secret-key-change-me'
    
    # 生产环境 Session 配置
    SESSION_COOKIE_SECURE = True  # 仅 HTTPS
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
