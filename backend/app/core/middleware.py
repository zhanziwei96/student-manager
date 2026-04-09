"""
审计日志中间件 - 自动记录敏感操作（异步优化）

修复内容：使用 asyncio.create_task 将审计日志写入改为后台任务，
避免阻塞主请求响应，提升高并发性能。

SEC-006: 添加任务队列管理，防止高并发下堆积过多后台任务
"""
import asyncio
import re
from typing import List, Optional, Dict, Any, Set
from concurrent.futures import ThreadPoolExecutor
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# 任务队列管理 - 限制最大并发任务数
MAX_CONCURRENT_AUDIT_TASKS = 50  # 最大并发审计任务数
MAX_PENDING_AUDIT_TASKS = 100   # 最大 pending 审计任务数，防止内存泄漏
_audit_task_semaphore = asyncio.Semaphore(MAX_CONCURRENT_AUDIT_TASKS)
_pending_audit_tasks: set[asyncio.Task] = set()

# 使用线程池处理数据库操作，避免阻塞事件循环
_audit_executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="audit_log_")


def shutdown_audit_executor():
    """
    关闭审计日志线程池
    在应用关闭时调用，确保线程资源正确释放
    """
    global _audit_executor
    if _audit_executor:
        _audit_executor.shutdown(wait=True)
        _audit_executor = None


async def _save_audit_log_with_timeout(audit_data: Dict[str, Any]) -> None:
    """
    保存审计日志（带超时保护）

    包装 _save_audit_log_async，添加 10 秒超时机制，防止数据库连接
    卡住导致任务长时间占用内存。

    Args:
        audit_data: 审计日志数据字典
    """
    try:
        await asyncio.wait_for(
            _save_audit_log_async(audit_data),
            timeout=10.0  # 10秒总超时（包含内部5秒超时）
        )
    except asyncio.TimeoutError:
        import logging
        logging.getLogger(__name__).warning("审计日志任务超时（10秒），已取消并释放资源")


async def _save_audit_log_async(audit_data: Dict[str, Any]) -> None:
    """
    异步保存审计日志（后台任务）- 性能优化

    使用独立的会话和异常处理，确保失败不影响主业务。
    通过 asyncio.create_task 在后台执行，不阻塞主请求响应。

    SEC-006 改进：
    - 添加信号量限制并发任务数，防止高并发下堆积过多任务
    - 使用线程池处理数据库操作，避免阻塞事件循环
    - 添加任务超时处理（5秒）

    Args:
        audit_data: 审计日志数据字典
    """
    # 使用信号量限制并发任务数
    async with _audit_task_semaphore:
        try:
            # 在线程池中执行数据库操作，避免阻塞事件循环
            loop = asyncio.get_event_loop()
            await asyncio.wait_for(
                loop.run_in_executor(_audit_executor, _save_audit_log_sync, audit_data),
                timeout=5.0  # 5秒超时
            )
        except asyncio.TimeoutError:
            import logging
            logging.getLogger(__name__).warning("审计日志写入超时（5秒），任务已放弃")
        except Exception as e:
            # 审计日志失败不应影响主业务，仅记录错误
            import logging
            logging.getLogger(__name__).error(f"审计日志异步写入失败: {e}")


def _save_audit_log_sync(audit_data: Dict[str, Any]) -> None:
    """
    同步保存审计日志（在线程池中执行）

    Args:
        audit_data: 审计日志数据字典
    """
    try:
        from app.core.db import engine
        from sqlmodel import Session
        from app.models import AuditLog

        with Session(engine) as session:
            audit_log = AuditLog(**audit_data)
            session.add(audit_log)
            session.commit()
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"审计日志同步写入失败: {e}")
        raise  # 重新抛出以便上层捕获


