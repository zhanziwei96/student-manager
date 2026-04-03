"""
系统相关 API
"""
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, Field
from sqlmodel import Session, text
from app.core.db import get_session, engine
from app.core.config import get_settings
from app.core.jwt import get_current_user
from app.models.constants import (
    VERSION, SystemStatusConst, ApiResponseConst, RoutePrefixConst,
    ApiResponse
)

router = APIRouter(tags=["system"])


# 响应模型定义
class HealthData(BaseModel):
    """健康检查响应数据"""
    status: str
    timestamp: str
    version: str


class SystemStatsData(BaseModel):
    """系统统计数据"""
    total_students: int
    total_classes: int
    today_checkins: int


class DashboardData(BaseModel):
    """仪表盘数据"""
    total_students: int
    total_classes: int
    today_checkins: int
    checked_in: int
    not_checked_in: int
    checkin_rate: float
    score_ranking: list[dict]


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    timestamp: str
    version: str


class DependencyStatus(BaseModel):
    """依赖状态"""
    name: str = Field(..., description="依赖名称")
    status: str = Field(..., description="状态：healthy/unhealthy")
    response_time_ms: float = Field(..., description="响应时间（毫秒）")
    message: str = Field(default="", description="状态消息")


class EnhancedHealthData(BaseModel):
    """增强健康检查数据"""
    status: str = Field(..., description="整体状态")
    timestamp: str = Field(..., description="时间戳")
    version: str = Field(..., description="版本")
    uptime_seconds: float = Field(..., description="运行时间（秒）")
    dependencies: list[DependencyStatus] = Field(default_factory=list, description="依赖状态列表")


class EnhancedHealthResponse(BaseModel):
    """增强健康检查响应"""
    status: str
    timestamp: str
    version: str
    uptime_seconds: float
    dependencies: list[DependencyStatus]


class SystemStatsResponse(ApiResponse[SystemStatsData]):
    """系统统计响应"""
    pass


class DashboardResponse(ApiResponse[DashboardData]):
    """仪表盘响应"""
    pass


# 启动时间记录
_start_time = datetime.now()


def _check_database_health() -> DependencyStatus:
    """检查数据库健康状态"""
    import time
    start = time.time()
    try:
        # 执行简单查询测试数据库连接
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.scalar()
        elapsed = (time.time() - start) * 1000
        return DependencyStatus(
            name="database",
            status="healthy",
            response_time_ms=round(elapsed, 2),
            message="数据库连接正常"
        )
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        return DependencyStatus(
            name="database",
            status="unhealthy",
            response_time_ms=round(elapsed, 2),
            message=f"数据库连接失败: {str(e)}"
        )


def _check_filesystem_health() -> DependencyStatus:
    """检查文件系统健康状态"""
    import time
    start = time.time()
    try:
        settings = get_settings()
        # 检查数据库目录是否可写
        db_path = Path(settings.get_database_path())
        db_dir = db_path.parent

        # 如果目录不存在，尝试创建（测试环境需要）
        if not db_dir.exists():
            db_dir.mkdir(parents=True, exist_ok=True)

        # 检查目录是否存在且可写
        test_file = db_dir / ".health_check_tmp"
        test_file.write_text("test")
        test_file.unlink()

        elapsed = (time.time() - start) * 1000
        return DependencyStatus(
            name="filesystem",
            status="healthy",
            response_time_ms=round(elapsed, 2),
            message=f"文件系统可写: {db_dir}"
        )
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        return DependencyStatus(
            name="filesystem",
            status="unhealthy",
            response_time_ms=round(elapsed, 2),
            message=f"文件系统检查失败: {str(e)}"
        )


def _check_disk_space() -> DependencyStatus:
    """检查磁盘空间"""
    import shutil
    import time
    start = time.time()
    try:
        settings = get_settings()
        db_path = Path(settings.get_database_path())
        db_dir = db_path.parent

        # 如果目录不存在，尝试创建（测试环境需要）
        if not db_dir.exists():
            db_dir.mkdir(parents=True, exist_ok=True)

        # 获取磁盘使用情况
        stat = shutil.disk_usage(db_dir)
        free_gb = stat.free / (1024**3)
        total_gb = stat.total / (1024**3)
        used_percent = (stat.used / stat.total) * 100

        elapsed = (time.time() - start) * 1000

        # 如果可用空间小于 1GB 或使用率超过 90%，标记为警告
        if free_gb < 1 or used_percent > 90:
            return DependencyStatus(
                name="disk_space",
                status="warning",
                response_time_ms=round(elapsed, 2),
                message=f"磁盘空间不足: 可用 {free_gb:.2f}GB / 总共 {total_gb:.2f}GB"
            )

        return DependencyStatus(
            name="disk_space",
            status="healthy",
            response_time_ms=round(elapsed, 2),
            message=f"磁盘空间充足: 可用 {free_gb:.2f}GB / 总共 {total_gb:.2f}GB"
        )
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        return DependencyStatus(
            name="disk_space",
            status="unhealthy",
            response_time_ms=round(elapsed, 2),
            message=f"磁盘空间检查失败: {str(e)}"
        )


