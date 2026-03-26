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
from app.api.deps import require_login, require_admin_or_teacher
from app.models.course_schedule import CourseSchedule, CourseScheduleResponse
from app.models.constants import ApiResponseConst, MessageConst, RoutePrefixConst

router = APIRouter(prefix=RoutePrefixConst.API, tags=["schedules"])


@router.get("/schedules", response_model=dict)
def get_schedules(
    class_name: Optional[str] = Query(None, description="按班级筛选"),
    teacher_id: Optional[int] = Query(None, description="按教师筛选"),
    day_of_week: Optional[int] = Query(None, description="按星期筛选(1-7)"),
    session: Session = Depends(get_session),
    user: dict = Depends(require_login)
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
def get_today_schedules(
    session: Session = Depends(get_session),
    user: dict = Depends(require_login)
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
    user: dict = Depends(require_admin_or_teacher)
):
    """导入课表"""
    # 检查文件类型
    filename = file.filename.lower()
    if not (filename.endswith('.xlsx') or filename.endswith('.csv')):
        raise HTTPException(
            status_code=HttpStatus.BAD_REQUEST,
            detail="只支持 .xlsx 或 .csv 格式的文件"
        )
    
    try:
        # 读取文件内容
        contents = await file.read()
        
        # 根据文件类型解析
        if filename.endswith('.xlsx'):
            df = pd.read_excel(BytesIO(contents))
        else:
            df = pd.read_csv(BytesIO(contents))
        
        # 检查必需的列
        required_columns = ['课程名称', '班级', '教师姓名', '星期', '开始时间', '结束时间']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=HttpStatus.BAD_REQUEST,
                detail=f"缺少必需的列: {', '.join(missing_columns)}"
            )
        
        # 导入数据
        imported_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # 数据校验
                course_name = str(row['课程名称']).strip()
                class_name = str(row['班级']).strip()
                teacher_name = str(row['教师姓名']).strip()
                day_of_week = int(row['星期'])
                start_time = str(row['开始时间']).strip()
                end_time = str(row['结束时间']).strip()
                
                if not all([course_name, class_name, teacher_name, start_time, end_time]):
                    errors.append(f"第 {index + 2} 行: 存在空值")
                    continue
                
                if day_of_week < 1 or day_of_week > 7:
                    errors.append(f"第 {index + 2} 行: 星期必须在 1-7 之间")
                    continue
                
                # 可选字段
                classroom = str(row.get('教室', '')).strip() if pd.notna(row.get('教室')) else None
                week_start = int(row.get('开始周', 1)) if pd.notna(row.get('开始周')) else 1
                week_end = int(row.get('结束周', 20)) if pd.notna(row.get('结束周')) else 20
                
                # 查找教师ID
                from app.models.user import User
                teacher = session.exec(
                    select(User).where(User.name == teacher_name)
                ).first()
                
                schedule = CourseSchedule(
                    course_name=course_name,
                    class_name=class_name,
                    teacher_id=teacher.id if teacher else None,
                    teacher_name=teacher_name,
                    day_of_week=day_of_week,
                    start_time=start_time,
                    end_time=end_time,
                    classroom=classroom,
                    week_start=week_start,
                    week_end=week_end,
                    created_at=datetime.now().isoformat(),
                    updated_at=datetime.now().isoformat()
                )
                
                session.add(schedule)
                imported_count += 1
                
            except Exception as e:
                errors.append(f"第 {index + 2} 行: {str(e)}")
        
        session.commit()
        
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
def delete_schedule(
    schedule_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher)
):
    """删除课程"""
    schedule = session.get(CourseSchedule, schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=HttpStatus.NOT_FOUND,
            detail="课程不存在"
        )
    
    # 教师只能删除自己的课程
    if user.get("role") == "teacher" and schedule.teacher_id != int(user.get("sub", 0)):
        raise HTTPException(
            status_code=HttpStatus.FORBIDDEN,
            detail="只能删除自己的课程"
        )
    
    session.delete(schedule)
    session.commit()
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: "课程已删除"
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
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=课表导入模板.xlsx"}
    )
