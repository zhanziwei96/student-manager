"""
班级管理系统 - Flask 后端 (API 服务器)
为 Vue 3 + Element Plus 前端提供 RESTful API
"""

import os
from functools import wraps
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from data_manager import (
    init_data, get_all_students, get_student_by_id, get_students_by_name, add_student,
    import_students_from_xlsx, update_student_score, add_checkin_record,
    get_checkin_records, get_score_logs, delete_student, delete_class,
    authenticate_user, change_password, get_user_by_id,
    set_current_class, get_current_class, get_class_students_with_checkin_status,
    reset_all_scores, close_db_connection, get_db_info, DB_ENV_NAME
)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600

# 启用 CORS，允许前端访问
CORS(app, supports_credentials=True, origins=['http://localhost:3000', 'http://127.0.0.1:3000'])

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


@app.teardown_appcontext
def close_db(error):
    """请求结束时关闭数据库连接"""
    close_db_connection()


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
    """API 首页"""
    return jsonify({
        'message': '班级管理系统 API',
        'version': '2.0',
        'frontend': 'Vue 3 + Element Plus'
    })


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
    import urllib.parse
    # 记录原始接收到的班级名
    print(f"[删除班级] 原始接收到的班级名: {repr(class_name)}")
    # URL解码后的班级名
    decoded_name = urllib.parse.unquote(class_name)
    print(f"[删除班级] URL解码后: {repr(decoded_name)}")
    
    success, message = delete_class(decoded_name)
    print(f"[删除班级] 结果: success={success}, message={message}")
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


@app.route('/api/admin/reset-scores', methods=['POST'])
@login_required
def api_reset_all_scores():
    """重置所有学生分数为70分（管理员功能）"""
    data = request.json or {}
    default_score = data.get('default_score', 70)
    
    try:
        default_score = int(default_score)
    except ValueError:
        return jsonify({'success': False, 'message': '分数必须是整数'})
    
    success, message = reset_all_scores(default_score)
    return jsonify({'success': success, 'message': message})


@app.route('/api/teacher-checkin', methods=['POST'])
@login_required
def api_teacher_checkin():
    """
    老师代签到接口 - 老师可以帮学生签到，不受次数限制
    支持通过学生姓名进行代签到
    """
    data = request.json
    student_name = data.get('student_name', '').strip()
    student_id = data.get('student_id', '').strip()
    
    # 如果提供了学号，直接按学号签到
    if student_id:
        student = get_student_by_id(student_id)
        if not student:
            return jsonify({'success': False, 'message': '学生不存在'})
        
        success, message, _ = add_checkin_record(student_id, checkin_type='老师代签')
        return jsonify({
            'success': success, 
            'message': message,
            'student_name': student['name'],
            'student_id': student_id,
            'checkin_type': '老师代签'
        })
    
    # 按姓名签到
    if not student_name:
        return jsonify({'success': False, 'message': '学生姓名不能为空'})
    
    # 查找匹配的学生
    students = get_students_by_name(student_name)
    
    if not students:
        return jsonify({'success': False, 'message': f'未找到名为 "{student_name}" 的学生'})
    
    # 如果只有一个匹配的学生，直接签到
    if len(students) == 1:
        student = students[0]
        success, message, _ = add_checkin_record(student['student_id'], checkin_type='老师代签')
        return jsonify({
            'success': success, 
            'message': message,
            'student_name': student['name'],
            'student_id': student['student_id'],
            'class_name': student['class_name'],
            'checkin_type': '老师代签'
        })
    
    # 如果有多个匹配的学生，返回列表供选择
    return jsonify({
        'success': False, 
        'message': f'找到 {len(students)} 个名为 "{student_name}" 的学生，请选择具体学生',
        'multiple_students': True,
        'students': students
    })


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
    """获取分数变更日志，默认只显示当前上课班级的学生"""
    student_id = request.args.get('student_id', '').strip()
    class_name = request.args.get('class_name', '').strip()
    student_name = request.args.get('student_name', '').strip()
    only_current_class = request.args.get('only_current_class', 'true').lower() == 'true'
    
    # 如果请求指定只显示当前上课班级，且没有提供班级参数
    if only_current_class and not class_name:
        session_info = get_current_class()
        if session_info['active'] and session_info['class_name']:
            class_name = session_info['class_name']
    
    logs = get_score_logs(
        student_id=student_id if student_id else None,
        class_name=class_name if class_name else None,
        student_name=student_name if student_name else None
    )
    
    # 添加当前筛选信息到响应
    result = {
        'success': True, 
        'data': logs,
        'filter_info': {
            'class_name': class_name if class_name else '全部班级',
            'is_current_class': only_current_class and bool(class_name)
        }
    }
    
    return jsonify(result)


@app.route('/api/db-info', methods=['GET'])
def api_get_db_info():
    """获取当前数据库环境信息"""
    return jsonify({'success': True, 'data': get_db_info()})


# ========== 页面路由 ==========

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
    db_info = get_db_info()
    
    print("=" * 50)
    print(f"班级管理系统已启动 [{DB_ENV_NAME}]")
    print("访问地址: http://127.0.0.1:5000")
    print("=" * 50)
    print(f"\n当前环境: {DB_ENV_NAME}")
    print(f"数据库文件: {db_info['file']}")
    print("\n切换环境方法:")
    print("  测试环境: set FLASK_ENV=testing  (Windows)")
    print("  测试环境: export FLASK_ENV=testing (Linux/Mac)")
    print("  或直接设置: set DB_ENV=testing")
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
