# 班级管理系统综合安全方案

> 版本：v1.0  
> 创建时间：2026-03-18  
> 适用范围：student-manage-v3

---

## 📋 方案概述

本方案整合 **RBAC + 班级隔离 + 接口分级 + 审计日志**，形成四层防护体系，解决"任何人可查学生信息"等安全问题。

---

## 🏗️ 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│  第一层：身份认证层 (Authentication)                          │
│  └── JWT Token / Session + 密码强度策略                      │
├─────────────────────────────────────────────────────────────┤
│  第二层：权限控制层 (Authorization)                           │
│  └── RBAC 角色模型 + 班级数据隔离                            │
├─────────────────────────────────────────────────────────────┤
│  第三层：接口防护层 (API Protection)                          │
│  └── 接口分级 + 请求限流 + 参数校验                          │
├─────────────────────────────────────────────────────────────┤
│  第四层：审计监控层 (Audit & Monitor)                         │
│  └── 操作日志 + 异常告警 + 数据脱敏                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 👥 第一层：RBAC 角色权限模型

### 角色定义

```python
ROLES = {
    'admin': {
        'description': '系统管理员',
        'permissions': ['*'],  # 所有权限
        'data_scope': 'all'    # 全校数据
    },
    'teacher': {
        'description': '任课老师',
        'permissions': [
            'student.read',      # 查看学生
            'student.import',    # 导入学生
            'checkin.manage',    # 管理签到
            'score.manage',      # 管理分数
            'class.manage'       # 管理自己的班级
        ],
        'data_scope': 'assigned_class'  # 只能看分配的班级
    },
    'student': {
        'description': '学生',
        'permissions': [
            'self.read',         # 查看自己信息
            'self.checkin',      # 自己签到
            'self.query'         # 查询自己排名
        ],
        'data_scope': 'self'     # 只能看自己
    }
}
```

### 权限矩阵

| 接口 | Admin | Teacher | Student | Guest |
|------|-------|---------|---------|-------|
| `/api/students` | ✅ 全校 | ✅ 本班 | ❌ | ❌ |
| `/api/checkin/records` | ✅ 全校 | ✅ 本班 | ✅ 自己 | ❌ |
| `/api/stats` | ✅ 详细 | ✅ 本班 | ✅ 本班排名 | ✅ 仅总数 |
| `/api/student/query` | ✅ | ✅ | ✅ 自己 | ❌ |
| `/api/admin/*` | ✅ | ❌ | ❌ | ❌ |

---

## 🗄️ 数据库表结构

```sql
-- 用户表扩展
ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'teacher';
ALTER TABLE users ADD COLUMN assigned_class TEXT;  -- 老师绑定的班级（逗号分隔多个班级）
ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1;
ALTER TABLE users ADD COLUMN last_login_ip TEXT;
ALTER TABLE users ADD COLUMN login_fail_count INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN locked_until TIMESTAMP;

-- 权限审计日志表
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    user_name TEXT,
    role TEXT,
    action TEXT,           -- 操作类型：read/create/update/delete/login/logout
    resource TEXT,         -- 访问的资源：students/checkin/score等
    resource_id TEXT,      -- 资源标识（如学生ID）
    method TEXT,           -- HTTP方法：GET/POST/DELETE
    params TEXT,           -- 请求参数（JSON字符串）
    ip_address TEXT,
    user_agent TEXT,
    status_code INTEGER,   -- 响应状态码
    response_msg TEXT,     -- 响应消息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引加速查询
CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_time ON audit_logs(created_at);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_ip ON audit_logs(ip_address);

-- 异常行为检测表
CREATE TABLE security_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type TEXT,       -- 告警类型：mass_query/cross_class/after_hours
    severity TEXT,         -- 严重级别：high/medium/low
    description TEXT,      -- 告警描述
    related_user_id INTEGER,
    related_ip TEXT,
    is_resolved INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔐 第二层：权限装饰器体系

### decorators.py

```python
from functools import wraps
from flask import session, request, jsonify, g, current_app
import time
import threading
from datetime import datetime

def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': '请先登录'}), 401
        
        # 加载用户信息到 g 对象，避免重复查询
        user = get_user_by_id(session['user_id'])
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 401
        
        if not user.get('is_active', 1):
            return jsonify({'success': False, 'message': '用户已被禁用'}), 403
        
        # 检查账号锁定
        if user.get('locked_until') and datetime.now() < user.get('locked_until'):
            return jsonify({'success': False, 'message': '账号已锁定，请稍后重试'}), 403
        
        g.user = user
        g.user_id = user['id']
        g.user_role = user.get('role', 'teacher')
        
        return f(*args, **kwargs)
    return decorated_function

def require_role(roles):
    """角色权限验证装饰器
    
    使用示例：
        @require_role(['admin'])           # 仅管理员
        @require_role(['teacher', 'admin']) # 老师和管理员
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = getattr(g, 'user', None)
            if not user:
                return jsonify({'success': False, 'message': '未登录'}), 401
            
            user_role = user.get('role', 'guest')
            if user_role not in roles:
                # 记录越权访问尝试
                log_access_violation(user, request)
                return jsonify({'success': False, 'message': '权限不足，需要 %s 权限' % '/'.join(roles)}), 403
                
            return f(*args, **kwargs)
        return wrapper
    return decorator

def require_class_access(f):
    """班级数据隔离验证装饰器
    
    确保用户只能访问自己被授权的班级数据
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = getattr(g, 'user', None)
        if not user:
            return jsonify({'success': False, 'message': '未登录'}), 401
        
        # 管理员跳过班级限制
        if user['role'] == 'admin':
            return f(*args, **kwargs)
        
        # 从请求中获取班级参数（支持 query string 和 json body）
        requested_class = None
        if request.method == 'GET':
            requested_class = request.args.get('class_name')
        else:
            data = request.get_json(silent=True) or {}
            requested_class = data.get('class_name')
        
        # 老师只能访问自己绑定的班级
        if user['role'] == 'teacher':
            assigned = user.get('assigned_class', '')
            allowed_classes = [c.strip() for c in assigned.split(',') if c.strip()]
            
            # 如果请求指定了班级，检查是否有权限
            if requested_class and requested_class not in allowed_classes:
                log_access_violation(user, request, 
                    extra=f'尝试访问未授权班级: {requested_class}')
                return jsonify({
                    'success': False, 
                    'message': f'无权访问班级 "{requested_class}"，您只能访问: {", ".join(allowed_classes)}'
                }), 403
            
            # 将允许的班级列表存入 g，方便后续查询使用
            g.allowed_classes = allowed_classes
        
        # 学生只能访问自己的班级（通过学号关联）
        if user['role'] == 'student':
            student = get_student_by_id(user.get('student_id'))
            if requested_class and student and student['class_name'] != requested_class:
                return jsonify({'success': False, 'message': '无权访问该班级数据'}), 403
            g.student_class = student.get('class_name') if student else None
                
        return f(*args, **kwargs)
    return wrapper

