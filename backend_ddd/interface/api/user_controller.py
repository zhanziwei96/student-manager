"""
用户API控制器
"""
from flask import Blueprint, request, jsonify, session
from functools import wraps

from infrastructure.persistence.database import Database
from infrastructure.persistence.repositories.sqlite_user_repository import SQLiteUserRepository
from application.services.user_app_service import UserAppService
from application.dto.user_dto import CreateUserDTO, UpdateUserDTO


user_bp = Blueprint('users', __name__)


def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': '请先登录'}), 401
        if not session.get('is_admin'):
            return jsonify({'success': False, 'message': '需要管理员权限'}), 403
        return f(*args, **kwargs)
    return decorated_function


def get_user_service():
    """获取用户应用服务"""
    db = Database()
    repo = SQLiteUserRepository(db)
    return UserAppService(repo)


@user_bp.route('/api/admin/users', methods=['GET'])
@admin_required
def get_users():
    """获取所有用户"""
    try:
        service = get_user_service()
        users = service.get_all_users()
        return jsonify({
            'success': True,
            'data': [u.__dict__ for u in users]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@user_bp.route('/api/admin/users', methods=['POST'])
@admin_required
def create_user():
    """创建用户"""
    try:
        data = request.json
        dto = CreateUserDTO(
            username=data.get('username', '').strip(),
            password=data.get('password', '').strip(),
            name=data.get('name', '').strip(),
            role=data.get('role', 'teacher'),
            assigned_classes=data.get('assigned_classes', [])
        )
        
        service = get_user_service()
        user = service.create_user(dto)
        
        return jsonify({
            'success': True,
            'message': '用户创建成功',
            'data': user.__dict__
        })
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@user_bp.route('/api/admin/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    """更新用户"""
    try:
        data = request.json
        dto = UpdateUserDTO(
            name=data.get('name'),
            role=data.get('role'),
            assigned_classes=data.get('assigned_classes'),
            status=data.get('status')
        )
        
        service = get_user_service()
        user = service.update_user(user_id, dto)
        
        return jsonify({
            'success': True,
            'message': '用户更新成功',
            'data': user.__dict__
        })
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@user_bp.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """删除用户"""
    try:
        # 不能删除自己
        if user_id == session.get('user_id'):
            return jsonify({'success': False, 'message': '不能删除当前登录账号'}), 400
        
        service = get_user_service()
        service.delete_user(user_id)
        return jsonify({'success': True, 'message': '用户删除成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@user_bp.route('/api/admin/users/<int:user_id>/reset-password', methods=['POST'])
@admin_required
def reset_password(user_id):
    """重置密码"""
    try:
        data = request.json
        new_password = data.get('new_password', '').strip()
        
        if len(new_password) < 6:
            return jsonify({'success': False, 'message': '密码长度至少6位'}), 400
        
        service = get_user_service()
        service.reset_password(user_id, new_password)
        
        return jsonify({'success': True, 'message': '密码重置成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@user_bp.route('/api/admin/users/<int:user_id>/unlock', methods=['POST'])
@admin_required
def unlock_user(user_id):
    """解锁用户"""
    try:
        service = get_user_service()
        service.unlock_user(user_id)
        return jsonify({'success': True, 'message': '账号已解锁'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@user_bp.route('/api/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        service = get_user_service()
        user = service.authenticate_user(
            username, 
            password, 
            request.remote_addr
        )
        
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin()
            
            return jsonify({
                'success': True,
                'message': '登录成功',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'name': user.name,
                    'role': user.role.value,
                    'is_admin': user.is_admin()
                }
            })
        else:
            return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 403
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@user_bp.route('/api/logout', methods=['POST'])
def logout():
    """用户登出"""
    session.clear()
    return jsonify({'success': True, 'message': '登出成功'})
