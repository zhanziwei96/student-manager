"""
班级管理系统 - Flask 后端
优化并发处理，支持多学生同时签到，添加老师登录功能
"""

import os
from functools import wraps
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
from data_manager import (
    init_data, get_all_students, get_student_by_id, add_student,
    import_students_from_xlsx, update_student_score, add_checkin_record,
    get_checkin_records, get_score_logs, delete_student, delete_class,
    authenticate_user, change_password, get_user_by_id,
    set_current_class, get_current_class, get_class_students_with_checkin_status
)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 最大 16MB 上传
app.config['SECRET_KEY'] = os.urandom(24)  # 用于 session 加密
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # session 有效期 1 小时

# 上传文件临时目录
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'success': False, 'message': '请先登录'}), 401
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """管理员验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'success': False, 'message': '请先登录'}), 401
            return redirect(url_for('login_page'))
        
        # 可以在这里添加管理员权限验证
        # user = get_user_by_id(session['user_id'])
        # if not user or not user.get('is_admin'):
        #     return jsonify({'success': False, 'message': '权限不足'}), 403
        
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


# ========== 登录相关 ==========

@app.route('/login', methods=['GET'])
def login_page():
    """登录页面"""
    if 'user_id' in session:
        return redirect(url_for('admin_page'))
    return render_template('login.html')


@app.route('/api/login', methods=['POST'])
def api_login():
    """登录 API"""
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({'success': False, 'message': '请输入用户名和密码'})
    
    user = authenticate_user(username, password)
    
    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['name'] = user['name']
        session.permanent = True
        return jsonify({
            'success': True, 
            'message': '登录成功',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'name': user['name']
            }
        })
    else:
        return jsonify({'success': False, 'message': '用户名或密码错误'})


@app.route('/api/logout', methods=['POST'])
def api_logout():
    """登出 API"""
    session.clear()
    return jsonify({'success': True, 'message': '登出成功'})


@app.route('/logout')
def logout():
    """登出页面"""
    session.clear()
    return redirect(url_for('login_page'))


@app.route('/api/change-password', methods=['POST'])
@login_required
def api_change_password():
    """修改密码 API"""
    data = request.json
    old_password = data.get('old_password', '').strip()
    new_password = data.get('new_password', '').strip()
    
    if not old_password or not new_password:
        return jsonify({'success': False, 'message': '请输入原密码和新密码'})
    
    if len(new_password) < 6:
        return jsonify({'success': False, 'message': '新密码长度至少为 6 位'})
    
    success, message = change_password(session['user_id'], old_password, new_password)
    return jsonify({'success': success, 'message': message})


@app.route('/api/me')
@login_required
def api_get_current_user():
    """获取当前登录用户信息"""
    user = get_user_by_id(session['user_id'])
    if user:
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'name': user['name'],
                'last_login': user['last_login']
            }
        })
    return jsonify({'success': False, 'message': '用户不存在'})


# ========== 学生管理 ==========

@app.route('/api/students', methods=['GET'])
def api_get_students():
    """获取所有学生"""
    students = get_all_students()
    return jsonify({'success': True, 'data': students})


@app.route('/api/students', methods=['POST'])
@login_required
def api_add_student():
    """添加单个学生"""
    data = request.json
    student_id = data.get('student_id', '').strip()
    name = data.get('name', '').strip()
    class_name = data.get('class_name', '').strip()
    
    if not student_id or not name:
        return jsonify({'success': False, 'message': '学号和姓名不能为空'})
    
    success, message = add_student(student_id, name, class_name or '未分班', 0)
    return jsonify({'success': success, 'message': message})


@app.route('/api/students/<student_id>', methods=['DELETE'])
@login_required
def api_delete_student(student_id):
    """删除学生"""
    success, message = delete_student(student_id)
    return jsonify({'success': success, 'message': message})


@app.route('/api/class/<class_name>', methods=['DELETE'])
@login_required
def api_delete_class(class_name):
    """删除整个班级"""
    success, message = delete_class(class_name)
    return jsonify({'success': success, 'message': message})


@app.route('/api/students/import', methods=['POST'])
@login_required
def api_import_students():
    """从 Excel 文件导入学生"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '请选择文件'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '请选择文件'})
    
    # 检查文件格式
    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'success': False, 'message': '请上传 Excel 文件（.xlsx 或 .xls）'})
    
    class_name = request.form.get('class_name', '').strip()
    
    # 保存上传的文件
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    
    try:
        success, message, errors = import_students_from_xlsx(filepath, class_name or None)
        # 删除临时文件
        os.remove(filepath)
        return jsonify({
            'success': success, 
            'message': message,
            'errors': errors
        })
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'success': False, 'message': f'导入失败: {str(e)}'})