def audit_log(action, resource):
    """操作审计日志装饰器
    
    使用示例：
        @audit_log('read', 'students')      # 读取学生列表
        @audit_log('delete', 'student')     # 删除学生
        @audit_log('update', 'score')       # 更新分数
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            user = getattr(g, 'user', {})
            
            # 执行原函数
            response = f(*args, **kwargs)
            
            # 解析响应状态
            status_code = 200
            if isinstance(response, tuple):
                status_code = response[1]
                response_data = response[0]
            else:
                response_data = response
            
            # 异步记录日志（不阻塞响应）
            try:
                log_entry = {
                    'user_id': user.get('id'),
                    'user_name': user.get('name', user.get('username', 'anonymous')),
                    'role': user.get('role', 'guest'),
                    'action': action,
                    'resource': resource,
                    'resource_id': kwargs.get('student_id') or kwargs.get('class_name'),
                    'method': request.method,
                    'params': filter_sensitive_params(request),
                    'ip_address': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', '')[:200],  # 限制长度
                    'status_code': status_code,
                    'response_time': int((time.time() - start_time) * 1000)  # 毫秒
                }
                # 异步写入
                threading.Thread(target=save_audit_log, args=(log_entry,), daemon=True).start()
            except Exception as e:
                # 日志失败不影响业务，但应记录到应用日志
                current_app.logger.error(f'审计日志记录失败: {e}')
                
            return response
        return wrapper
    return decorator

def rate_limit(requests_per_minute=60):
    """请求限流装饰器
    
    使用示例：
        @rate_limit(5)    # 每分钟最多5次请求
    """
    def decorator(f):
        # 使用内存存储，生产环境建议使用 Redis
        request_history = {}
        
        @wraps(f)
        def wrapper(*args, **kwargs):
            # 根据用户ID或IP限流
            user = getattr(g, 'user', None)
            key = str(user['id']) if user else request.remote_addr
            
            now = time.time()
            window_start = now - 60  # 60秒窗口
            
            # 清理过期记录
            if key in request_history:
                request_history[key] = [t for t in request_history[key] if t > window_start]
            else:
                request_history[key] = []
            
            # 检查是否超过限制
            if len(request_history[key]) >= requests_per_minute:
                return jsonify({
                    'success': False, 
                    'message': f'请求过于频繁，请稍后再试（限制：{requests_per_minute}/分钟）'
                }), 429
            
            request_history[key].append(now)
            return f(*args, **kwargs)
        return wrapper
    return decorator

# ==================== 辅助函数 ====================

def get_user_by_id(user_id):
    """根据ID获取用户信息"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, username, name, role, assigned_class, is_active, 
               last_login_ip, login_fail_count, locked_until
        FROM users WHERE id = ?
    ''', (user_id,))
    row = cursor.fetchone()
    return dict(row) if row else None

def get_student_by_id(student_id):
    """根据学号获取学生信息"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT student_id, name, class_name, score 
        FROM students WHERE student_id = ?
    ''', (student_id,))
    row = cursor.fetchone()
    return dict(row) if row else None

def filter_sensitive_params(request):
    """过滤敏感参数后再记录"""
    sensitive_fields = ['password', 'old_password', 'new_password', 'secret', 'token']
    
    params = {}
    
    # 处理 query string
    for key in request.args:
        params[key] = '***' if key in sensitive_fields else request.args.get(key)
    
    # 处理 json body
    if request.is_json:
        try:
            data = request.get_json()
            if isinstance(data, dict):
                for key in data:
                    params[key] = '***' if key in sensitive_fields else data[key]
        except:
            pass
    
    # 处理 form data
    for key in request.form:
        params[key] = '***' if key in sensitive_fields else request.form.get(key)
    
    return params

def log_access_violation(user, request, extra=''):
    """记录越权访问尝试"""
    try:
        log_entry = {
            'user_id': user.get('id') if user else None,
            'user_name': user.get('name', 'unknown') if user else 'unknown',
            'role': user.get('role', 'unknown') if user else 'unknown',
            'action': 'access_violation',
            'resource': request.path,
            'method': request.method,
            'ip_address': request.remote_addr,
            'response_msg': extra
        }
        threading.Thread(target=save_audit_log, args=(log_entry,), daemon=True).start()
    except:
        pass

