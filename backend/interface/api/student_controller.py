"""
学生API控制器
处理HTTP请求，调用应用服务
"""
from flask import Blueprint, request, jsonify, session
from functools import wraps

from infrastructure.persistence.database import Database
from infrastructure.persistence.repositories.sqlite_student_repository import SQLiteStudentRepository
from infrastructure.persistence.repositories.sqlite_score_log_repository import SQLiteScoreLogRepository
from application.services.student_app_service import StudentAppService
from application.dto.student_dto import CreateStudentDTO, UpdateScoreDTO


student_bp = Blueprint('students', __name__)


def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': '请先登录'}), 401
        return f(*args, **kwargs)
    return decorated_function


def get_student_service():
    """获取学生应用服务（依赖注入）"""
    db = Database()
    repo = SQLiteStudentRepository(db)
    log_repo = SQLiteScoreLogRepository(db)
    return StudentAppService(repo, log_repo)


@student_bp.route('/api/students', methods=['GET'])
@login_required
def get_students():
    """获取学生列表"""
    try:
        service = get_student_service()
        class_name = request.args.get('class_name')
        
        if class_name:
            students = service.get_students_by_class(class_name)
        else:
            students = service.get_all_students()
        
        return jsonify({
            'success': True,
            'data': [s.__dict__ for s in students]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@student_bp.route('/api/students/<student_id>', methods=['GET'])
@login_required
def get_student(student_id):
    """获取单个学生"""
    try:
        service = get_student_service()
        student = service.get_student_by_id(student_id)
        
        if student:
            return jsonify({
                'success': True,
                'data': student.__dict__
            })
        return jsonify({'success': False, 'message': '学生不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@student_bp.route('/api/students', methods=['POST'])
@login_required
def create_student():
    """创建学生"""
    try:
        data = request.json
        dto = CreateStudentDTO(
            student_id=data.get('student_id', '').strip(),
            name=data.get('name', '').strip(),
            class_name=data.get('class_name', '').strip() or None
        )
        
        service = get_student_service()
        student = service.create_student(dto)
        
        return jsonify({
            'success': True,
            'message': '学生创建成功',
            'data': student.__dict__
        })
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@student_bp.route('/api/students/<student_id>/score', methods=['POST'])
@login_required
def update_score(student_id):
    """更新学生分数"""
    try:
        data = request.json
        dto = UpdateScoreDTO(
            student_id=student_id,
            delta=float(data.get('score_change', 0)),
            reason=data.get('reason', '').strip(),
            operator=session.get('username', 'unknown')
        )
        
        service = get_student_service()
        student = service.update_score(dto)
        
        return jsonify({
            'success': True,
            'message': '分数更新成功',
            'data': student.__dict__
        })
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@student_bp.route('/api/students/<student_id>', methods=['DELETE'])
@login_required
def delete_student(student_id):
    """删除学生"""
    try:
        service = get_student_service()
        service.delete_student(student_id)
        return jsonify({'success': True, 'message': '学生删除成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@student_bp.route('/api/score/logs', methods=['GET'])
@login_required
def get_score_logs():
    """获取分数变更日志"""
    try:
        student_id = request.args.get('student_id', '').strip()
        class_name = request.args.get('class_name', '').strip()
        
        db = Database()
        log_repo = SQLiteScoreLogRepository(db)
        
        logs = log_repo.find_by_filters(
            student_id=student_id if student_id else None,
            class_name=class_name if class_name else None,
            limit=100
        )
        
        return jsonify({
            'success': True,
            'data': [log.to_dict() for log in logs]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@student_bp.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    """获取统计数据"""
    try:
        db = Database()
        
        # 基础统计
        with db.get_connection() as conn:
            # 总学生数
            cursor = conn.execute("SELECT COUNT(*) as count FROM students")
            total_students = cursor.fetchone()['count']
            
            # 班级列表
            cursor = conn.execute(
                "SELECT class_name, COUNT(*) as count FROM students GROUP BY class_name"
            )
            class_stats = [
                {'class_name': row['class_name'], 'student_count': row['count']}
                for row in cursor.fetchall()
            ]
            
            # 今日签到人数
            from datetime import datetime
            today = datetime.now().strftime('%Y-%m-%d')
            cursor = conn.execute(
                "SELECT COUNT(DISTINCT student_id) as count FROM checkin_records WHERE checkin_date = ?",
                (today,)
            )
            today_checkins = cursor.fetchone()['count']
            
            # 平均分
            cursor = conn.execute("SELECT AVG(score) as avg FROM students")
            avg_score = cursor.fetchone()['avg'] or 0
        
        return jsonify({
            'success': True,
            'data': {
                'total_students': total_students,
                'class_count': len(class_stats),
                'class_stats': class_stats,
                'today_checkins': today_checkins,
                'average_score': round(avg_score, 2)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@student_bp.route('/api/admin/reset-scores', methods=['POST'])
@login_required
def reset_all_scores():
    """重置所有学生分数（管理员）"""
    try:
        if not session.get('is_admin'):
            return jsonify({'success': False, 'message': '需要管理员权限'}), 403
        
        from domain.value_objects.score import Score
        db = Database()
        repo = SQLiteStudentRepository(db)
        
        students = repo.find_all()
        for student in students:
            student.score = Score(70)  # 重置为默认分数
            repo.save(student)
        
        return jsonify({
            'success': True,
            'message': f'已重置{len(students)}名学生的分数'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@student_bp.route('/api/students/import', methods=['POST'])
@login_required
def import_students():
    """从Excel导入学生"""
    try:
        import io
        from openpyxl import load_workbook
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '请上传文件'}), 400
        
        file = request.files['file']
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'success': False, 'message': '请上传Excel文件'}), 400
        
        # 读取Excel
        stream = io.BytesIO(file.read())
        wb = load_workbook(stream)
        ws = wb.active
        
        service = get_student_service()
        success_count = 0
        error_count = 0
        errors = []
        
        # 从第二行开始读取（假设第一行是标题）
        for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            try:
                if not row or len(row) < 2:
                    continue
                
                student_id = str(row[0]).strip() if row[0] else None
                name = str(row[1]).strip() if row[1] else None
                class_name = str(row[2]).strip() if len(row) > 2 and row[2] else None
                
                if not student_id or not name:
                    continue
                
                dto = CreateStudentDTO(
                    student_id=student_id,
                    name=name,
                    class_name=class_name
                )
                service.create_student(dto)
                success_count += 1
                
            except Exception as e:
                error_count += 1
                errors.append(f"第{row_num}行: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': f'导入完成: 成功{success_count}条, 失败{error_count}条',
            'data': {'success_count': success_count, 'error_count': error_count, 'errors': errors[:10]}
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'导入失败: {str(e)}'}), 500