@app.route('/api/students/<student_id>/score', methods=['POST'])
@login_required
def api_update_score(student_id):
    """更新学生分数"""
    data = request.json
    score_change = data.get('score_change', 0)
    reason = data.get('reason', '').strip()
    
    try:
        score_change = int(score_change)
    except ValueError:
        return jsonify({'success': False, 'message': '分数变更必须是整数'})
    
    success, message = update_student_score(student_id, score_change, reason)
    return jsonify({'success': success, 'message': message})


# ========== 签到相关 ==========

@app.route('/api/checkin', methods=['POST'])
def api_checkin():
    """
    签到接口 - 优化并发处理
    学生输入学号和姓名进行签到
    """
    data = request.json
    student_id = data.get('student_id', '').strip()
    name = data.get('name', '').strip()
    
    if not student_id:
        return jsonify({'success': False, 'message': '学号不能为空'})
    
    if not name:
        return jsonify({'success': False, 'message': '姓名不能为空'})
    
    # 检查学生是否存在
    student = get_student_by_id(student_id)
    if not student:
        return jsonify({'success': False, 'message': '学生不存在，请先联系老师添加'})
    
    # 验证姓名是否匹配（防止输错学号签到成别人）
    if student['name'] != name:
        return jsonify({'success': False, 'message': '学号与姓名不匹配'})
    
    # 添加签到记录
    success, message, student_name = add_checkin_record(student_id)
    
    return jsonify({
        'success': success, 
        'message': message,
        'student_name': student_name
    })


@app.route('/api/checkin/records', methods=['GET'])
def api_get_checkin_records():
    """获取签到记录"""
    student_id = request.args.get('student_id', '').strip()
    date = request.args.get('date', '').strip()
    
    records = get_checkin_records(
        student_id if student_id else None,
        date if date else None
    )
    return jsonify({'success': True, 'data': records})


# ========== 上课状态管理 ==========

@app.route('/api/class-session', methods=['GET'])
@login_required
def api_get_class_session():
    """获取当前上课状态"""
    session_info = get_current_class()
    return jsonify({
        'success': True,
        'data': session_info
    })


@app.route('/api/class-session', methods=['POST'])
@login_required
def api_set_class_session():
    """设置当前上课班级"""
    data = request.json
    class_name = data.get('class_name', '').strip()
    
    success, message = set_current_class(class_name if class_name else None)
    return jsonify({'success': success, 'message': message})


@app.route('/api/class-session/students', methods=['GET'])
def api_get_class_session_students():
    """获取当前上课班级的学生签到状态"""
    session_info = get_current_class()
    
    if not session_info['active'] or not session_info['class_name']:
        return jsonify({
            'success': False,
            'message': '没有正在上课的班级',
            'data': {
                'active': False,
                'students': []
            }
        })
    
    students = get_class_students_with_checkin_status(session_info['class_name'])
    
    return jsonify({
        'success': True,
        'data': {
            'active': True,
            'class_name': session_info['class_name'],
            'start_time': session_info['start_time'],
            'students': students,
            'total': len(students),
            'checked_in': sum(1 for s in students if s['checked_in']),
            'not_checked_in': sum(1 for s in students if not s['checked_in'])
        }
    })


@app.route('/api/score/logs', methods=['GET'])
def api_get_score_logs():
    """获取分数变更日志"""
    student_id = request.args.get('student_id', '').strip()
    logs = get_score_logs(student_id if student_id else None)
    return jsonify({'success': True, 'data': logs})


# ========== 页面路由 ==========

@app.route('/checkin')
def checkin_page():
    """签到页面"""
    return render_template('checkin.html')


@app.route('/admin')
@login_required
def admin_page():
    """管理后台"""
    return render_template('admin.html')


# ========== 错误处理 ==========

@app.errorhandler(500)
def internal_error(error):
    """处理 500 错误"""
    return jsonify({'success': False, 'message': '服务器内部错误，请稍后重试'}), 500


@app.errorhandler(401)
def unauthorized_error(error):
    """处理 401 错误"""
    if request.is_json:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    return redirect(url_for('login_page'))


if __name__ == '__main__':
    init_data()
    print("=" * 50)
    print("班级管理系统已启动")
    print("访问地址: http://127.0.0.1:5000")
    print("=" * 50)
    print("\n功能说明:")
    print("- 首页: http://127.0.0.1:5000/")
    print("- 管理后台: http://127.0.0.1:5000/admin")
    print("- 登录页面: http://127.0.0.1:5000/login")
    print("- 签到页面: http://127.0.0.1:5000/checkin")
    print("\n特殊功能:")
    print("- 一机一签: 每台设备每天只能签到一次")
    print("\n默认管理员账户:")
    print("- 用户名: admin")
    print("- 密码: admin123")
    print("\n按 Ctrl+C 停止服务")
    print("=" * 50)
    
    # 使用 threaded=True 启用多线程处理并发请求
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