def save_audit_log(log_entry):
    """保存审计日志到数据库"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO audit_logs 
            (user_id, user_name, role, action, resource, resource_id, method, params, 
             ip_address, user_agent, status_code)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            log_entry.get('user_id'),
            log_entry.get('user_name'),
            log_entry.get('role'),
            log_entry.get('action'),
            log_entry.get('resource'),
            log_entry.get('resource_id'),
            log_entry.get('method'),
            str(log_entry.get('params', {})),
            log_entry.get('ip_address'),
            log_entry.get('user_agent', ''),
            log_entry.get('status_code', 200)
        ))
        conn.commit()
    except Exception as e:
        print(f'保存审计日志失败: {e}')
```

---

## 🌐 第三层：接口分级保护

### 接口权限配置

```python
# permissions.py

# 公开接口（无需登录）
PUBLIC_ENDPOINTS = [
    {'path': '/api/stats/summary', 'methods': ['GET'], 'desc': '公开统计（仅总数，不含名单）'},
    {'path': '/api/checkin', 'methods': ['POST'], 'desc': '学生签到（需学号+姓名验证）'},
    {'path': '/api/student/query', 'methods': ['POST'], 'desc': '自助查询（只能查自己）'},
    {'path': '/api/class-session', 'methods': ['GET'], 'desc': '当前上课状态'},
    {'path': '/api/login', 'methods': ['POST'], 'desc': '登录接口'},
]

# 需要登录的接口
AUTHENTICATED_ENDPOINTS = [
    {'path': '/api/me', 'methods': ['GET'], 'desc': '当前用户信息'},
    {'path': '/api/change-password', 'methods': ['POST'], 'desc': '修改密码'},
    {'path': '/api/logout', 'methods': ['POST'], 'desc': '退出登录'},
]

# 老师权限接口
TEACHER_ENDPOINTS = [
    {'path': '/api/students', 'methods': ['GET', 'POST'], 'desc': '查看/添加学生（本班）'},
    {'path': '/api/students/import', 'methods': ['POST'], 'desc': '导入学生'},
    {'path': '/api/students/<id>/score', 'methods': ['POST'], 'desc': '更新学生分数'},
    {'path': '/api/checkin/records', 'methods': ['GET'], 'desc': '查看签到记录（本班）'},
    {'path': '/api/score/logs', 'methods': ['GET'], 'desc': '查看分数日志（本班）'},
    {'path': '/api/teacher-checkin', 'methods': ['POST'], 'desc': '老师代签'},
    {'path': '/api/class-session', 'methods': ['POST'], 'desc': '设置上课班级'},
    {'path': '/api/class-session/students', 'methods': ['GET'], 'desc': '获取班级学生签到状态'},
]

# 管理员权限接口
ADMIN_ENDPOINTS = [
    {'path': '/api/admin/reset-scores', 'methods': ['POST'], 'desc': '重置全校分数'},
    {'path': '/api/students/<id>', 'methods': ['DELETE'], 'desc': '删除学生'},
    {'path': '/api/class/<name>', 'methods': ['DELETE'], 'desc': '删除班级'},
    {'path': '/api/db-info', 'methods': ['GET'], 'desc': '数据库信息'},
    {'path': '/api/audit/logs', 'methods': ['GET'], 'desc': '审计日志查询'},
    {'path': '/api/audit/stats', 'methods': ['GET'], 'desc': '审计统计'},
]
```

### 路由实现示例

```python
# routes/students.py

from flask import Blueprint, request, jsonify, g
from decorators import login_required, require_role, require_class_access, audit_log, rate_limit
from privacy import filter_student_data, filter_students_list

students_bp = Blueprint('students', __name__)

@students_bp.route('/api/students', methods=['GET'])
@login_required
@require_role(['teacher', 'admin'])
@require_class_access
@audit_log('read', 'students')
def get_students():
    """获取学生列表
    
    权限控制：
    - 管理员：查看全校学生
    - 老师：只能查看自己绑定的班级
    """
    user = g.user
    
    # 获取查询参数
    class_name = request.args.get('class_name')
    
    if user['role'] == 'admin':
        # 管理员可以看全校，但如果指定了班级就只看该班级
        if class_name:
            students = get_students_by_class(class_name)
        else:
            students = get_all_students()
    else:
        # 老师只能看自己绑定的班级
        allowed_classes = g.allowed_classes
        
        # 如果请求指定了班级，必须在允许列表内
        if class_name:
            if class_name not in allowed_classes:
                return jsonify({'success': False, 'message': '无权访问该班级'}), 403
            students = get_students_by_class(class_name)
        else:
            # 未指定班级，返回所有绑定班级的学生
            students = []
            for cls in allowed_classes:
                students.extend(get_students_by_class(cls))
    
    # 根据角色过滤敏感字段
    filtered_students = [filter_student_data(s, user['role']) for s in students]
    
    return jsonify({
        'success': True,
        'data': filtered_students,
        'total': len(filtered_students),
        'filter_info': {
            'accessible_classes': allowed_classes if user['role'] == 'teacher' else 'all',
            'requested_class': class_name or 'all'
        }
    })

@students_bp.route('/api/students', methods=['POST'])
@login_required
@require_role(['teacher', 'admin'])
@require_class_access
@audit_log('create', 'student')
@rate_limit(30)  # 每分钟最多30次添加
def add_student():
    """添加学生
    
    老师只能往自己绑定的班级添加学生
    """
    data = request.json
    student_id = data.get('student_id', '').strip()
    name = data.get('name', '').strip()
    class_name = data.get('class_name', '').strip()
    
    if not student_id or not name:
        return jsonify({'success': False, 'message': '学号和姓名不能为空'}), 400
    
    user = g.user
    
    # 老师必须指定班级，且只能是自己绑定的班级
    if user['role'] == 'teacher':
        if not class_name:
            return jsonify({'success': False, 'message': '请指定班级'}), 400
        if class_name not in g.allowed_classes:
            return jsonify({'success': False, 'message': '无权向该班级添加学生'}), 403
    
    # 执行添加
    success, message = add_student_to_db(student_id, name, class_name or '未分班')
    
    return jsonify({'success': success, 'message': message})

@students_bp.route('/api/students/<student_id>', methods=['DELETE'])
@login_required
@require_role(['admin'])  # 仅管理员可删除
@audit_log('delete', 'student')
def delete_student(student_id):
    """删除学生（仅管理员）"""
    success, message = delete_student_from_db(student_id)
    return jsonify({'success': success, 'message': message})


# ==================== 辅助函数 ====================

def get_all_students():
    """获取所有学生"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT student_id, name, class_name, score FROM students ORDER BY class_name, student_id')
    return [dict(row) for row in cursor.fetchall()]

