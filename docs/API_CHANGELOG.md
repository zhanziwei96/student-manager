# ClassHub API 变更日志

---

**文档版本**: v1.0  
**最后更新**: 2026-04-03  
**适用版本**: v3.0.0+  
**当前API版本**: v3.0.0  
**API前缀**: `/api/v1`  
**状态**: ✅ 已同步代码

---

---

## 版本说明

本文档记录 ClassHub API 的所有变更，包括：
- 新增接口
- 变更接口
- 弃用接口
- 移除接口

---

## v3.0.0 (2026-03-27)

### 新增接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 仪表盘数据 | GET | `/api/v1/dashboard` | 公开仪表盘统计数据（数据脱敏） |
| 课程表管理 | GET | `/api/v1/schedules` | 获取课程表列表 |
| 课程表管理 | POST | `/api/v1/schedules` | 创建课程（管理员） |
| 课程表管理 | POST | `/api/v1/schedules/import` | 批量导入课程表 |
| 审计日志 | GET | `/api/v1/audit/logs` | 获取审计日志（管理员） |
| Token 刷新 | POST | `/api/v1/refresh-token` | 刷新 JWT Token |

### 变更接口

| 接口 | 变更内容 |
|------|----------|
| `POST /api/v1/login` | 限流状态码 503 → 429 |
| `PUT /api/v1/students/{id}/score` | 添加乐观锁保护（BE-008），防止并发更新数据丢失 |
| `POST /api/v1/checkin` | 添加设备指纹识别，支持一机一签限制 |
| `GET /api/v1/stats` | 响应数据添加缓存，提升性能 |

### 安全更新

| 更新 | 说明 |
|------|------|
| SEC-003 | 密码哈希算法升级为 bcrypt（自动处理盐值） |
| SEC-004 | JWT Token 时区统一为 Asia/Shanghai |
| SEC-005 | HttpOnly Cookie 安全属性增强 |
| SEC-006 | 审计日志中间件记录所有敏感操作 |

---

## v2.3.0 (2026-03-26)

### 修复

| 问题ID | 说明 |
|--------|------|
| RATE-001 | 限流状态码从 503 Service Unavailable 改为 429 Too Many Requests |
| TIME-001 | JWT Token 过期时间计算使用 Asia/Shanghai 时区 |

### 变更

- **登录失败保护**: 连续10次登录失败后锁定账号30分钟
- **限流配置**: 支持通过环境变量配置限流参数

---

## v2.2.0 (2026-03-25)

### 安全升级 (SEC-003)

| 变更 | 旧实现 | 新实现 |
|------|--------|--------|
| 密码哈希算法 | SHA256 + salt | bcrypt（自动处理盐值） |
| 密码验证接口 | `verify_password_hash(pwd, hash, salt)` | `verify_password(pwd, hash)` |
| 密码生成接口 | `generate_password_hash(pwd)` → 返回 (hash, salt) | `hash_password(pwd)` → 返回 hash |

### 数据库变更

- 移除 `users` 表的 `salt` 列
- 移除 `students` 表的 `salt` 列

**迁移脚本**: `migrations/remove_salt_field.sql`

---

## v2.1.0 (2026-03-20)

### 新增接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 学生自助查询 | POST | `/api/v1/student/query` | 学生查询自己的分数和排名 |
| 重置学生密码 | PUT | `/api/v1/students/{id}/reset-password` | 管理员重置学生密码 |
| 班级列表 | GET | `/api/v1/classes` | 获取班级列表 |

### 新增功能

- **乐观锁保护**: 学生分数更新添加版本号控制（BE-008）
- **领域事件**: 引入事件驱动架构，`events.py` + `handlers.py`
- **并发保护**: 防止并发更新导致的数据丢失

---

## v2.0.0 (2026-03-15)

### 架构升级

- **API 版本化**: 所有接口添加 `/api/v1` 前缀
- **统一响应格式**: 标准响应 `{success, data, message}`
- **常量规范化**: API 响应字段使用 `ApiResponseConst` 常量

