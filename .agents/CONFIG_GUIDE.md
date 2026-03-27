# 配置管理指南

> **最后更新时间**: 2026-03-27

## 概述

本系统使用 Pydantic Settings 管理配置，支持环境变量、`.env` 文件和代码默认值三种配置来源。

## 配置架构

### 1. 配置分类

配置按功能分为以下几类：

| 配置类 | 说明 | 环境变量前缀 | 访问方式 |
|--------|------|-------------|---------|
| `AppSettings` | 应用基础配置 | - | `settings.app.*` |
| `DatabaseSettings` | 数据库配置 | `DATABASE_` | `settings.database.*` |
| `SecuritySettings` | 安全配置 | `SECURITY_` | `settings.security.*` |
| `JWTSettings` | JWT 认证配置 | `JWT_` | `settings.jwt.*` |
| `ScoreSettings` | 分数配置 | `SCORE_` | `settings.score.*` |
| `PaginationSettings` | 分页配置 | `PAGINATION_` | `settings.pagination.*` |
| `RateLimitSettings` | 限流配置 | `RATE_LIMIT_` | `settings.rate_limit.*` |

### 2. 配置优先级

配置优先级从高到低：

1. 环境变量（如 `export DATABASE__PATH=/path/to/db`）
2. `.env` 文件中的变量
3. 代码中的默认值

**注意**：使用双下划线 `__` 访问嵌套配置，如 `DATABASE__PATH` 对应 `settings.database.path`

## 使用方法

### 基本用法

```python
from app.core.config import get_settings

settings = get_settings()

# 访问配置
db_path = settings.get_database_path()
secret_key = settings.security.secret_key
min_score = settings.score.min_score
```

### 重新加载配置

```python
from app.core.config import get_settings

# 配置热更新（实际会重新读取环境变量）
settings = get_settings()
```

### 指定环境文件

系统根据 `ENV` 环境变量自动选择配置文件：

```bash
# 开发环境
ENV=development python main.py

# 测试环境
ENV=testing python main.py

# 生产环境（默认）
ENV=production python main.py
```

## 环境变量

### 常用配置项

```bash
# 应用配置
ENV=production                    # 运行环境
APP__NAME=ClassHub                # 应用名称
APP__DEBUG=false                  # 调试模式
APP__HOST=0.0.0.0                 # 服务器地址
APP__PORT=8000                    # 服务器端口

# 数据库配置
DATABASE__PATH=./data/class_system.db  # 数据库文件路径

# 安全配置
SECURITY__SECRET_KEY=your-secret      # JWT 密钥
SECURITY__MAX_LOGIN_FAILURES=10       # 最大登录失败次数
SECURITY__LOCKOUT_DURATION_MINUTES=30 # 账号锁定时间
SECURITY__CORS_ORIGINS=["http://localhost:5173"]  # CORS 来源

# JWT 配置
JWT__ACCESS_TOKEN_EXPIRE_MINUTES=1440 # JWT 有效期（分钟，默认24小时）
JWT__ALGORITHM=HS256                  # JWT 算法
JWT__COOKIE_NAME=access_token         # Cookie 名称

# 分数配置
SCORE__MIN_SCORE=0                # 最低分数
SCORE__MAX_SCORE=100              # 最高分数
SCORE__DEFAULT_SCORE=70           # 默认分数

# 分页配置
PAGINATION__DEFAULT_PAGE_SIZE=20         # 默认每页数量
PAGINATION__SCORE_LOG_DEFAULT_LIMIT=50   # 分数日志默认条数

# 限流配置（内存存储，无需Redis）
RATE_LIMIT__ENABLED=true              # 是否启用限流
RATE_LIMIT__LOGIN_MAX_REQUESTS=5      # 登录接口每分钟最大请求数
RATE_LIMIT__CHECKIN_MAX_REQUESTS=10   # 签到接口每分钟最大请求数
RATE_LIMIT__SCORE_MAX_REQUESTS=10     # 分数接口每分钟最大请求数
```

### 最新环境变量（2026-03-27）

新增配置项：

