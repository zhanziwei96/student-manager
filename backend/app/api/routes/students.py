"""
学生管理 API - JWT 版本
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Request, HTTPException, Query, UploadFile, File
from pydantic import BaseModel, Field
from sqlmodel import Session, select
from app.core.db import get_session
from app.core.config import HttpStatus, get_settings
from app.core.jwt import require_admin, get_current_user
from app.core.class_cache import build_class_display_name
from app.api.deps import require_admin_or_teacher, verify_teacher_class_access
from app.crud import (
    get_student, get_students, get_students_by_class, get_students_by_classes,
    create_student, delete_student, reset_student_password,
    unlock_student_account, disable_students_by_class, count_students_filtered
)
from app.crud.checkin import get_today_checkins
from app.crud.course_session import get_active_course_session_by_class_id
from app.models.constants import (
    ApiResponseConst, MessageConst,
    ApiResponse, ApiSuccessResponse, ApiListResponse
)

router = APIRouter(tags=["students"])


class CreateStudentRequest(BaseModel):
    student_id: str = Field(..., min_length=1, description="学号")
    name: str = Field(..., min_length=1, description="姓名")
    class_id: Optional[int] = Field(None, description="班级ID（未分班为 None）")


class StudentWithCheckin(BaseModel):
    """带签到状态的学生数据"""
    id: Optional[int] = None
    student_id: str
    name: str
    class_name: str
    status: str
    is_account_enabled: bool
    checkin_status: str = "not_checked_in"
    created_at: Optional[datetime] = None


class StudentListResponse(ApiResponse[list[StudentWithCheckin]]):
    """学生列表响应（分页请求时附带 total）"""
    total: Optional[int] = Field(None, description="符合条件的学生总数（仅分页请求时返回）")


class StudentDetailResponse(ApiResponse[dict]):
    """学生详情响应"""
    pass


class StudentCreateResponse(ApiResponse[dict]):
    """学生创建响应"""
    pass


class StudentImportResult(BaseModel):
    """学生导入结果"""
    imported: int = Field(..., description="成功导入数")
    skipped: int = Field(..., description="跳过数（学号已存在）")
    skipped_rows: List[str] = Field(default_factory=list, description="跳过明细（含行号）")
    errors: List[str] = Field(default_factory=list, description="失败明细（含行号）")


class ImportResponse(ApiSuccessResponse):
    """批量导入响应"""
    data: StudentImportResult
    warning: Optional[str] = None


@router.get("/students", response_model=StudentListResponse)
async def get_students_list(
    request: Request,
    class_id: Optional[int] = Query(None, description="班级ID"),
    limit: Optional[int] = Query(None, ge=1, le=200, description="每页数量（不传则返回全部，保持向后兼容）"),
    offset: int = Query(0, ge=0, description="偏移量（分页用）"),
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher)
):
    """获取学生列表（管理员看所有，教师看负责班级；学生不可访问）

    分页说明：传入 limit 时按 limit/offset 分页并在响应中附带 total；
    不传 limit 时返回全部（旧客户端行为不变）。
    """
    # REVIEW-P1: 权限检查统一在 API 层处理，CRUD 层保持纯粹
    from app.models import User

    is_admin = user.get("is_admin", False)
    # 仅在分页请求时计算总数（避免全量请求多一次 COUNT 查询）
    total: Optional[int] = None

    if is_admin:
        # 管理员可以查看所有学生
        if class_id is not None:
            students = get_students_by_class(session, class_id, limit=limit, offset=offset)
            if limit is not None:
                total = count_students_filtered(session, class_id=class_id)
        else:
            students = get_students(session, limit=limit, offset=offset)
            if limit is not None:
                total = count_students_filtered(session)
    else:
        # 教师只能查看负责班级的学生
        user_id = user.get("sub")
        if not user_id:
            raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="无效的用户信息")

        from app.api.deps import get_teacher_accessible_classes
        # int 列表 / None（通配：面向全部班级）/ []（空集，fail-closed）
        assigned_class_ids = get_teacher_accessible_classes(user, session)

        if class_id is not None:
            # 如果指定了班级，检查权限（通配时放行）
            if assigned_class_ids is not None and class_id not in assigned_class_ids:
                raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="无权查看该班级学生")
            students = get_students_by_class(session, class_id, limit=limit, offset=offset)
            if limit is not None:
                total = count_students_filtered(session, class_id=class_id)
        elif assigned_class_ids is None:
            # 通配：面向全部班级
            students = get_students(session, limit=limit, offset=offset)
            if limit is not None:
                total = count_students_filtered(session)
        else:
            # 获取所有负责班级的学生 - 使用IN查询优化性能（REVIEW-P1）
            # 替代循环查询，减少数据库往返次数
            students = get_students_by_classes(session, assigned_class_ids, limit=limit, offset=offset)
            if limit is not None:
                total = count_students_filtered(session, class_ids=assigned_class_ids)

    # 获取当前课堂会话
    cs = get_active_course_session_by_class_id(session, class_id) if class_id is not None else None
    current_class_id = cs.class_id if cs and cs.status == "active" else None

    # 只获取当前课堂的签到记录（如果没有活跃课堂，则无人活跃）
    if current_class_id is not None:
        checkins = get_today_checkins(session, current_class_id)
    else:
        checkins = []
    checked_in_students = set(c.student_id for c in checkins)

    # 批量解析班级展示名（class_id → 完整展示名）
    from app.core.class_cache import get_class_display_names
    class_name_map = get_class_display_names(session, (s.class_id for s in students))

    # 构建带签到状态的学生列表（白名单字段，防止泄露 password_hash/version/last_login）
    students_with_checkin = []
    for student in students:
        # 只有在当前课堂签到才算已签到
        student_dict = {
            'student_id': student.student_id,
            'name': student.name,
            'class_name': class_name_map.get(student.class_id) or "未分班",
            'status': student.status,
            'is_account_enabled': student.is_account_enabled,
            'created_at': student.created_at,
            'checkin_status': 'checked_in' if student.student_id in checked_in_students else 'not_checked_in',
        }
        students_with_checkin.append(student_dict)
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: students_with_checkin,
        "total": total,
    }


@router.get("/students/import-template")
def download_import_template():
    """下载学生批量导入模板（xlsx，含填写说明页）"""
    import pandas as pd
    from io import BytesIO
    from fastapi.responses import StreamingResponse
    from urllib.parse import quote

    columns = ["学号", "姓名", "所属届", "专业", "班级名"]
    sample = pd.DataFrame([
        {"学号": "2513010101", "姓名": "张三", "所属届": "2025", "专业": "康复治疗技术", "班级名": "1班"},
        {"学号": "2513010102", "姓名": "李四", "所属届": "2025", "专业": "康复治疗技术", "班级名": "1班"},
    ])
    notes = pd.DataFrame([
        {"列名": "学号", "说明": "必填，唯一。已存在的学号会被跳过（不会修改既有学生）"},
        {"列名": "姓名", "说明": "必填"},
        {"列名": "所属届", "说明": "如 2025；班级不存在时用于自动建班，班级已存在可留空"},
        {"列名": "专业", "说明": "必填，如 康复治疗技术（与「所属届 + 班级名」一起定位班级）"},
        {"列名": "班级名", "说明": "必填，如 1班（只写班名，不要带届和专业；完整班级名由系统按「届+专业+班名」拼成）"},
        {"列名": "示例", "说明": "所属届=2025 / 专业=康复治疗技术 / 班级名=1班 → 2025届康复治疗技术1班"},
        {"列名": "初始密码", "说明": "无需填写，导入后默认密码为学号"},
    ])

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        sample.to_excel(writer, index=False, sheet_name="学生名单")
        notes.to_excel(writer, index=False, sheet_name="填写说明")
    output.seek(0)

    filename = quote("学生导入模板.xlsx", safe="")
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=utf-8''{filename}"}
    )


@router.post("/students/import", response_model=ImportResponse)
async def import_students(
    request: Request,
    file: UploadFile = File(..., description="Excel文件 (.xlsx)"),
    session: Session = Depends(get_session),
    user_id: str = Depends(require_admin)
):
    """导入学生（Excel，仅管理员）

    列：学号 / 姓名 / 所属届 / 专业 / 班级名。
    班级按「所属届 + 专业 + 班名」三元组定位：已存在则复用，不存在则自动建班；
    学号重复则跳过并在结果中列出。
    """
    import pandas as pd
    from io import BytesIO
    from app.core.logging import logger
    from app.core.upload import (
        validate_filename, validate_extension, validate_content_type, validate_file_size,
    )
    from app.crud.student import import_students as crud_import_students

    cleaned_filename = validate_filename(file.filename or "unnamed")
    validate_extension(cleaned_filename, ['.xlsx'])
    validate_content_type(file.content_type, [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
        'application/octet-stream',  # 部分客户端未带正确 MIME
    ])

    # 流式读取 + 大小限制（SEC-007：防止大文件内存耗尽）
    max_size_bytes = 10 * 1024 * 1024  # 10MB
    contents = bytearray()
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        contents.extend(chunk)
        if len(contents) > max_size_bytes:
            raise HTTPException(status_code=HttpStatus.BAD_REQUEST,
                                detail="文件大小超过限制（最大 10MB）")
    validate_file_size(len(contents), max_size_mb=10)

    try:
        df = pd.read_excel(BytesIO(contents))
        MAX_ROWS = 2000
        if len(df) > MAX_ROWS:
            raise HTTPException(status_code=HttpStatus.BAD_REQUEST,
                                detail=f"数据行数超过限制（最大 {MAX_ROWS} 行，当前 {len(df)} 行）")

        required = {"学号", "姓名"}
        missing = required - set(df.columns)
        if missing:
            raise HTTPException(
                status_code=HttpStatus.BAD_REQUEST,
                detail=f"缺少必需列: {', '.join(sorted(missing))}（请使用导入模板）",
            )

        def _cell(row, key) -> str:
            """取单元格文本：空单元格/NaN → ""

            pandas 把「数字列 + 任一空单元格」整列推断为 float64，
            直接 str() 会得到 "2028.0"、"2513010101.0"，故整数浮点还原为整数。
            """
            value = row.get(key)
            if pd.isna(value):
                return ""
            if isinstance(value, float) and value.is_integer():
                return str(int(value))
            return str(value).strip()

        records = [{
            "student_id": _cell(row, "学号"),
            "name": _cell(row, "姓名"),
            "cohort_year": _cell(row, "所属届"),
            "major": _cell(row, "专业"),
            "class_name": _cell(row, "班级名"),
        } for _, row in df.iterrows()]

        result = crud_import_students(session, records)
        logger.info(
            f"学生导入完成: 导入 {result['imported']} 条，跳过 {result['skipped']} 条，"
            f"失败 {len(result['errors'])} 条（上传者: {user_id}）"
        )

        response = {
            ApiResponseConst.SUCCESS: True,
            ApiResponseConst.MESSAGE: f"成功导入 {result['imported']} 名学生",
            ApiResponseConst.DATA: result,
        }
        if result["errors"] or result["skipped"]:
            response["warning"] = (
                f"{result['skipped']} 行跳过，{len(result['errors'])} 行导入失败"
            )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"学生导入失败: {e}")
        raise HTTPException(status_code=HttpStatus.INTERNAL_ERROR, detail=f"导入失败: {str(e)}")


@router.get("/students/{student_id}", response_model=StudentDetailResponse)
async def get_student_info(
    request: Request,
    student_id: str,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """获取学生信息（学生只能查看自己；教师限负责班级；响应不含 password_hash）"""
    from app.models import UserRoleConst

    student = get_student(session, student_id)
    if not student:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail='学生不存在')

    role = user.get("role", '')
    user_id = user.get("sub", '')

    # 学生只能查看自己的信息
    if role == UserRoleConst.STUDENT:
        if student_id != user_id:
            raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail='无权查看其他学生信息')
    elif role == UserRoleConst.TEACHER:
        # 教师只能查看负责班级的学生
        verify_teacher_class_access(user, student.class_id, session)

    # 白名单字段，防止泄露 password_hash（P0 修复）
    from app.core.class_cache import get_class_display_name_by_id
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {
            'student_id': student.student_id,
            'name': student.name,
            'class_id': student.class_id,
            'class_name': get_class_display_name_by_id(session, student.class_id) or "未分班",
            'status': student.status,
            'is_account_enabled': student.is_account_enabled,
            'created_at': student.created_at,
        }
    }


@router.post("/students", response_model=StudentCreateResponse)
async def add_student(
    request: Request,
    data: CreateStudentRequest,
    session: Session = Depends(get_session),
    user_id: str = Depends(require_admin)
):
    """添加学生（仅管理员）"""
    existing = get_student(session, data.student_id)
    if existing:
        raise HTTPException(status_code=HttpStatus.CONFLICT, detail='学号已存在')
    
    student = create_student(
        session,
        data.student_id,
        data.name,
        class_id=data.class_id
    )

    # 白名单字段，防止泄漏 password_hash/version（与 get_student_info 一致）
    from app.core.class_cache import get_class_display_name_by_id
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.STUDENT_CREATED,
        ApiResponseConst.DATA: {
            'student_id': student.student_id,
            'name': student.name,
            'class_id': student.class_id,
            'class_name': get_class_display_name_by_id(session, student.class_id) or "未分班",
            'status': student.status,
            'is_account_enabled': student.is_account_enabled,
            'created_at': student.created_at,
        }
    }


@router.delete("/students/{student_id}", response_model=ApiSuccessResponse)
async def remove_student(
    request: Request,
    student_id: str,
    session: Session = Depends(get_session),
    user_id: str = Depends(require_admin)
):
    """删除学生"""
    success = delete_student(session, student_id)
    if not success:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail='学生不存在')
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.STUDENT_DELETED
    }

class ResetStudentPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=1, description="新密码")


@router.put("/students/{student_id}/reset-password", response_model=ApiSuccessResponse)
async def reset_student_password_api(
    request: Request,
    student_id: str,
    data: ResetStudentPasswordRequest,
    session: Session = Depends(get_session),
    user_id: str = Depends(require_admin)
):
    """重置学生密码 - SEC-003: 使用简化密码哈希接口"""
    from app.core.security import hash_password
    password_hash = hash_password(data.new_password)
    
    student = reset_student_password(session, student_id, password_hash)
    if not student:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail='学生不存在')
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.PASSWORD_RESET
    }


@router.put("/students/{student_id}/unlock", response_model=ApiSuccessResponse)
async def unlock_student_api(
    request: Request,
    student_id: str,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher)
):
    """手动解锁学生账号（admin 或负责该班的教师）"""
    student = get_student(session, student_id)
    if not student:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail='学生不存在')

    verify_teacher_class_access(user, student.class_id, session)

    unlock_student_account(session, student_id)

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: "账号已解锁"
    }


class DisableByClassRequest(BaseModel):
    class_ids: List[int] = Field(..., min_length=1, description="班级ID列表")


@router.post("/students/disable-by-class", response_model=ApiResponse[dict])
async def disable_students_by_class_api(
    request: Request,
    data: DisableByClassRequest,
    session: Session = Depends(get_session),
    user_id: str = Depends(require_admin)
):
    """按班级批量禁用学生账号（学期归档，仅管理员）

    支持一次传多个班级。禁用后学生无法登录，班级从班级列表消失，历史数据保留。
    老师不再具备禁用权限（业务纠正：老师不教了不再等于禁用学生账号）。
    """
    total_disabled = 0
    for class_id in data.class_ids:
        total_disabled += disable_students_by_class(session, class_id)

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: f"已禁用 {total_disabled} 名学生",
        ApiResponseConst.DATA: {"disabled_count": total_disabled, "class_ids": data.class_ids}
    }


class UpdateStudentStatusRequest(BaseModel):
    status: str = Field(..., description="学籍状态: active|suspended|withdrawn|graduated")


@router.put("/students/{student_id}/status", response_model=ApiSuccessResponse)
def update_student_status(
    student_id: str,
    body: UpdateStudentStatusRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin)
):
    """学生学籍状态管理（在读/休学/退学/毕业，仅管理员）"""
    if body.status not in ("active", "suspended", "withdrawn", "graduated"):
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="无效学籍状态")

    student = get_student(session, student_id)
    if not student:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="学生不存在")

    student.status = body.status
    session.add(student)
    session.commit()
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: f"学籍状态已更新为 {body.status}",
    }


class TransferClassRequest(BaseModel):
    class_id: int = Field(..., description="目标行政班ID")


@router.put("/students/{student_id}/class", response_model=ApiSuccessResponse)
def transfer_student_class(
    student_id: str,
    body: TransferClassRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin)
):
    """学生转班（仅管理员）：更新行政班归属 + 同步冗余缓存"""
    from app.core.class_cache import invalidate_class_cache
    from app.core.term import get_current_semester_id
    from app.models import Class_, StudentClassSemester

    student = get_student(session, student_id)
    if not student:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="学生不存在")

    target = session.get(Class_, body.class_id)
    if target is None:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="目标班级不存在")

    # 行政班归属：当前学期记录 upsert（历史学期归属保留）
    semester_id = get_current_semester_id(session)
    if semester_id is not None:
        scs = session.exec(select(StudentClassSemester).where(
            StudentClassSemester.student_id == student_id,
            StudentClassSemester.semester_id == semester_id,
        )).first()
        if scs is None:
            session.add(StudentClassSemester(
                student_id=student_id, class_id=target.id, semester_id=semester_id,
            ))
        else:
            scs.class_id = target.id
            session.add(scs)

    # 同步冗余缓存（cohort_year 为身份属性不随转班更新）
    student.class_id = target.id
    session.add(student)
    session.commit()
    invalidate_class_cache()
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: f"已转入 {build_class_display_name(target)}",
    }
