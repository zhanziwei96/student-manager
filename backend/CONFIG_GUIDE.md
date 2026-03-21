# 配置管理指南

## 概述

本系统采用分层配置管理架构，支持环境变量、`.env` 文件和代码默认值三种配置来源。

## 配置架构

### 1. 配置分类

配置按功能分为以下几类：

| 配置类 | 说明 | 环境变量前缀 |
|--------|------|-------------|
| `AppSettings` | 应用基础配置 | - |
| `DatabaseSettings` | 数据库配置 | `DB_` |
| `RedisSettings` | Redis 配置 | `REDIS_` |
| `CacheSettings` | 缓存配置 | `CACHE_` |
| `SecuritySettings` | 安全配置 | `SECURITY_` |
| `RateLimitSettings` | 限流配置 | `RATE_LIMIT_` |
| `LogSettings` | 日志配置 | `LOG_` |
| `PaginationSettings` | 分页配置 | `PAGINATION_` |
| `ScoreSettings` | 分数配置 | `SCORE_` |

### 2. 配置优先级

配置优先级从高到低：

1. 环境变量（如 `export REDIS_URL=redis://...`）
2. `.env` 文件中的变量
3. 代码中的默认值

## 使用方法

### 基本用法

```python
from infrastructure.config import get_settings

settings = get_settings()

# 访问配置
redis_url = settings.redis.url
db_path = settings.database.path
secret_key = settings.security.secret_key
```

### 便捷访问函数

```python
from infrastructure.config import (
    get_db_settings,
    get_redis_settings,
    get_cache_settings,
    get_security_settings,
)

db_config = get_db_settings()
redis_config = get_redis_settings()
```

### 重新加载配置

```python
from infrastructure.config import reload_settings

# 配置热更新
settings = reload_settings()
```

### 指定环境文件

```python
from infrastructure.config import init_settings

# 使用特定的环境文件
settings = init_settings("/path/to/.env.production")
```

## 环境变量

### 常用配置项

```bash
# 应用配置
ENV=production                    # 运行环境
DEBUG=false                       # 调试模式
HOST=0.0.0.0                      # 服务器地址
PORT=8000                         # 服务器端口

# 数据库配置
DB_PATH=/data/class_system.db     # 数据库文件路径
DB_TIMEOUT=30                     # 连接超时

# Redis 配置
REDIS_URL=redis://localhost:6379  # Redis 连接 URL
REDIS_POOL_SIZE=10                # 连接池大小

# 安全配置
SECURITY_SECRET_KEY=your-secret   # Session 密钥
SECURITY_SESSION_MAX_AGE=86400    # Session 有效期（秒）

# 缓存配置
CACHE_ENABLED=true                # 是否启用缓存
CACHE_TTL=60                      # 默认 TTL（秒）
```

### 完整配置项

参考 `.env.example` 文件获取所有可配置项。

## 配置文件

### .env 文件

在项目根目录创建 `.env` 文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件修改配置：

```bash
# 修改密钥
SECURITY_SECRET_KEY=my-secure-secret-key

# 修改 Redis 地址
REDIS_URL=redis://192.168.1.100:6379
```

### 多环境配置

可以创建多个环境文件：

- `.env.development` - 开发环境
- `.env.testing` - 测试环境
- `.env.production` - 生产环境

通过环境变量指定使用的配置文件：

```bash
ENV=production python main.py
```

## 配置常量（兼容旧代码）

为了保持兼容性，系统同时提供配置常量类：

```python
from infrastructure.config import (
    AppConfig,
    AuthConfig,
    ScoreConfig,
    CacheConfig,
    HttpStatus,
)

# 使用常量
version = AppConfig.VERSION
default_score = ScoreConfig.DEFAULT_SCORE
```

**注意**：新代码建议使用 `get_settings()` 获取配置。

## 最佳实践

### 1. 敏感信息

敏感信息（如密钥、密码）应通过环境变量传递，不要提交到代码仓库：

```bash
# 生产环境
export SECURITY_SECRET_KEY=$(openssl rand -hex 32)
```

### 2. 不同环境配置

开发环境可以使用 `.env` 文件，生产环境使用环境变量：

```dockerfile
# Dockerfile
ENV ENV=production
ENV SECURITY_SECRET_KEY=${SECRET_KEY}
```

### 3. 配置验证

系统使用 Pydantic 自动验证配置：

```python
# 无效的配置会抛出异常
CACHE_TTL=invalid  # 错误：必须是整数
```

### 4. 配置文档

为自定义配置添加注释：

```python
from pydantic import Field

class MySettings(BaseSettings):
    my_config: str = Field(
        default="default_value",
        description="配置项说明"
    )
```

## 故障排查

### 配置不生效

1. 检查环境变量是否正确设置
2. 检查 `.env` 文件是否存在且格式正确
3. 检查配置项名称是否正确（区分大小写）

### 配置验证失败

查看错误信息，确保配置值类型正确：

```bash
# 正确
CACHE_TTL=60

# 错误
CACHE_TTL=sixty
```

### 调试配置

打印所有配置（注意不要暴露敏感信息）：

```python
from infrastructure.config import get_settings

settings = get_settings()
print(settings.model_dump())  # 打印所有配置
```

## 迁移指南

### 从旧配置迁移

旧代码：
```python
from infrastructure.config import CacheConfig

ttl = CacheConfig.STUDENT_LIST_TTL_SECONDS
```

新代码：
```python
from infrastructure.config import get_settings

settings = get_settings()
ttl = settings.cache.student_list_ttl
```

### 自定义配置

在 `infrastructure/config/settings.py` 中添加新的配置类：

```python
class MyFeatureSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MY_FEATURE_")
    
    enabled: bool = Field(default=True)
    timeout: int = Field(default=30)

class AppSettings(BaseSettings):
    # ... 其他配置
    my_feature: MyFeatureSettings = Field(default_factory=MyFeatureSettings)
```

使用：
```python
settings = get_settings()
if settings.my_feature.enabled:
    timeout = settings.my_feature.timeout
```
