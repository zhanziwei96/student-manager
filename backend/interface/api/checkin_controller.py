"""
签到API控制器
"""
from flask import Blueprint, request, jsonify, session
from functools import wraps

from infrastructure.persistence.database import Database
from infrastructure.persistence.repositories.sqlite_checkin_repository import SQLiteCheckinRepository
from infrastructure.persistence.repositories.sqlite_student_repository import SQLiteStudentRepository
from infrastructure.security.rate_limiter import rate_limit
from application.services.checkin_app_service import CheckinAppService
from application.services.privacy_service import PrivacyService


checkin_bp = Blueprint('checkin', __name__)


def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': '请先登录'}), 401
        return f(*args, **kwargs)
    return decorated_function


def get_checkin_service():
    """获取签到应用服务"""
    db = Database()
    checkin_repo = SQLiteCheckinRepository(db)
    student_repo = SQLiteStudentRepository(db)
    return CheckinAppService(checkin_repo, student_repo)


@checkin_bp.route('/api/checkin', methods=['POST'])
@rate_limit('checkin')
def student_checkin():
    """学生自主签到 (限流: 10次/分钟)"""
    try:
        data = request.json
        student_id = data.get('student_id', '').strip()
        name = data.get('name', '').strip()
        
        if not student_id:
            return jsonify({'success': False, 'message': '学号不能为空'}), 400
        
        if not name:
            return jsonify({'success': False, 'message': '姓名不能为空'}), 400
        
        service = get_checkin_service()
        success, message, checkin = service.student_checkin(student_id, name)
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'data': checkin.to_dict() if checkin else None
            })
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@checkin_bp.route('/api/teacher-checkin', methods=['POST'])
@login_required
def teacher_checkin():
    """老师代签到"""
    try:
        data = request.json
        student_name = data.get('student_name', '').strip()
        student_id = data.get('student_id', '').strip()
        
        service = get_checkin_service()
        
        # 优先使用学号
        if student_id:
            success, message, checkin, student = service.teacher_checkin(
                student_id,
                session['user_id'],
                is_student_id=True
            )
        elif student_name:
            success, message, checkin, student = service.teacher_checkin(
                student_name,
                session['user_id'],
                is_student_id=False
            )
        else:
            return jsonify({'success': False, 'message': '请提供学生学号或姓名'}), 400
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'data': {
                    'student_id': student.student_id.value if student else None,
                    'student_name': student.name if student else None,
                    'checkin': checkin.to_dict() if checkin else None
                }
            })
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@checkin_bp.route('/api/checkin/records', methods=['GET'])
@login_required
def get_checkin_records():
    """获取签到记录（带数据脱敏）"""
    try:
        # 查询参数
        student_id = request.args.get('student_id', '').strip()
        date = request.args.get('date', '').strip()
        class_name = request.args.get('class_name', '').strip()
        
        service = get_checkin_service()
        records = service.get_checkin_records(
            student_id=student_id if student_id else None,
            class_name=class_name if class_name else None,
            date=date if date else None,
            limit=200
        )
        
        # 数据脱敏处理
        privacy = PrivacyService()
        is_admin = session.get('is_admin', False)
        current_user_id = session.get('user_id')
        
        # 如果是老师，获取其管理的班级
        assigned_classes = None
        if not is_admin:
            from infrastructure.persistence.repositories.sqlite_user_repository import SQLiteUserRepository
            user_repo = SQLiteUserRepository(Database())
            user = user_repo.find_by_id(current_user_id)
            if user and user.assigned_classes:
                assigned_classes = user.assigned_classes
        
        result = []
        for record in records:
            record_dict = record.to_dict()
            # 应用数据脱敏
            record_dict = privacy.mask_checkin_record(
                record_dict,
                is_admin,
                assigned_classes
            )
            result.append(record_dict)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@checkin_bp.route('/api/checkin/stats', methods=['GET'])
@login_required
def get_checkin_stats():
    """获取签到统计"""
    try:
        student_id = request.args.get('student_id', '').strip()
        month = request.args.get('month', '').strip()  # YYYY-MM格式
        
        if not student_id:
            return jsonify({'success': False, 'message': '请提供学生学号'}), 400
        
        service = get_checkin_service()
        stats = service.get_student_checkin_stats(student_id, month)
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@checkin_bp.route('/api/checkin/today', methods=['GET'])
@login_required
def get_today_checkins():
    """获取今日班级签到情况"""
    try:
        class_name = request.args.get('class_name', '').strip()
        
        if not class_name:
            return jsonify({'success': False, 'message': '请提供班级名称'}), 400
        
        service = get_checkin_service()
        records = service.get_class_today_checkins(class_name)
        
        return jsonify({
            'success': True,
            'data': [r.to_dict() for r in records],
            'count': len(records)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