def get_students_by_class(class_name):
    """获取指定班级的学生"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT student_id, name, class_name, score 
        FROM students 
        WHERE class_name = ?
        ORDER BY student_id
    ''', (class_name,))
    return [dict(row) for row in cursor.fetchall()]

def add_student_to_db(student_id, name, class_name):
    """添加学生到数据库"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO students (student_id, name, class_name, score)
            VALUES (?, ?, ?, 70)
        ''', (student_id, name, class_name))
        conn.commit()
        return True, "添加成功"
    except Exception as e:
        conn.rollback()
        if 'UNIQUE constraint failed' in str(e):
            return False, "学号已存在"
        return False, f"添加失败: {str(e)}"

def delete_student_from_db(student_id):
    """从数据库删除学生"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 先删除关联记录
        cursor.execute('DELETE FROM checkin_records WHERE student_id = ?', (student_id,))
        cursor.execute('DELETE FROM score_logs WHERE student_id = ?', (student_id,))
        cursor.execute('DELETE FROM students WHERE student_id = ?', (student_id,))
        conn.commit()
        return True, "删除成功"
    except Exception as e:
        conn.rollback()
        return False, f"删除失败: {str(e)}"
```

---

## 🔒 第四层：数据脱敏与隐私保护

```python
# privacy.py

"""
数据脱敏与隐私保护模块
"""

# 脱敏规则配置
MASKING_CONFIG = {
    'student_id': {
        'admin': 'full',          # 完整显示
        'teacher': 'partial',     # 部分脱敏
        'student': 'full',        # 自己看完整的
        'guest': 'hidden'         # 访客看不到
    },
    'name': {
        'admin': 'full',
        'teacher': 'full',
        'student': 'full',
        'guest': 'partial'        # 张* 
    },
    'phone': {
        'admin': 'full',
        'teacher': 'masked',      # 138****8000
        'student': 'full',
        'guest': 'hidden'
    },
    'score': {
        'admin': 'full',
        'teacher': 'full',
        'student': 'full',
        'guest': 'none'           # 不显示
    }
}

def mask_student_id(student_id, viewer_role):
    """学号脱敏
    
    老师查看时：2024001234 -> 2024****34
    """
    if not student_id:
        return ''
    
    config = MASKING_CONFIG['student_id'].get(viewer_role, 'hidden')
    
    if config == 'full':
        return student_id
    elif config == 'hidden':
        return '****'
    elif config == 'partial':
        if len(student_id) <= 6:
            return '*' * len(student_id)
        return student_id[:4] + '*' * (len(student_id) - 6) + student_id[-2:]
    
    return '****'

def mask_name(name, viewer_role):
    """姓名脱敏
    
    访客查看时：张三 -> 张*
    """
    if not name:
        return ''
    
    config = MASKING_CONFIG['name'].get(viewer_role, 'partial')
    
    if config == 'full':
        return name
    elif config == 'hidden':
        return '*'
    elif config == 'partial':
        if len(name) <= 1:
            return '*'
        return name[0] + '*' * (len(name) - 1)
    
    return '*'

def mask_phone(phone, viewer_role):
    """手机号脱敏
    
    13800138000 -> 138****8000
    """
    if not phone:
        return ''
    
    config = MASKING_CONFIG['phone'].get(viewer_role, 'hidden')
    
    if config == 'full':
        return phone
    elif config == 'hidden':
        return '***********'
    elif config == 'masked':
        if len(phone) < 7:
            return '*' * len(phone)
        return phone[:3] + '*' * 4 + phone[-4:]
    
    return '***********'

def filter_student_data(student, viewer_role, is_self=False):
    """根据查看者角色过滤学生数据
    
    Args:
        student: 学生原始数据字典
        viewer_role: 查看者角色
        is_self: 是否是自己查看自己
    
    Returns:
        过滤后的数据字典
    """
    if not student:
        return {}
    
    # 自己查看自己时，显示完整信息
    if is_self:
        viewer_role = 'student'
    
    # 基础字段（所有人可见）
    filtered = {
        'student_id': mask_student_id(student.get('student_id'), viewer_role),
        'name': mask_name(student.get('name'), viewer_role),
        'class_name': student.get('class_name')
    }
    
    # 分数（访客不可见）
    if viewer_role != 'guest':
        filtered['score'] = student.get('score', 0)
    
    # 敏感字段仅管理员可见
    if viewer_role == 'admin':
        filtered.update({
            'phone': mask_phone(student.get('phone'), viewer_role),
            'created_at': student.get('created_at'),
            'updated_at': student.get('updated_at')
        })
    
    return filtered

def filter_checkin_record(record, viewer_role, user_class=None):
    """过滤签到记录
    
    - 老师只能看自己班级的签到记录
    - 学生只能看自己的
    """
    if not record:
        return {}
    
    # 基础字段
    filtered = {
        'record_id': record.get('record_id'),
        'checkin_time': record.get('checkin_time'),
        'checkin_type': record.get('checkin_type'),
        'class_name': record.get('class_name')
    }
    
    # 学生信息脱敏
    filtered['student_name'] = mask_name(record.get('student_name'), viewer_role)
    filtered['student_id'] = mask_student_id(record.get('student_id'), viewer_role)
    
    return filtered

def filter_score_log(log, viewer_role, is_own=False):
    """过滤分数变更日志
    
    - 老师可以看本班的
    - 学生只能看自己的
    """
    if not log:
        return {}
    
    filtered = {
        'log_id': log.get('log_id'),
        'score_change': log.get('score_change'),
        'reason': log.get('reason'),
        'operation_time': log.get('operation_time')
    }
    
    # 操作人信息脱敏
    if viewer_role == 'admin':
        filtered['operator'] = log.get('operator_name', '系统')
    else:
        filtered['operator'] = '老师'  # 不显示具体操作人
    
    return filtered
```

---

## 📊 第五层：审计与监控

```python
# audit_monitor.py

"""
审计监控与异常检测模块
"""

from datetime import datetime, timedelta
from collections import defaultdict
import threading
import time

class SecurityMonitor:
    """安全监控类"""
    
    def __init__(self):
        self.alert_handlers = []
        self.running = False
        
    def start(self):
        """启动监控线程"""
        self.running = True
        monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        monitor_thread.start()
        
    def stop(self):
        """停止监控"""
        self.running = False
        
    def _monitor_loop(self):
        """监控主循环"""
        while self.running:
            try:
                self._check_suspicious_activity()
                time.sleep(60)  # 每分钟检查一次
            except Exception as e:
                print(f'监控检查异常: {e}')
    
    def _check_suspicious_activity(self):
        """检查可疑行为"""
        alerts = []
        
        # 1. 批量查询检测（数据爬取）
        mass_queries = self._detect_mass_query()
        for query in mass_queries:
            alerts.append({
                'type': 'mass_query',
                'severity': 'high',
                'user_id': query['user_id'],
                'user_name': query['user_name'],
                'message': f'用户 {query["user_name"]} 1小时内查询 {query["count"]} 次，疑似数据爬取',
                'details': query
            })
        
        # 2. 跨班级访问尝试
        cross_class = self._detect_cross_class_access()
        for item in cross_class:
            alerts.append({
                'type': 'cross_class_access',
                'severity': 'high',
                'user_id': item['user_id'],
                'user_name': item['user_name'],
                'message': f'用户 {item["user_name"]} 尝试访问未授权班级 {item["target_class"]}',
                'details': item
            })
        
        # 3. 非工作时间访问
        after_hours = self._detect_after_hours_access()
        for item in after_hours:
            alerts.append({
                'type': 'after_hours',
                'severity': 'medium',
                'user_id': item['user_id'],
                'message': f'用户 {item["user_name"]} 在非工作时间进行 {item["action"]} 操作',
                'details': item
            })
        
        # 4. 登录失败过多
        failed_logins = self._detect_failed_login()
        for item in failed_logins:
            alerts.append({
                'type': 'failed_login',
                'severity': 'high',
                'ip': item['ip'],
                'message': f'IP {item["ip"]} 在10分钟内登录失败 {item["count"]} 次',
                'details': item
            })
        
        # 保存告警并通知
        for alert in alerts:
            self._save_alert(alert)
            self._notify_alert(alert)
    
    def _detect_mass_query(self, threshold=100, window_hours=1):
        """检测批量查询
        
        Args:
            threshold: 阈值，超过此数量视为可疑
            window_hours: 时间窗口（小时）
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_id, user_name, role, COUNT(*) as query_count
            FROM audit_logs
            WHERE action = 'read' 
              AND created_at >= datetime('now', '-{} hours')
              AND user_id IS NOT NULL
            GROUP BY user_id
            HAVING query_count > ?
            ORDER BY query_count DESC
        '''.format(window_hours), (threshold,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def _detect_cross_class_access(self, window_hours=24):
        """检测跨班级访问尝试"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_id, user_name, resource, params, COUNT(*) as count
            FROM audit_logs
            WHERE action = 'access_violation'
              AND created_at >= datetime('now', '-{} hours')
            GROUP BY user_id
            ORDER BY count DESC
        '''.format(window_hours))
        
        results = []
        for row in cursor.fetchall():
            row_dict = dict(row)
            # 解析参数获取目标班级
            params = row_dict.get('params', '')
            if '尝试访问未授权班级' in params:
                # 提取班级名
                import re
                match = re.search(r'班级: ([^\']+)', params)
                if match:
                    row_dict['target_class'] = match.group(1)
            results.append(row_dict)
        
        return results
    
    def _detect_after_hours_access(self, window_hours=24):
        """检测非工作时间访问
        
        工作时间定义：周一至周五 08:00-22:00
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_id, user_name, action, resource, created_at
            FROM audit_logs
            WHERE created_at >= datetime('now', '-{} hours')
              AND (
                  -- 周末
                  strftime('%w', created_at) IN ('0', '6')
                  OR
                  -- 工作时间外
                  strftime('%H', created_at) < '08'
                  OR
                  strftime('%H', created_at) > '22'
              )
              AND action NOT IN ('login', 'logout')  -- 排除登录登出
            ORDER BY created_at DESC
            LIMIT 50
        '''.format(window_hours))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def _detect_failed_login(self, threshold=5, window_minutes=10):
        """检测登录失败"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ip_address, COUNT(*) as fail_count
            FROM audit_logs
            WHERE action = 'login' 
              AND status_code != 200
              AND created_at >= datetime('now', '-{} minutes')
            GROUP BY ip_address
            HAVING fail_count >= ?
            ORDER BY fail_count DESC
        '''.format(window_minutes), (threshold,))
        
        return [{'ip': row['ip_address'], 'count': row['fail_count']} 
                for row in cursor.fetchall()]
    
    def _save_alert(self, alert):
        """保存告警到数据库"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO security_alerts 
            (alert_type, severity, description, related_user_id, related_ip)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            alert['type'],
            alert['severity'],
            alert['message'],
            alert.get('user_id'),
            alert.get('ip')
        ))
        conn.commit()
    
    def _notify_alert(self, alert):
        """通知告警（可扩展为邮件、短信、钉钉等）"""
        # 高严重性告警打印到控制台（生产环境可接入消息推送）
        if alert['severity'] == 'high':
            print(f'[HIGH ALERT] {alert["message"]}')
            # TODO: 接入钉钉/企业微信通知
            # send_dingtalk_alert(alert)


def get_audit_stats(days=7, user_id=None):
    """获取审计统计
    
    Args:
        days: 统计天数
        user_id: 指定用户（None则统计全校）
    
    Returns:
        统计字典
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    params = []
    where_clause = f"created_at >= datetime('now', '-{days} days')"
    
    if user_id:
        where_clause += " AND user_id = ?"
        params.append(user_id)
    
    # 操作类型统计
    cursor.execute(f'''
        SELECT action, COUNT(*) as count 
        FROM audit_logs 
        WHERE {where_clause}
        GROUP BY action
    ''', params)
    action_stats = {row['action']: row['count'] for row in cursor.fetchall()}
    
    # 资源访问统计
    cursor.execute(f'''
        SELECT resource, COUNT(*) as count 
        FROM audit_logs 
        WHERE {where_clause}
        GROUP BY resource
    ''', params)
    resource_stats = {row['resource']: row['count'] for row in cursor.fetchall()}
    
    # 活跃用户统计
    cursor.execute(f'''
        SELECT user_name, COUNT(*) as count 
        FROM audit_logs 
        WHERE {where_clause} AND user_id IS NOT NULL
        GROUP BY user_id
        ORDER BY count DESC
        LIMIT 10
    ''', params)
    top_users = [dict(row) for row in cursor.fetchall()]
    
    # 异常统计
    cursor.execute(f'''
        SELECT alert_type, COUNT(*) as count
        FROM security_alerts
        WHERE created_at >= datetime('now', '-{days} days')
          AND is_resolved = 0
        GROUP BY alert_type
    ''')
    active_alerts = {row['alert_type']: row['count'] for row in cursor.fetchall()}
    
    return {
        'period_days': days,
        'action_stats': action_stats,
        'resource_stats': resource_stats,
        'top_active_users': top_users,
        'active_alerts': active_alerts
    }