```bash
# 审计日志配置
AUDIT__ENABLED=true                   # 是否启用审计日志
AUDIT__ASYNC_WRITE=false              # 是否异步写入（默认同步）
AUDIT__BATCH_SIZE=100                 # 批量写入大小（异步模式）

# 领域事件配置
EVENTS__ENABLED=true                  # 是否启用领域事件
EVENTS__SCORE_LOG_VIA_EVENTS=true     # 通过事件处理器记录分数日志
```

## 多环境配置

### 环境文件

创建多个环境文件：

- `.env.development` - 开发环境
- `.env.testing` - 测试环境
- `.env.production` - 生产环境

### 环境文件示例

```bash
# .env.production
ENV=production
SECURITY__SECRET_KEY=your-production-secret-key-min-32-chars-long
DATABASE__PATH=./data/class_system.db
JWT__ACCESS_TOKEN_EXPIRE_MINUTES=1440
RATE_LIMIT__ENABLED=true
```

### 多环境配置最佳实践

```bash
# 开发环境（热重载+详细日志）
ENV=development uvicorn main:app --reload --log-level debug

# 测试环境（内存数据库）
ENV=testing pytest tests/ -v

# 生产环境（性能优先）
ENV=production python main.py
```

## 兼容性常量

系统提供常量类用于业务逻辑：

```python
from app.models.constants import (
    UserRoleConst,      # 用户角色: ADMIN, TEACHER, STUDENT
    ApiResponseConst,   # API响应键: SUCCESS, DATA, MESSAGE
    RoutePrefixConst,   # 路由前缀: API, ADMIN
    MessageConst,       # 业务消息
)

# 使用常量
role = UserRoleConst.ADMIN
```

**注意**: 旧版 `SessionKeyConst` 已弃用，JWT 认证使用 claims（sub, username, role, is_admin）

HTTP 状态码常量：

```python
from app.core.config import HttpStatus

HttpStatus.OK           # 200
HttpStatus.BAD_REQUEST  # 400
HttpStatus.UNAUTHORIZED # 401
HttpStatus.FORBIDDEN    # 403
HttpStatus.NOT_FOUND    # 404
HttpStatus.CONFLICT     # 409
```

## 最佳实践

### 1. 敏感信息

敏感信息（如密钥、密码）应通过环境变量传递，不要提交到代码仓库：

```bash
# 生产环境
export SECURITY__SECRET_KEY=$(openssl rand -hex 32)
```

### 2. 配置验证

系统使用 Pydantic 自动验证配置：

```bash
# 无效的配置会抛出异常
SCORE__MIN_SCORE=invalid  # 错误：必须是数值
```

### 3. 配置文档

为自定义配置添加注释：

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class MyFeatureSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MY_FEATURE_")
    
    enabled: bool = Field(default=True, description="功能开关")
    timeout: int = Field(default=30, description="超时时间（秒）")

# 在 Settings 类中添加
class Settings(BaseSettings):
    # ... 其他配置
    my_feature: MyFeatureSettings = Field(default_factory=MyFeatureSettings)
```

## 故障排查

### 配置不生效

1. 检查环境变量是否正确设置
2. 检查 `.env` 文件是否存在且格式正确
3. 检查配置项名称是否正确（区分大小写）
4. 检查是否使用了双下划线 `__` 访问嵌套配置

### 配置验证失败

查看错误信息，确保配置值类型正确：

```bash
# 正确
SCORE__MIN_SCORE=0

# 错误
SCORE__MIN_SCORE=zero
```

### 调试配置

打印所有配置（注意不要暴露敏感信息）：

```python
from app.core.config import get_settings

settings = get_settings()
print(settings.model_dump())  # 打印所有配置
```

### 检查当前环境

```python
from app.core.config import get_settings

settings = get_settings()
print(f"当前环境: {settings.app.env}")
print(f"是否开发环境: {settings.app.is_development}")
print(f"是否生产环境: {settings.app.is_production}")
```

## 相关文件

- `backend/app/core/config.py` - 配置实现
- `backend/.env.example` - 配置示例（如存在）
- `backend/.env.production` - 生产环境配置
- `backend/.env.testing` - 测试环境配置

---

**文档版本**: v2.0  
**最后更新**: 2026-03-27（新增审计日志和领域事件配置）