@router.get("/health", response_model=HealthResponse)
def health_check():
    """健康检查 - 基础版本（快速响应）"""
    return {
        "status": SystemStatusConst.HEALTHY,
        "timestamp": datetime.now().isoformat(),
        "version": VERSION
    }


@router.get("/health/detailed", response_model=EnhancedHealthResponse)
def health_check_detailed():
    """
    增强健康检查 - 包含依赖状态检查

    检查项目：
    - database: 数据库连接状态
    - filesystem: 文件系统可写状态
    - disk_space: 磁盘空间使用情况

    返回 503 如果任何关键依赖不健康
    """
    from time import time

    # 检查各项依赖
    dependencies = [
        _check_database_health(),
        _check_filesystem_health(),
        _check_disk_space(),
    ]

    # 计算整体状态
    critical_deps = ["database", "filesystem"]
    critical_statuses = [d for d in dependencies if d.name in critical_deps]

    has_unhealthy = any(d.status == "unhealthy" for d in critical_statuses)
    has_warning = any(d.status == "warning" for d in dependencies)

    if has_unhealthy:
        overall_status = "unhealthy"
    elif has_warning:
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    # 计算运行时间
    uptime = (datetime.now() - _start_time).total_seconds()

    return {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "version": VERSION,
        "uptime_seconds": round(uptime, 2),
        "dependencies": dependencies
    }


@router.get("/stats", response_model=SystemStatsResponse)
def get_stats(
    request: Request,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """获取系统统计（需要登录）- 使用 COUNT 查询优化性能"""
    from app.crud import count_students, get_all_classes
    from app.crud.checkin import count_today_checkins

    total_students = count_students(session)
    classes = get_all_classes(session)
    today_checkins = count_today_checkins(session)

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {
            'total_students': total_students,
            'total_classes': len(classes),
            'today_checkins': today_checkins
        }
    }


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard_stats(session: Session = Depends(get_session)):
    """
    获取仪表盘统计数据（公开接口，数据脱敏）
    用于首页数据展示，无需登录
    """
    from app.crud import get_students, get_all_classes, count_students
    from app.crud.checkin import get_today_checkins, count_today_checkins
    
    # 使用 COUNT 查询优化性能（避免加载所有对象到内存）
    total_students = count_students(session)
    checked_in = count_today_checkins(session)
    not_checked_in = total_students - checked_in
    checkin_rate = round(checked_in / total_students * 100, 1) if total_students > 0 else 0
    
    # 获取班级列表（数据量小，保持原方式）
    classes = get_all_classes(session)
    
    # 获取分数排行榜（需要完整对象，保持原方式）
    students = get_students(session)
    
    # 分数排行榜（脱敏处理：隐藏姓名和学号，只显示分数和排名）
    score_ranking = []
    if students:
        # 按分数排序，取前10
        sorted_students = sorted(students, key=lambda s: s.score, reverse=True)[:10]
        for rank, student in enumerate(sorted_students, 1):
            score_ranking.append({
                'rank': rank,
                'score': student.score,
                # 姓名脱敏：显示第一位和最后一位，中间用 * 代替
                'name_mask': student.name[0] + '*' + student.name[-1] if len(student.name) >= 2 else (student.name if student.name else '*'),
                # 学号脱敏：只显示后4位
                'student_id_mask': '****' + student.student_id[-4:] if len(student.student_id) >= 4 else '****'
            })
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {
            'total_students': total_students,
            'total_classes': len(classes),
            'today_checkins': checked_in,
            'checked_in': checked_in,
            'not_checked_in': not_checked_in,
            'checkin_rate': checkin_rate,
            'score_ranking': score_ranking
        }
    }
