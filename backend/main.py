"""
班级管理系统 - DDD架构主入口
前后端完全分离，后端只提供API
"""
import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from infrastructure.persistence.database import Database
from infrastructure.security.rate_limiter import init_rate_limiter
from interface.api.student_controller import student_bp
from interface.api.user_controller import user_bp
from interface.api.checkin_controller import checkin_bp


def create_app() -> Flask:
    """
    应用工厂函数
    
    Returns:
        Flask应用实例
    """
    # 创建Flask应用
    app = Flask(__name__, static_folder='../frontend/dist', static_url_path='')
    
    # 配置
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(32))
    app.config['SESSION_TYPE'] = 'filesystem'
    
    # 跨域配置（开发环境）
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
            "supports_credentials": True
        }
    })
    
    # 初始化限流器
    init_rate_limiter(app)
    
    # 初始化数据库
    db = Database()
    db.init_tables()
    
    # 注册蓝图（按优先级顺序）
    # 1. API蓝图（具体路由优先）
    app.register_blueprint(student_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(checkin_bp)
    
    # 2. API路由兜底
    @app.route('/api/', defaults={'path': ''})
    @app.route('/api/<path:path>')
    def api_not_found(path):
        """API 404处理"""
        return {'success': False, 'message': 'API接口不存在'}, 404
    
    # 3. 静态文件和前端路由（最后）
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def catch_all(path):
        """
        处理前端路由
        所有非API请求都返回index.html，由Vue Router处理
        """
        if path.startswith('api/'):
            return {'success': False, 'message': 'API接口不存在'}, 404
        
        # 静态文件直接返回
        if path and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        
        # 其他请求返回index.html（前端路由）
        return send_from_directory(app.static_folder, 'index.html')
    
    return app


# 创建应用实例
app = create_app()

if __name__ == '__main__':
    import sys
    
    # 获取环境
    env = os.environ.get('FLASK_ENV', 'production')
    is_dev = env == 'development'
    
    print("=" * 50)
    print(f"班级管理系统 DDD架构")
    print("=" * 50)
    print(f"\n环境: {env}")
    print(f"后端API: http://localhost:5000")
    print(f"前端页面: http://localhost:3000 (开发服务器)")
    print("\n架构层次:")
    print("  - Interface (API层)")
    print("  - Application (应用层)")
    print("  - Domain (领域层)")
    print("  - Infrastructure (基础设施层)")
    print("\n按 Ctrl+C 停止服务")
    print("=" * 50)
    
    # 启动服务
    app.run(
        debug=is_dev,
        host='0.0.0.0',
        port=5000,
        threaded=True
    )
