"""
班级管理系统 - Flask 后端 (API 服务器)
为 Vue 3 + Element Plus 前端提供 RESTful API
"""

import os
from functools import wraps
from datetime import datetime
from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from config import config
from data_manager import (
    init_data, get_all_students, get_student_by_id, get_students_by_name, add_student,
    import_students_from_xlsx, update_student_score, add_checkin_record,
    get_checkin_records, get_score_logs, delete_student, delete_class,
    authenticate_user, change_password, get_user_by_id,
    set_current_class, get_current_class, get_class_students_with_checkin_status,
    reset_all_scores, close_db_connection, get_db_info, DB_ENV_NAME,
    get_db_connection, query_student_info
)

# 根据环境变量加载配置
env = os.environ.get('FLASK_ENV', 'production')
app = Flask(__name__, static_folder='../frontend/dist', static_url_path='')
app.config.from_object(config.get(env, config['default']))

# 生产环境关闭 CORS，Nginx 会处理跨域
# 开发环境启用 CORS
if env == 'development':
    CORS(app, supports_credentials=True, origins=['http://localhost:3000', 'http://127.0.0.1:3000'])

# 上传文件临时目录
UPLOAD_FOLDER = app.config.get('UPLOAD_FOLDER', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def login_required(f):
    """登录验证装饰器（API版本）"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': '请先登录'}), 401
        return f(*args, **kwargs)
    return decorated_function


@app.teardown_appcontext
def close_db(error):
    """请求结束时关闭数据库连接"""
    close_db_connection()


def admin_required(f):
    """管理员验证装饰器（API版本）"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': '请先登录'}), 401
        
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
    # 支持参数控制是否返回签到状态
    with_checkin = request.args.get('with_checkin', 'false').lower() == 'true'
    students = get_all_students(with_checkin_status=with_checkin)
    return jsonify({'success': True, 'data': students})


@app.route('/api/stats', methods=['GET'])
def api_get_stats():
    """获取首页统计数据（优化版）"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. 获取学生总数和班级数
        cursor.execute('SELECT COUNT(*) as count FROM students')
        student_count = cursor.fetchone()['count']
        
        # 2. 获取班级数量
        cursor.execute('SELECT COUNT(DISTINCT class_name) as count FROM students')
        class_count = cursor.fetchone()['count']
        
        # 3. 获取今日签到数
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT COUNT(*) as count 
            FROM checkin_records 
            WHERE DATE(checkin_time) = ?
        ''', (today,))
        today_checkin = cursor.fetchone()['count']
        
        # 4. 获取平均分数
        cursor.execute('SELECT AVG(score) as avg_score FROM students')
        avg_score_row = cursor.fetchone()
        avg_score = round(avg_score_row['avg_score']) if avg_score_row['avg_score'] else 70
        
        # 5. 获取分数前10名（直接在数据库排序）
        cursor.execute('''
            SELECT student_id, name, class_name, score 
            FROM students 
            ORDER BY score DESC 
            LIMIT 10
        ''')
        top_students = [
            {
                'student_id': row['student_id'],
                'name': row['name'],
                'class_name': row['class_name'],
                'score': row['score'] if row['score'] else 0
            }
            for row in cursor.fetchall()
        ]
        
        # 6. 获取班级列表及签到统计
        cursor.execute('''
            SELECT s.class_name, COUNT(*) as total,
                   COUNT(CASE WHEN cr.record_id IS NOT NULL THEN 1 END) as checked
            FROM students s
            LEFT JOIN checkin_records cr ON s.student_id = cr.student_id 
                AND DATE(cr.checkin_time) = ?
            GROUP BY s.class_name
            ORDER BY s.class_name
        ''', (today,))
        class_stats = [
            {
                'class_name': row['class_name'],
                'student_count': row['total'],
                'checkin_count': row['checked']
            }
            for row in cursor.fetchall()
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'student_count': student_count,
                'class_count': class_count,
                'today_checkin': today_checkin,
                'today_checkin_rate': round(today_checkin / student_count * 100) if student_count > 0 else 0,
                'avg_score': avg_score,
                'top_students': top_students,
                'class_stats': class_stats
            }
        })
    except Exception as e:
        import traceback
        print(f"获取统计数据失败: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'获取统计数据失败: {str(e)}'
        }), 500


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
        score_change = float(score_change)
    except ValueError:
        return jsonify({'success': False, 'message': '分数变更必须是数字'})
    
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
def api_get_class_session():
    """获取当前上课状态（公开接口）"""
    try:
        session_info = get_current_class()
        return jsonify({
            'success': True,
            'data': session_info
        })
    except Exception as e:
        import traceback
        print(f"获取上课状态失败: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'获取上课状态失败: {str(e)}'
        }), 500


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
    try:
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
    except Exception as e:
        import traceback
        print(f"获取班级学生状态失败: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'获取班级学生状态失败: {str(e)}'
        }), 500


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


# ========== 学生自助查询 ==========

@app.route('/api/student/query', methods=['POST'])
def api_query_student():
    """学生自助查询 - 通过学号和姓名查询自己的分数、排名和记录"""
    try:
        data = request.json
        student_id = data.get('student_id', '').strip()
        name = data.get('name', '').strip()
        
        if not student_id or not name:
            return jsonify({'success': False, 'message': '请输入学号和姓名'})
        
        result, error = query_student_info(student_id, name)
        
        if error:
            return jsonify({'success': False, 'message': error})
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        import traceback
        print(f"学生查询失败: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': f'查询失败: {str(e)}'}), 500


# ========== 页面路由 ==========

# 生产环境：Vue 前端路由交由前端处理
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    """处理前端路由"""
    # API 请求直接返回 404
    if path.startswith('api/'):
        return jsonify({'success': False, 'message': 'API not found'}), 404
    
    # 静态文件直接返回
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    
    # 其他路径返回 index.html（Vue 前端处理路由）
    return send_from_directory(app.static_folder, 'index.html')

# ========== 错误处理 ==========

@app.errorhandler(500)
def internal_error(error):
    """处理 500 错误"""
    import traceback
    print(f"500 错误: {str(error)}")
    print(traceback.format_exc())
    return jsonify({'success': False, 'message': f'服务器错误: {str(error)}'}), 500


@app.errorhandler(401)
def unauthorized_error(error):
    """处理 401 错误（API版本）"""
    return jsonify({'success': False, 'message': '请先登录'}), 401


if __name__ == '__main__':
    init_data()
    db_info = get_db_info()
    
    # 获取当前环境
    env = os.environ.get('FLASK_ENV', 'production')
    is_dev = env == 'development'
    
    print("=" * 50)
    print(f"班级管理系统已启动 [{DB_ENV_NAME}]")
    print("=" * 50)
    print(f"\n当前环境: {env}")
    print(f"数据库文件: {db_info['file']}")
    
    if is_dev:
        print("\n开发模式:")
        print("- 前端开发服务器: http://localhost:3000")
        print("- Flask API 服务器: http://localhost:5000")
        print("\n切换生产环境:")
        print("  export FLASK_ENV=production")
    else:
        print("\n生产模式:")
        print("- 访问地址: http://localhost:5000")
        print("\n建议使用 Nginx + Gunicorn 部署")
        print("  gunicorn -w 4 -b 127.0.0.1:5000 app:app")
    
    print("\n默认管理员账户:")
    print("- 用户名: admin")
    print("- 密码: admin123")
    print("\n按 Ctrl+C 停止服务")
    print("=" * 50)
    
    # 生产环境关闭 debug
    app.run(debug=is_dev, host='0.0.0.0', port=5000, threaded=True)
