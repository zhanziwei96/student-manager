"""
领域层类型定义
提供项目中使用的类型别名和类型变量
"""
from typing import TypeVar, Dict, Any, Optional, List, Union
from datetime import datetime

# 实体 ID 类型
EntityId = Union[int, str]

# 学生 ID 类型
StudentId = str

# 用户 ID 类型
UserId = int

# 分数类型
ScoreValue = float

# 班级名称类型
ClassName = str

# 查询参数类型
QueryParams = Dict[str, Any]

# 服务返回类型（成功标志, 消息, 数据）
ServiceResult = tuple[bool, str, Optional[Any]]

# 泛型类型变量
T = TypeVar('T')
EntityType = TypeVar('EntityType')

# API 响应类型
ApiResponse = Dict[str, Any]

# 审计日志动作类型
AuditAction = str

# 审计日志资源类型
AuditResource = str

# 缓存键类型
CacheKey = str

# HTTP 方法类型
HttpMethod = str
