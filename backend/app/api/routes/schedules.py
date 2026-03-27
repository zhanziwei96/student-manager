"""
课表管理 API
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query
from sqlmodel import Session, select
import pandas as pd
from io import BytesIO

from app.core.db import get_session
from app.core.config import HttpStatus
from app.core.upload import (
    _validate_filename,
    _validate_extension,
    _validate_content_type,
    _validate_file_size,
)
from app.api.deps import get_current_user, require_login, require_admin, require_admin_or_teacher
from app.crud import get_schedules as crud_get_schedules, delete_schedule as crud_delete_schedule
from app.models.course_schedule import CourseSchedule, CourseScheduleResponse
from app.models.constants import ApiResponseConst, MessageConst, RoutePrefixConst

router = APIRouter(prefix=RoutePrefixConst.API, tags=["schedules"])


@router.get("/schedules", response_model=dict)
async def get_schedules(
    class_name: Optional[str] = Query(None, description="按班级筛选"),
    teacher_id: Optional[int] = Query(None, description="按教师筛选"),
    day_of_week: Optional[int] = Query(None, description="按星期筛选(1-7)"),
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """获取课表列表"""
    query = select(CourseSchedule)
    
    # 教师只能查看自己的课表（除非有admin角色）
    if user.get("role") == "teacher":
        query = query.where(CourseSchedule.teacher_id == int(user.get("sub", 0)))
    elif teacher_id:
        query = query.where(CourseSchedule.teacher_id == teacher_id)
    
    if class_name:
        query = query.where(CourseSchedule.class_name == class_name)
    if day_of_week:
        query = query.where(CourseSchedule.day_of_week == day_of_week)
    
    # 按星期和时间排序
    query = query.order_by(CourseSchedule.day_of_week, CourseSchedule.start_time)
    
    schedules = session.exec(query).all()
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: [s.model_dump() for s in schedules]
    }


@router.get("/schedules/today", response_model=dict)
async def get_today_schedules(
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """获取今日课表"""
    # 获取今天是星期几 (1-7)
    today = datetime.now().isoweekday()
    
    query = select(CourseSchedule).where(CourseSchedule.day_of_week == today)
    
    # 教师只能查看自己的课表
    if user.get("role") == "teacher":
        query = query.where(CourseSchedule.teacher_id == int(user.get("sub", 0)))
    
    query = query.order_by(CourseSchedule.start_time)
    schedules = session.exec(query).all()
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: [s.model_dump() for s in schedules]
    }


@router.post("/schedules/import", response_model=dict)
async def import_schedules(
    file: UploadFile = File(..., description="Excel或CSV文件"),
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin)
):
    """导入课表"""
    # SEC-001: 文件上传安全检查（使用 upload.py 安全模块）
    
    # 1. 验证文件名（路径遍历防护）
    cleaned_filename = _validate_filename(file.filename or "unnamed")
    
    # 2. 验证扩展名白名单
    _validate_extension(cleaned_filename, ['.xlsx', '.csv'])
    
    # 3. 验证 MIME 类型
    _validate_content_type(file.content_type, [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
        'application/vnd.ms-excel',  # .xls
        'text/csv',  # .csv
        'application/csv',
        'text/plain',  # CSV 有时被识别为 text/plain
    ])
    
    # 4. 读取文件并验证大小
    contents = await file.read()
    _validate_file_size(len(contents), max_size_mb=10)
    
    # 使用清理后的文件名
    filename = cleaned_filename.lower()
    
    try:
        
        # 根据文件类型解析
        if filename.endswith('.xlsx'):
            df = pd.read_excel(BytesIO(contents))
        else:
            df = pd.read_csv(BytesIO(contents))
        
        # 5. 检查行数限制（最多 1000 行，防止内存攻击）
        MAX_ROWS = 1000
        if len(df) > MAX_ROWS:
            raise HTTPException(
                status_code=HttpStatus.BAD_REQUEST,
                detail=f"数据行数超过限制（最大 {MAX_ROWS} 行，当前 {len(df)} 行）"
            )
        
        # 检查必需的列
        required_columns = ['课程名称', '班级', '教师姓名', '星期', '开始时间', '结束时间']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=HttpStatus.BAD_REQUEST,
                detail=f"缺少必需的列: {', '.join(missing_columns)}"
            )
        
        # 准备数据并调用CRUD层函数（架构分层修复）
        # 将DataFrame转换为字典列表，业务逻辑移到CRUD层
        records = []
        for _, row in df.iterrows():
            records.append({
                'course_name': row.get('课程名称'),
                'class_name': row.get('班级'),
                'teacher_name': row.get('教师姓名'),
                'day_of_week': row.get('星期'),
                'start_time': row.get('开始时间'),
                'end_time': row.get('结束时间'),
                'classroom': row.get('教室') if pd.notna(row.get('教室')) else None,
                'week_start': int(row.get('开始周', 1)) if pd.notna(row.get('开始周')) else 1,
                'week_end': int(row.get('结束周', 20)) if pd.notna(row.get('结束周')) else 20,
            })
        
        # 调用CRUD层函数处理所有业务逻辑
        from app.crud import import_schedules as crud_import_schedules
        imported_count, errors = crud_import_schedules(session, records)
        
        result = {
            ApiResponseConst.SUCCESS: True,
            ApiResponseConst.MESSAGE: f"成功导入 {imported_count} 条课程",
            ApiResponseConst.DATA: {
                "imported": imported_count,
                "errors": errors
            }
        }
        
        if errors:
            result["warning"] = f"有 {len(errors)} 行导入失败"
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.INTERNAL_ERROR,
            detail=f"导入失败: {str(e)}"
        )


@router.delete("/schedules/{schedule_id}", response_model=dict)
async def delete_schedule_api(
    schedule_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin)
):
    """删除课程（仅管理员）- 使用CRUD层函数"""
    success = crud_delete_schedule(session, schedule_id)
    if not success:
        raise HTTPException(
            status_code=HttpStatus.NOT_FOUND,
            detail="课程不存在"
        )
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: "课程已删除"
    }


@router.put("/schedules/{schedule_id}/assign", response_model=dict)
async def assign_teacher_to_schedule(
    schedule_id: int,
    teacher_id: int,
    teacher_name: str,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin)
):
    """为课程分配教师（仅管理员）"""
    # 查询课程
    schedule = session.get(CourseSchedule, schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=HttpStatus.NOT_FOUND,
            detail="课程不存在"
        )
    
    # 更新教师信息
    schedule.teacher_id = teacher_id
    schedule.teacher_name = teacher_name
    session.add(schedule)
    session.commit()
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: f"已将课程 '{schedule.course_name}' 分配给教师 '{teacher_name}'"
    }


@router.put("/schedules/{schedule_id}/unassign", response_model=dict)
async def unassign_teacher_from_schedule(
    schedule_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin)
):
    """取消课程的教师分配（仅管理员）"""
    # 查询课程
    schedule = session.get(CourseSchedule, schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=HttpStatus.NOT_FOUND,
            detail="课程不存在"
        )
    
    # 清除教师信息
    schedule.teacher_id = None
    schedule.teacher_name = None
    session.add(schedule)
    session.commit()
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: f"已取消课程 '{schedule.course_name}' 的教师分配"
    }


@router.get("/schedules/template")
def download_template():
    """下载导入模板"""
    # 创建示例数据
    data = {
        '课程名称': ['计算机基础', '数据结构', '英语'],
        '班级': ['2025康复治疗技术1班', '2025康复治疗技术1班', '2025康复治疗技术2班'],
        '教师姓名': ['张老师', '李老师', '王老师'],
        '星期': [1, 3, 5],
        '开始时间': ['08:00', '10:00', '14:00'],
        '结束时间': ['09:40', '11:40', '15:40'],
        '教室': ['A-101', 'B-202', 'C-303'],
        '开始周': [1, 1, 1],
        '结束周': [20, 20, 20]
    }
    
    df = pd.DataFrame(data)
    
    # 生成 Excel 文件
    output = BytesIO()
    df.to_excel(output, index=False, sheet_name='课表模板')
    output.seek(0)
    
    from fastapi.responses import StreamingResponse
    
    # RFC 5987 编码中文文件名
    from urllib.parse import quote
    filename = quote("课表导入模板.xlsx", safe="")
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=utf-8''{filename}"}
    )
