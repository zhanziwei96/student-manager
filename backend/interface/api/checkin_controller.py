"""
签到API控制器 - FastAPI版本
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Request, HTTPException, Query
from pydantic import BaseModel, Field

from infrastructure.persistence.database import Database
from infrastructure.persistence.repositories.sqlite_checkin_repository import SQLiteCheckinRepository
from infrastructure.persistence.repositories.sqlite_student_repository import SQLiteStudentRepository
from infrastructure.persistence.repositories.sqlite_user_repository import SQLiteUserRepository
from infrastructure.security.rate_limiter import checkin_limit
from infrastructure.security.session import require_login, is_admin
from infrastructure.security.xss_protection import sanitize_checkin_record, escape_html
from infrastructure.logging import logger
from infrastructure.config import AuthConfig, HttpStatus, PaginationConfig
from application.services.checkin_app_service import CheckinAppService
from application.services.privacy_service import PrivacyService


router = APIRouter(prefix="/api", tags=["checkin"])


# ============ Pydantic模型 ============

class StudentCheckinRequest(BaseModel):
    student_id: str = Field(..., min_length=AuthConfig.NAME_MIN_LENGTH, description="学号")
    name: str = Field(..., min_length=AuthConfig.NAME_MIN_LENGTH, description="姓名")


class TeacherCheckinRequest(BaseModel):
    student_name: Optional[str] = Field(None, description="学生姓名")
    student_id: Optional[str] = Field(None, description="学生学号")


# ============ 依赖注入 ============

def get_checkin_service():
    """获取签到应用服务"""
    db = Database()
    checkin_repo = SQLiteCheckinRepository(db)
    student_repo = SQLiteStudentRepository(db)
    return CheckinAppService(checkin_repo, student_repo)


# ============ API端点 ============

@router.post(
    "/checkin", 
    response_model=dict,
    dependencies=[Depends(checkin_limit())]
)
async def student_checkin(
    request: Request,
    data: StudentCheckinRequest,
    service: CheckinAppService = Depends(get_checkin_service)
):
    """学生自主签到（限流: 10次/分钟）"""
    try:
        success, message, checkin = service.student_checkin(
            data.student_id.strip(),
            data.name.strip()
        )
        
        if success:
            # XSS防护：对签到记录进行HTML转义
            return {
                'success': True,
                'message': message,
                'data': sanitize_checkin_record(checkin.to_dict()) if checkin else None
            }
        else:
            raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail=message)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"学生签到失败: {e}", exc_info=True)
        raise HTTPException(status_code=HttpStatus.INTERNAL_ERROR, detail=str(e))


@router.post("/teacher-checkin", response_model=dict)
async def teacher_checkin(
    request: Request,
    data: TeacherCheckinRequest,
    service: CheckinAppService = Depends(get_checkin_service)
):
    """老师代签到"""
    require_login(request)
    
    try:
        # 优先使用学号
        if data.student_id:
            success, message, checkin, student = service.teacher_checkin(
                data.student_id.strip(),
                request.session.get('user_id'),
                is_student_id=True
            )
        elif data.student_name:
            success, message, checkin, student = service.teacher_checkin(
                data.student_name.strip(),
                request.session.get('user_id'),
                is_student_id=False
            )
        else:
            raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail='请提供学生学号或姓名')
        
        if success:
            # XSS防护：对返回数据进行HTML转义
            return {
                'success': True,
                'message': message,
                'data': {
                    'student_id': student.student_id.value if student else None,
                    'student_name': escape_html(student.name) if student else None,
                    'checkin': sanitize_checkin_record(checkin.to_dict()) if checkin else None
                }
            }
        else:
            raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail=message)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"老师代签失败: {e}", exc_info=True)
        raise HTTPException(status_code=HttpStatus.INTERNAL_ERROR, detail=str(e))


@router.get("/checkin/records", response_model=dict)
async def get_checkin_records(
    request: Request,
    student_id: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
    class_name: Optional[str] = Query(None)
):
    """获取签到记录（带数据脱敏）"""
    require_login(request)
    
    try:
        db = Database()
        service = CheckinAppService(
            SQLiteCheckinRepository(db),
            SQLiteStudentRepository(db)
        )
        
        records = service.get_checkin_records(
            student_id=student_id,
            class_name=class_name,
            date=date,
            limit=PaginationConfig.MAX_CHECKIN_RECORDS
        )
        
        # 数据脱敏处理
        privacy = PrivacyService()
        is_admin = request.session.get('is_admin', False)
        current_user_id = request.session.get('user_id')
        
        # 获取老师管理的班级
        assigned_classes = None
        if not is_admin:
            user_repo = SQLiteUserRepository(db)
            user = user_repo.find_by_id(current_user_id)
            if user and user.assigned_classes:
                assigned_classes = user.assigned_classes
        
        result = []
        for record in records:
            record_dict = record.to_dict()
            # 先进行隐私脱敏
            record_dict = privacy.mask_checkin_record(
                record_dict,
                is_admin,
                assigned_classes
            )
            # XSS防护：HTML转义
            record_dict = sanitize_checkin_record(record_dict)
            result.append(record_dict)
        
        return {
            'success': True,
            'data': result
        }
        
    except Exception as e:
        logger.error(f"获取签到记录失败: {e}", exc_info=True)
        raise HTTPException(status_code=HttpStatus.INTERNAL_ERROR, detail=str(e))


@router.get("/checkin/stats", response_model=dict)
async def get_checkin_stats(
    request: Request,
    student_id: str = Query(..., description="学生学号"),
    month: Optional[str] = Query(None, description="月份(YYYY-MM格式)")
):
    """获取签到统计"""
    require_login(request)
    
    try:
        db = Database()
        service = CheckinAppService(
            SQLiteCheckinRepository(db),
            SQLiteStudentRepository(db)
        )
        stats = service.get_student_checkin_stats(student_id, month)
        
        return {
            'success': True,
            'data': stats
        }
        
    except Exception as e:
        logger.error(f"获取签到统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=HttpStatus.INTERNAL_ERROR, detail=str(e))


@router.get("/checkin/today", response_model=dict)
async def get_today_checkins(
    request: Request,
    class_name: str = Query(..., description="班级名称")
):
    """获取今日班级签到情况"""
    require_login(request)
    
    try:
        db = Database()
        service = CheckinAppService(
            SQLiteCheckinRepository(db),
            SQLiteStudentRepository(db)
        )
        records = service.get_class_today_checkins(class_name)
        
        # XSS防护：对签到记录进行HTML转义
        records_data = [sanitize_checkin_record(r.to_dict()) for r in records]
        
        return {
            'success': True,
            'data': records_data,
            'count': len(records)
        }
        
    except Exception as e:
        logger.error(f"获取今日签到列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=HttpStatus.INTERNAL_ERROR, detail=str(e))