def get_user_activity(user_id, days=7):
    """获取用户活动详情"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT action, resource, method, status_code, ip_address, created_at
        FROM audit_logs
        WHERE user_id = ? AND created_at >= datetime('now', '-? days')
        ORDER BY created_at DESC
    ''', (user_id, days))
    
    return [dict(row) for row in cursor.fetchall()]


# 全局监控实例
security_monitor = SecurityMonitor()

def start_security_monitor():
    """启动安全监控"""
    security_monitor.start()

def stop_security_monitor():
    """停止安全监控"""
    security_monitor.stop()
```

---

## 📋 实施路线图

### 第一阶段：基础防护（Week 1）

```
Day 1-2: 数据库改造
    ├── 执行 SQL 迁移脚本（users 表扩展、audit_logs 表创建）
    └── 为现有用户设置默认角色

Day 3-4: 核心装饰器开发
    ├── decorators.py 实现
    ├── login_required 增强
    ├── require_role 实现
    └── require_class_access 实现

Day 5-7: 接口加固
    ├── 给关键接口添加装饰器
    ├── 关闭/限制危险接口
    └── 基础审计日志测试
```

### 第二阶段：数据安全（Week 2）

```
Week 2: 
    ├── privacy.py 数据脱敏实现
    ├── 前端展示适配（使用脱敏后的数据）
    ├── 敏感字段梳理和分级
    └── 学生自助查询接口改造
```

### 第三阶段：监控告警（Week 3）

```
Week 3:
    ├── audit_monitor.py 实现
    ├── 审计日志查询接口（仅管理员）
    ├── 异常行为检测规则
    └── 管理员审计面板前端
```

### 第四阶段：优化完善（Week 4）

```
Week 4:
    ├── 权限缓存优化（减少数据库查询）
    ├── 压力测试
    ├── 安全测试（模拟越权访问）
    └── 操作手册编写
```

---

## 🔧 快速启动脚本

```bash
#!/bin/bash
# setup_security.sh

echo "=== 班级管理系统安全方案部署 ==="

# 1. 数据库迁移
echo "[1/4] 执行数据库迁移..."
sqlite3 backend/data/class_system.db < migrations/add_security_tables.sql

# 2. 安装依赖
echo "[2/4] 安装安全相关依赖..."
pip install -r requirements-security.txt

# 3. 配置环境变量
echo "[3/4] 配置环境变量..."
if [ -z "$SECRET_KEY" ]; then
    export SECRET_KEY=$(openssl rand -hex 32)
    echo "已生成 SECRET_KEY: $SECRET_KEY"
    echo "请将 SECRET_KEY 添加到 ~/.bashrc 或系统环境变量"
fi

# 4. 初始化数据
echo "[4/4] 初始化角色和权限..."
python scripts/init_security.py

echo "=== 部署完成 ==="
echo "请检查以下配置："
echo "1. 环境变量 SECRET_KEY 已设置"
echo "2. 为现有老师账号分配班级（assigned_class 字段）"
echo "3. 创建至少一个 admin 账号"
```

---

## 📝 配置文件示例

```python
# config/security.py

class SecurityConfig:
    """安全配置"""
    
    # ========== 认证配置 ==========
    SECRET_KEY = os.environ.get('SECRET_KEY')  # 强制从环境变量读取
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 3600  # 1小时
    SESSION_REFRESH_EACH_REQUEST = True
    
    # ========== 密码策略 ==========
    MIN_PASSWORD_LENGTH = 8
    PASSWORD_REQUIRE_UPPER = True
    PASSWORD_REQUIRE_LOWER = True
    PASSWORD_REQUIRE_DIGIT = True
    PASSWORD_REQUIRE_SPECIAL = False  # 职业院校场景可适当放宽
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = 900  # 15分钟
    
    # ========== 限流配置 ==========
    RATE_LIMIT_DEFAULT = '100/hour'
    RATE_LIMIT_LOGIN = '5/minute'
    RATE_LIMIT_IMPORT = '10/hour'
    RATE_LIMIT_ADMIN = '30/minute'
    
    # ========== 审计配置 ==========
    AUDIT_ENABLED = True
    AUDIT_LOG_RETENTION_DAYS = 90
    AUDIT_SENSITIVE_FIELDS = ['password', 'token', 'secret']
    
    # ========== 数据隔离 ==========
    CLASS_ISOLATION_ENABLED = True
    TEACHER_MULTIPLE_CLASSES = True  # 允许一个老师带多个班
    
    # ========== 监控告警 ==========
    SECURITY_MONITOR_ENABLED = True
    ALERT_MASS_QUERY_THRESHOLD = 100  # 1小时内查询超过100次告警
    ALERT_FAILED_LOGIN_THRESHOLD = 5   # 10分钟内登录失败5次告警
    
    # ========== 数据脱敏 ==========
    MASKING_ENABLED = True
    MASKING_STUDENT_ID_FOR_TEACHER = True
    MASKING_PHONE_FOR_TEACHER = True
```

---

## ✅ 验收检查清单

### 安全功能验证

- [ ] 未登录用户无法访问 `/api/students`
- [ ] 老师 A 无法查看老师 B 班级的学生
- [ ] 学生只能查询自己的信息
- [ ] 普通老师无法调用 `/api/admin/reset-scores`
- [ ] 文件上传使用随机文件名，防止路径遍历
- [ ] 所有敏感操作都有审计日志
- [ ] 审计日志中密码等敏感字段已脱敏
- [ ] XSS 防护：返回数据中的特殊字符已转义

### 性能验证

- [ ] 权限检查不显著影响接口响应时间（<10ms）
- [ ] 审计日志异步写入，不阻塞业务
- [ ] 高并发场景下权限缓存有效

### 用户体验

- [ ] 权限不足时返回清晰的中文提示
- [ ] 老师能看到自己有权限的班级列表
- [ ] 管理员审计面板可正常查询日志

---

**方案版本**: v1.0  
**最后更新**: 2026-03-18  
**文档位置**: `/root/student-manage-v3/SECURITY_SOLUTION.md`

---

## ✅ 已修复问题记录

### 2026-03-18 修复：SECRET_KEY 硬编码漏洞 (CRITICAL)

**问题描述**：
- `app.py` 和 `config.py` 中存在硬编码的默认 SECRET_KEY
- 风险：Session Cookie 可被伪造，攻击者可完全绕过登录认证

**修复内容**：

1. **app.py 修改**（第26-34行）：
   - 移除硬编码密钥 `student-manage-fixed-secret-key-2024`
   - 未设置环境变量时自动生成随机密钥（每次重启失效）
   - 添加警告日志提示用户设置永久密钥

2. **backend/config.py 修改**：
   - 移除硬编码密钥 `your-secret-key-here-change-in-production` 和 `student-manage-v2-secret-key-change-me`
   - 生产环境强制检查 `SECRET_KEY` 环境变量，未设置时抛异常阻止启动

**安全改进**：
```
修复前：密钥固定，任何人知道源码就能伪造 Session
修复后：
  - 开发环境：自动生成随机密钥（安全但重启失效）
  - 生产环境：强制要求设置环境变量，否则拒绝启动
```

**使用方式**：
```bash
# 生成密钥
./generate_secret_key.sh

# 临时设置
export SECRET_KEY=your-generated-key

# 永久设置（推荐）
echo 'export SECRET_KEY=your-generated-key' >> ~/.bashrc
```

**状态**：✅ 已修复并验证


### 2026-03-18 修复：文件上传路径遍历漏洞 (HIGH)

**问题描述**：
- `api_import_students` 接口直接使用用户上传的文件名保存文件
- 风险：攻击者可构造 `../../../etc/passwd` 等路径上传文件到任意位置

**漏洞代码（修复前）**：
```python
filepath = os.path.join(UPLOAD_FOLDER, file.filename)  # 危险！
file.save(filepath)
```

**修复内容**：

1. **backend/app.py 和 app.py 修改**：
```python
import uuid
from werkzeug.utils import secure_filename

# 保存上传的文件（使用随机文件名防止路径遍历攻击）
original_filename = secure_filename(file.filename)
ext = original_filename.split('.')[-1] if '.' in original_filename else 'xlsx'
safe_filename = f"{uuid.uuid4().hex}.{ext}"
filepath = os.path.join(UPLOAD_FOLDER, safe_filename)
file.save(filepath)
```

**安全改进**：
```
修复前：
  用户上传 "../../../etc/passwd" → 保存到 /etc/passwd（系统被入侵）
  
修复后：
  用户上传 "../../../etc/passwd" → 保存为 "a1b2c3d4...e5f6.passwd"（随机文件名）
  攻击者无法控制文件路径和名称
```

**状态**：✅ 已修复并验证


### 2026-03-18 修复：管理员权限绕过 (HIGH)

**问题描述**：
- `admin_required` 装饰器没有实际检查管理员权限
- `api_reset_all_scores` 只检查登录，不检查是否是管理员
- 任何登录用户都可以重置全校学生分数

**漏洞代码（修复前）**：
```python
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': '请先登录'}), 401
        # 没有实际检查管理员权限！
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/admin/reset-scores', methods=['POST'])
@login_required  # ❌ 只检查登录
def api_reset_all_scores():
    ...
```

**修复内容**：

1. **修复 admin_required 装饰器**：
```python
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': '请先登录'}), 401
        
        # ✅ 检查管理员权限
        user = get_user_by_id(session['user_id'])
        if not user or not user.get('is_admin'):
            return jsonify({'success': False, 'message': '权限不足，需要管理员权限'}), 403
        
        return f(*args, **kwargs)
    return decorated_function
```

2. **应用 admin_required 到敏感接口**：
```python
@app.route('/api/admin/reset-scores', methods=['POST'])
@admin_required  # ✅ 必须使用管理员权限
def api_reset_all_scores():
    ...

@app.route('/api/db-info', methods=['GET'])
@admin_required  # ✅ 数据库信息也需要保护
def api_get_db_info():
    ...
```

**安全改进**：
```
修复前：
  任何登录用户 → 可以重置全校分数
  
修复后：
  普通登录用户 → 403 权限不足
  管理员 (is_admin=1) → 允许操作
```

**受保护的接口**：
| 接口 | 方法 | 需要权限 |
|------|------|----------|
| /api/admin/reset-scores | POST | 管理员 |
| /api/db-info | GET | 管理员 |

**状态**：✅ 已修复并验证


### 2026-03-18 修复：缺乏请求限流 (HIGH)

**问题描述**：
- 登录接口可被无限次尝试，存在暴力破解风险
- 签到接口可被刷，影响数据统计
- API 缺乏频率限制，可能被爬虫滥用

**修复内容**：

1. **安装 flask-limiter**：
```bash
pip install flask-limiter>=4.0.0
```

2. **backend/app.py 配置限流器**：
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
    strategy="fixed-window"
)
```

3. **敏感接口添加限流装饰器**：
```python
# 登录接口限流：5次/分钟
@app.route('/api/login', methods=['POST'])
@limiter.limit("5 per minute")
def api_login():
    ...

# 签到接口限流：10次/分钟
@app.route('/api/checkin', methods=['POST'])
@limiter.limit("10 per minute")
def api_checkin():
    ...
```

**安全改进**：
```
修复前：
  攻击者可无限次尝试破解密码
  
修复后：
  - 登录接口：5次/分钟
  - 签到接口：10次/分钟
  - 其他接口：50次/小时，200次/天
  - 超限返回 429 Too Many Requests
```

**限流策略**：
| 接口 | 限制 | 说明 |
|------|------|------|
| /api/login | 5/分钟 | 防止暴力破解 |
| /api/checkin | 10/分钟 | 防止刷签到 |
| 其他接口 | 50/小时, 200/天 | 默认保护 |

**状态**：✅ 已修复并验证


---

## ✅ 实施进度记录

### 2026-03-19 完成：第一阶段 Day 1-2 - 数据库改造

**完成任务**：
1. ✅ 创建数据库迁移脚本 `migrations/add_security_tables.sql`
2. ✅ 扩展 users 表字段：
   - `role` - 用户角色（admin/teacher/student）
   - `assigned_class` - 老师绑定的班级
   - `is_active` - 账号是否激活
   - `last_login_ip` - 最后登录IP
   - `login_fail_count` - 登录失败次数
   - `locked_until` - 账号锁定时间
3. ✅ 创建 audit_logs 审计日志表
4. ✅ 创建 security_alerts 安全告警表
5. ✅ 创建 db_migrations 迁移版本表
6. ✅ 为现有用户设置默认角色（admin→admin）
7. ✅ 创建相关索引优化查询

**迁移状态**：✅ 已执行并验证


### 2026-03-19 完成：第一阶段 Day 3-4 - 核心装饰器开发

**完成任务**：
1. ✅ 创建 `decorators.py` 权限装饰器模块
   - `login_required` 增强版：检查账号激活状态、锁定状态
   - `admin_required`：管理员权限验证
   - `require_role`：角色权限控制（admin/teacher/student）
   - `require_class_access`：班级数据访问控制
   - `audit_log`：操作审计日志装饰器

2. ✅ 登录接口安全增强
   - 密码错误计数（login_fail_count）
   - 5次错误后自动锁定15分钟（locked_until）
   - 登录IP记录（last_login_ip）
   - 登录时间更新（last_login）
   - 失败次数提示（"还剩 X 次机会"）
   - 登录审计日志写入（audit_logs）

3. ✅ 后端架构优化
   - 使用新的增强版装饰器替换旧装饰器
   - 保留原有的限流保护（flask-limiter）

**测试验证**：
| 测试项 | 结果 |
|--------|:--:|
| 正常登录 | ✅ 返回用户信息（含role） |
| 错误密码 | ✅ 提示剩余次数 |
| 审计日志 | ✅ 记录到audit_logs表 |
| 账号锁定 | ✅ 5次错误后锁定15分钟 |

**状态**：✅ 已完成并测试


### 2026-03-19 完成：第一阶段 Day 5-7 - 接口加固

**完成任务**：
1. ✅ 敏感接口添加 `@login_required` 权限控制
   - `GET /api/students` - 学生列表查询
   - `GET /api/stats` - 统计数据查询
   - `GET /api/checkin/records` - 签到记录查询
   - `GET /api/class-session` - 上课状态查询
   - `GET /api/class-session/students` - 上课班级学生查询
   - `GET /api/score/logs` - 分数变更日志查询

2. ✅ 敏感操作添加审计日志记录
   - 删除学生 (`api_delete_student`) - 记录操作人、被删学生ID
   - 修改分数 (`api_update_score`) - 记录变更值和原因
   - 重置全校分数 (`api_reset_all_scores`) - 记录重置分数值
   - 用户登录 (`api_login`) - 记录登录IP和结果

3. ✅ 保留必要的公开接口（限流保护）
   - `POST /api/login` - 登录（5次/分钟限流）
   - `POST /api/checkin` - 学生签到（10次/分钟限流）
   - `POST /api/query_student` - 学生自助查询

**接口权限状态总览**：

| 接口 | 方法 | 权限 |
|------|------|------|
| /api/login | POST | 公开（限流） |
| /api/logout | POST | 公开 |
| /api/checkin | POST | 公开（限流） |
| /api/students | GET | 🔒 需登录 |
| /api/stats | GET | 🔒 需登录 |
| /api/checkin/records | GET | 🔒 需登录 |
| /api/score/logs | GET | 🔒 需登录 |
| /api/admin/* | POST | 🔴 需管理员 |

**状态**：✅ 已完成并测试

---

## 📊 Phase 1 完成总结

### 已完成内容（Week 1）

| 阶段 | 任务 | 关键成果 |
|------|------|----------|
| Day 1-2 | 数据库改造 | users表扩展6个字段，audit_logs表，security_alerts表 |
| Day 3-4 | 核心装饰器 | login_required增强版，admin_required，审计日志装饰器 |
| Day 5-7 | 接口加固 | 6个敏感接口加权限控制，4类操作加审计日志 |

### 安全能力提升

```
改造前：
  ❌ 任何人可查看全校学生名单
  ❌ 任何人可查看签到记录
  ❌ 无操作审计，无法追溯
  ❌ 密码可无限次尝试
  ❌ 账号无法禁用

改造后：
  ✅ 敏感数据需登录才能访问
  ✅ 所有重要操作有审计日志
  ✅ 5次密码错误自动锁定15分钟
  ✅ 账号可禁用、可锁定
  ✅ 登录IP被记录
```

### 下一步：Phase 2 - 数据安全（Week 2）
- 数据脱敏实现（privacy.py）
- 敏感字段分级
- 学生自助查询接口改造


### 2026-03-19 完成：Phase 2 数据安全

**完成任务**：
1. ✅ 创建 `privacy.py` 数据脱敏模块
   - `mask_string()`: 学号脱敏 (2513010101 → 2513****01)
   - `mask_name()`: 姓名脱敏 (段静云 → 段**)
   - `filter_student_data()`: 单条学生数据脱敏
   - `filter_students_list()`: 学生列表脱敏
   - `filter_stats_data()`: 统计数据脱敏
   - `filter_checkin_records()`: 签到记录脱敏

2. ✅ 数据脱敏规则配置
   ```python
   MASKING_RULES = {
       'student_id': {
           'admin': 'full',        # 完整显示
           'teacher': 'partial',   # 部分脱敏
           'student': 'self_only'  # 只能看自己
       },
       'name': {
           'admin': 'full',
           'teacher': 'partial',   # 姓氏保留
           'student': 'self_only'
       }
   }
   ```

3. ✅ API接口数据脱敏
   - `GET /api/students` - 学生列表脱敏 + 班级过滤
   - `GET /api/stats` - 统计数据脱敏
   - `GET /api/checkin/records` - 签到记录脱敏
   - `POST /api/student/query` - 学生自助查询脱敏

4. ✅ 班级数据隔离
   - 老师只能查看 `assigned_class` 绑定的班级
   - 管理员可查看所有班级
   - 学生只能查看自己的数据

**测试验证**：
| 角色 | 学号显示 | 姓名显示 | 可见班级 |
|------|---------|---------|---------|
| admin | 2513010101 | 段静云 | 所有班级 |
| teacher | 2513****01 | 段** | 绑定班级 |
| student | ****0101 | ** | 仅自己 |

**状态**：✅ 已完成并测试