class AuditLogMiddleware(BaseHTTPMiddleware):
    """
    审计日志中间件
    
    自动记录配置的敏感操作到 audit_logs 表
    """
    
    # 需要记录审计日志的路径和方法
    # 支持 {id} 或 {student_id} 等路径参数占位符
    AUDIT_ROUTES = {
        "POST": [
            "/api/v1/login",
            "/api/v1/change-password",
            "/api/v1/students",
        ],
        "PUT": [
            "/api/v1/students/{id}/score",
            "/api/v1/students/{id}/reset-password",
            "/api/v1/users/{id}",
            "/api/v1/users/{id}/reset-password",
        ],
        "DELETE": [
            "/api/v1/students/{id}",
            "/api/v1/users/{id}",
        ],
    }

    def __init__(self, app: ASGIApp, exclude_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/api/v1/health", "/docs", "/openapi.json"]
    
    async def dispatch(self, request: Request, call_next):
        # 判断是否需要记录审计
        if not self._should_audit(request):
            return await call_next(request)
        
        # 记录请求信息
        audit_data = await self._capture_request(request)
        
        # 执行请求
        response = await call_next(request)
        
        # 记录响应并保存审计日志
        await self._save_audit_log(request, audit_data, response)
        
        return response
    
    def _should_audit(self, request: Request) -> bool:
        """判断是否需要记录审计日志"""
        method = request.method
        path = request.url.path
        
        # 检查是否在排除列表
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return False
        
        # 检查是否匹配的审计路由
        audit_paths = self.AUDIT_ROUTES.get(method, [])
        for audit_path in audit_paths:
            # 将 {id} 或 {student_id} 等转换为正则表达式
            pattern = re.sub(r'\{[^/]+\}', r'[^/]+', audit_path)
            if re.match(f"^{pattern}$", path):
                return True
        
        return False
    
    async def _capture_request(self, request: Request) -> Dict[str, Any]:
        """捕获请求信息"""
        # 尝试从 cookie 中解析 JWT token 获取用户信息
        user = self._get_user_from_request(request)
        
        return {
            "user_id": user.get("sub") if user else None,
            "user_name": user.get("username") if user else None,
            "role": user.get("role") if user else None,
            "method": request.method,
            "path": request.url.path,
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }
    
    def _get_user_from_request(self, request: Request) -> Optional[Dict[str, Any]]:
        """从请求中获取用户信息"""
        try:
            # 尝试从 state 获取（如果使用了依赖注入设置）
            user = getattr(request.state, 'user', None)
            if user:
                return user
            
            # 尝试从 cookie 解析 JWT
            from app.core.jwt import get_token_from_cookie, decode_token
            token = get_token_from_cookie(request)
            if token:
                payload = decode_token(token)
                if payload:
                    return payload
        except Exception:
            pass
        return None
    
    async def _save_audit_log(self, request: Request, audit_data: Dict[str, Any], response):
        """
        保存审计日志（异步优化）
        
        将数据库写入改为后台任务，使用 asyncio.create_task 不阻塞主请求。
        这样可以显著降低高并发场景下的请求延迟。
        
        Args:
            request: FastAPI请求对象
            audit_data: 基础审计数据（用户、方法、路径等）
            response: 响应对象
        """
        from app.core.timezone import get_now

        audit_data.update({
            "action": self._get_action_name(audit_data["method"], audit_data["path"]),
            "resource": self._get_resource_name(audit_data["path"]),
            "resource_id": self._extract_resource_id(audit_data["path"]),
            "status_code": response.status_code,
            "response_msg": "成功" if response.status_code < 400 else "失败",
            "created_at": get_now(),
        })

        # SEC-006: 创建后台任务异步写入，添加错误处理和队列管理
        # 限制 pending 任务总数，防止高并发下 create_task 无限堆积导致内存泄漏
        if len(_pending_audit_tasks) >= MAX_PENDING_AUDIT_TASKS:
            import logging
            logging.getLogger(__name__).warning(
                f"审计日志 pending 任务数已达上限 ({MAX_PENDING_AUDIT_TASKS})，丢弃当前审计日志以防止内存泄漏"
            )
            return

        # SEC-006: 创建后台任务异步写入，添加超时保护防止任务无限运行
        task = asyncio.create_task(
            _save_audit_log_with_timeout(audit_data)
        )
        _pending_audit_tasks.add(task)

        # 添加任务完成回调，捕获异常防止未处理异常警告
        def _on_task_done(t: asyncio.Task) -> None:
            _pending_audit_tasks.discard(t)
            try:
                t.result()  # 这会抛出任务中的异常（如果有）
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"审计日志任务执行失败: {e}")

        task.add_done_callback(_on_task_done)
    
    def _get_action_name(self, method: str, path: str) -> str:
        """获取操作名称"""
        action_map = {
            "POST": "创建",
            "PUT": "更新",
            "DELETE": "删除",
        }
        
        # 特殊路径处理
        if "/score" in path and method == "PUT":
            return "修改分数"
        if "/reset-password" in path and method == "PUT":
            return "重置密码"
        if "/login" in path and method == "POST":
            return "登录"
        if "/change-password" in path and method == "POST":
            return "修改密码"
            
        return action_map.get(method, method)
    
    def _get_resource_name(self, path: str) -> str:
        """获取资源名称"""
        if "/students/" in path or path == "/api/v1/students":
            return "学生"
        elif "/users/" in path or path == "/api/v1/users":
            return "用户"
        elif "/login" in path:
            return "系统"
        return "系统"
    
    def _extract_resource_id(self, path: str) -> Optional[str]:
        """从路径中提取资源ID"""
        # 尝试提取 /path/{id} 中的 id
        parts = path.strip("/").split("/")
        if len(parts) >= 3:
            # 如 /api/students/123/score -> 123
            potential_id = parts[-2] if parts[-1] in ["score", "reset-password"] else parts[-1]
            # 验证是否是数字ID
            if potential_id.isdigit():
                return potential_id
        return None