### 新增接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 健康检查 | GET | `/api/v1/health` | 系统健康状态检查 |
| 系统统计 | GET | `/api/v1/stats` | 首页统计数据 |
| 分数日志 | GET | `/api/v1/score/logs` | 分数变更历史 |
| 课堂会话 | GET | `/api/v1/class-session` | 获取当前课堂状态 |
| 课堂会话 | POST | `/api/v1/class-session/start` | 开始课堂 |
| 课堂会话 | POST | `/api/v1/class-session/end` | 结束课堂 |

---

## v1.5.0 (2026-03-10)

### 新增接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 教师代签 | POST | `/api/v1/teacher-checkin` | 教师帮学生代签到 |
| 签到记录 | GET | `/api/v1/checkin/records` | 查询签到记录 |
| 今日签到 | GET | `/api/v1/checkins/today` | 获取今日签到列表 |
| 签到统计 | GET | `/api/v1/checkins/stats` | 签到统计数据 |

---

## v1.0.0 (2026-03-01)

### 初始版本

#### 认证接口

| 接口 | 方法 | 路径 |
|------|------|------|
| 登录 | POST | `/api/v1/login` |
| 登出 | POST | `/api/v1/logout` |
| 当前用户 | GET | `/api/v1/me` |
| 修改密码 | POST | `/api/v1/change-password` |

#### 学生管理接口

| 接口 | 方法 | 路径 |
|------|------|------|
| 学生列表 | GET | `/api/v1/students` |
| 添加学生 | POST | `/api/v1/students` |
| 删除学生 | DELETE | `/api/v1/students/{id}` |
| 更新分数 | PUT | `/api/v1/students/{id}/score` |
| 导入学生 | POST | `/api/v1/students/import` |

#### 签到接口

| 接口 | 方法 | 路径 |
|------|------|------|
| 学生签到 | POST | `/api/v1/checkin` |

#### 用户管理接口（管理员）

| 接口 | 方法 | 路径 |
|------|------|------|
| 用户列表 | GET | `/api/v1/admin/users` |
| 创建用户 | POST | `/api/v1/admin/users` |
| 更新用户 | PUT | `/api/v1/admin/users/{id}` |
| 重置密码 | PUT | `/api/v1/admin/users/{id}/reset-password` |
| 删除用户 | DELETE | `/api/v1/admin/users/{id}` |

---

## 已弃用接口

| 接口 | 弃用版本 | 替代接口 | 计划移除 |
|------|----------|----------|----------|
| `POST /api/login` | v2.0.0 | `POST /api/v1/login` | v3.1.0 |
| `GET /api/students` | v2.0.0 | `GET /api/v1/students` | v3.1.0 |

---

## 迁移指南

### 从 v2.x 迁移到 v3.0

**密码验证更新**:
```python
# 旧代码
from app.core.security import verify_password_hash
is_valid = verify_password_hash(password, stored_hash, salt)

# 新代码
from app.core.security import verify_password
is_valid = verify_password(password, stored_hash)
```

**API 响应处理更新**:
```python
# 旧代码
return {"success": True, "message": "创建成功"}

# 新代码
from app.models.constants import ApiResponseConst, MessageConst
return {
    ApiResponseConst.SUCCESS: True,
    ApiResponseConst.MESSAGE: MessageConst.USER_CREATED
}
```

**JWT 时区更新**:
```python
# 旧代码
from datetime import datetime, timedelta
expire = datetime.utcnow() + timedelta(hours=24)

# 新代码
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
expire = datetime.now(ZoneInfo("Asia/Shanghai")) + timedelta(hours=24)
```

---

## 兼容性说明

| 版本 | 状态 | 支持截止日期 |
|------|------|--------------|
| v3.0.x | ✅ 当前版本 | - |
| v2.3.x | ⚠️ 维护模式 | 2026-06-30 |
| v2.2.x | ❌ 已停止支持 | - |
| v2.1.x | ❌ 已停止支持 | - |
| v2.0.x | ❌ 已停止支持 | - |
| v1.x.x | ❌ 已停止支持 | - |

---

## 相关文档

- [弃用说明](./DEPRECATIONS.md) - 详细的接口弃用和迁移指南
- [后端架构](../backend/README.md) - API 设计规范
- [需求规格](./REQUIREMENTS.md) - 功能需求说明

---

**文档版本**: v1.0
**最后更新**: 2026-04-03
