# ClassHub API 变更日志

---

**文档版本**: v1.1  
**最后更新**: 2026-09-11  
**适用版本**: v3.1.0+  
**当前API版本**: v3.1.0  
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

## v3.1.0 (2026-09-11) — 班级锚点 class_id 化（Phase 6）

> ⚠️ **破坏性变更**：所有以班级为维度的接口参数由 `class_name`（裸班级名）改为 `class_id`（行政班 ID）。

**原因**：`classes` 的唯一约束是 `(name, major, cohort_year)`，裸班名可跨专业/跨届重复（如三个专业都有 `1班`）。按裸名反查必然歧义——实测 `get_class_id_by_name(session, "1班")` 在 3 个同名班中任取其一，导致**跨专业串班与越权**。本版本把班级锚点唯一化为 `class_id`。

### 变更接口（请求参数 class_name → class_id）

| 接口 | 方法 | 变更 |
|------|------|------|
| `/api/v1/students` | GET | query `class_name: str?` → `class_id: int?` |
| `/api/v1/students` | POST | body `class_name: str?` → `class_id: int?` |
| `/api/v1/students/disable-by-class` | POST | body `class_names: str[]` → `class_ids: int[]`（min 1） |
| `/api/v1/course-sessions/class/{class_id}` | GET | **路径参数由班名改为 ID**（`{class_name}` → `{class_id}`） |
| `/api/v1/course-sessions/start` | POST | body `class_name` → `class_id: int` |
| `/api/v1/teacher/groups` | GET | query `class_name` → `class_id: int`（必填） |
| `/api/v1/teacher/groups` | POST | body `class_name` → `class_id: int` |
| `/api/v1/teacher/groups/auto-assign` | POST | body `class_name` → `class_id: int` |
| `/api/v1/teacher/class-group-settings` | GET / PUT | `class_name` → `class_id: int` |
| `/api/v1/teacher/questions` | POST / GET | `class_name` → `class_id: int?`（缺省/`None` = 所有班级） |
| `/api/v1/schedules` | GET | query `class_name` → `class_id: int?` |
| `/api/v1/rankings` | GET | query `class_name` → `class_id: int?` |
| `/api/v1/offerings` | POST | body `class_scope: str` → `class_ids: int[]`（空数组 = 全部班级） |
| `/api/v1/offerings/{offering_id}` | PUT | body `class_scope: str?` → `class_ids: int[]?` |

### 响应变更

| 接口 | 变更 |
|------|------|
| 所有含 `class_name` 的响应 | **键保留，值改为完整班级展示名**：`"1班"` → `"2026届软件工程1班"`（`{届}届{专业}{班名}`）；未分班为 `"未分班"` |
| `GET /students/{student_id}`、`POST /students` | 新增 `class_id: int?` |
| `GET /offerings`、`GET /teacher/offerings` | 新增 `class_ids: int[]`；`class_scope` 键保留为服务端拼装的展示串（无关联班级时 = `"所有班级"`） |

### 数据模型变更

- **删除** `students.class_name` 列（冗余快照；`class_id` 已是真源）
- **删除** `course_offerings.class_scope` 列（自由文本，且为权限真源）
- **新增** `course_offering_classes(offering_id, class_id)` 关联表（复合主键，FK `ondelete=CASCADE`）
- `uix_offering` 唯一约束由 `(course_id, semester_id, teacher_id, class_scope)` 重建为 `(course_id, semester_id, teacher_id)`

### 语义变更

- **教学班面向范围**：offering 在 `course_offering_classes` 无关联行 = **面向全部班级**（通配）。教师权限由该关联表派生；此前由 `class_scope` 按逗号 split 后与裸班名比对，存在静默失效（填 `计科1-2班` 时匹配不到任何班 → 教师零权限）与越权（填 `1班` → 获得所有专业 `1班` 权限）
- **课表 Excel 导入**：`班级` 单列（粘连串如 `2025康复治疗技术1班`，无法拆分）→ `所属届` + `专业` + `班级名` 三列（与学生导入对齐）；导入**不再自动建班**，且要求班级存在且有启用学生
- **`students` 工具函数**：`get_all_classes()` 不再并入学生历史班名（该列已删），只返回 `classes` 表

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
