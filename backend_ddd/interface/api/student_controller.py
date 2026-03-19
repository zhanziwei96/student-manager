"""
学生API控制器
处理HTTP请求，调用应用服务
"""
from flask import Blueprint, request, jsonify, session
from functools import wraps

from infrastructure.persistence.database import Database
from infrastructure.persistence.repositories.sqlite_student_repository import SQLiteStudentRepository
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
    return StudentAppService(repo)


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
