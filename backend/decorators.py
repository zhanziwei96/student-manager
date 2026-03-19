"""
班级管理系统 - 权限装饰器模块
Phase 1: 核心安全装饰器
"""

import functools
from flask import request, jsonify, session
from datetime import datetime
from data_manager import get_user_by_id


def admin_required(f):
    """
    管理员权限验证装饰器
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # 先检查登录
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': '请先登录'}), 401
        
        # 检查管理员权限
        user = get_user_by_id(session['user_id'])
        if not user or not user.get('is_admin'):
            return jsonify({'success': False, 'message': '权限不足，需要管理员权限'}), 403
        
        # 检查账号状态
        if not user.get('is_active', 1):
            return jsonify({'success': False, 'message': '账号已被禁用'}), 403
        
        request.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function


def login_required(f):
    """
    增强版登录验证装饰器
    - 检查是否登录
    - 检查账号是否激活 (is_active)
    - 检查账号是否被锁定 (locked_until)
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. 检查是否登录
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': '请先登录'}), 401
        
        user_id = session['user_id']
        user = get_user_by_id(user_id)
        
        # 2. 检查用户是否存在
        if not user:
            session.clear()
            return jsonify({'success': False, 'message': '用户不存在'}), 401
        
        # 3. 检查账号是否激活
        if not user.get('is_active', 1):
            return jsonify({'success': False, 'message': '账号已被禁用'}), 403
        
        # 4. 检查账号是否被锁定
        locked_until = user.get('locked_until')
        if locked_until:
            # 解析锁定时间
            try:
                if isinstance(locked_until, str):
                    locked_time = datetime.fromisoformat(locked_until.replace('Z', '+00:00'))
                else:
                    locked_time = locked_until
                
                if datetime.now() < locked_time:
                    return jsonify({
                        'success': False, 
                        'message': f'账号已被锁定，请稍后再试'
                    }), 403
            except:
                pass  # 时间格式错误，忽略
        
        # 将用户信息存入 request 上下文，方便后续使用
        request.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function


def require_role(*roles):
    """
    角色权限控制装饰器
    
    用法:
        @require_role('admin')  # 仅管理员
        @require_role('admin', 'teacher')  # 管理员或老师
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # 先检查登录
            if 'user_id' not in session:
                return jsonify({'success': False, 'message': '请先登录'}), 401
            
            user_id = session['user_id']
            user = get_user_by_id(user_id)
            
            if not user:
                return jsonify({'success': False, 'message': '用户不存在'}), 401
            
            # 检查用户角色
            user_role = user.get('role', 'teacher')
            if user_role not in roles:
                return jsonify({
                    'success': False, 
                    'message': f'权限不足，需要角色: {", ".join(roles)}'
                }), 403
            
            request.current_user = user
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def require_class_access(f):
    """
    班级数据访问控制装饰器
    - 管理员可以访问所有班级
    - 老师只能访问 assigned_class 中绑定的班级
    - 从请求参数中获取 class_name 进行检查
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # 先检查登录
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': '请先登录'}), 401
        
        user_id = session['user_id']
        user = get_user_by_id(user_id)
        
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 401
        
        # 管理员直接放行
        if user.get('role') == 'admin' or user.get('is_admin'):
            request.current_user = user
            return f(*args, **kwargs)
        
        # 获取请求的班级
        class_name = None
        if request.is_json:
            class_name = request.json.get('class_name')
        if not class_name:
            class_name = request.args.get('class_name')
        if not class_name:
            class_name = request.form.get('class_name')
        
        # 如果没有指定班级，放行（可能是查询所有数据）
        if not class_name:
            request.current_user = user
            return f(*args, **kwargs)
        
        # 检查老师是否有权限访问该班级
        assigned_classes = user.get('assigned_class', '')
        if assigned_classes:
            allowed_classes = [c.strip() for c in assigned_classes.split(',')]
            if class_name not in allowed_classes:
                return jsonify({
                    'success': False,
                    'message': f'无权访问班级: {class_name}'
                }), 403
        
        request.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function


def audit_log(action, resource):
    """
    审计日志装饰器
    记录操作到 audit_logs 表
    
    用法:
        @audit_log('update', 'student_score')
        def api_update_score(student_id):
            ...
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # 执行原函数
            response = f(*args, **kwargs)
            
            # 记录审计日志
            try:
                from data_manager import get_db_connection
                
                user_id = session.get('user_id')
                user_name = session.get('username', 'anonymous')
                
                # 获取用户信息
                user_role = 'anonymous'
                if user_id:
                    user = get_user_by_id(user_id)
                    if user:
                        user_role = user.get('role', 'unknown')
                
                # 解析响应
                status_code = 200
                response_msg = ''
                try:
                    if hasattr(response, 'status_code'):
                        status_code = response.status_code
                    if hasattr(response, 'get_json'):
                        resp_data = response.get_json()
                        if resp_data:
                            response_msg = str(resp_data.get('message', ''))[:200]
                except:
                    pass
                
                # 获取请求参数
                params = {}
                try:
                    if request.is_json:
                        params = request.get_json()
                    else:
                        params = request.args.to_dict() or request.form.to_dict()
                    # 隐藏敏感信息
                    if 'password' in params:
                        params['password'] = '***'
                except:
                    pass
                
                # 写入审计日志
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO audit_logs 
                    (user_id, user_name, role, action, resource, resource_id, 
                     method, params, ip_address, user_agent, status_code, response_msg)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    user_name,
                    user_role,
                    action,
                    resource,
                    kwargs.get('student_id') or kwargs.get('class_name') or '',
                    request.method,
                    json.dumps(params, ensure_ascii=False) if params else None,
                    request.remote_addr,
                    request.user_agent.string[:200] if request.user_agent else None,
                    status_code,
                    response_msg
                ))
                conn.commit()
                
            except Exception as e:
                # 审计日志失败不应影响主业务
                print(f"[Audit Log Error] {e}")
            
            return response
        
        return decorated_function
    return decorator


# 简化导入
import json
