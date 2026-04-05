# ClassHub 更新日志

---

**文档版本**: v1.0  
**最后更新**: 2026-04-05  
**适用版本**: v3.0.0+  
**状态**: ✅ 已同步代码

---

本文档记录 ClassHub 项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [3.0.0] - 2026-04-05

### 新增

#### 功能
- 仪表盘数据公开接口，支持数据脱敏展示
- 课程表管理功能（创建、查询、导入）
- 审计日志系统，记录所有敏感操作
- Token 刷新机制，提升用户体验
- 活跃课堂索引优化，提升查询性能

#### 文档
- 新增文档地图 (docs/DOCUMENTATION_MAP.md)
- 新增开发者快速开始指南 (GETTING_STARTED.md)
- 新增贡献者指南 (CONTRIBUTING.md)
- 新增项目更新日志 (CHANGELOG.md)
- 新增 API 使用示例 (docs/API_EXAMPLES.md)
- 新增术语表 (docs/GLOSSARY.md)

#### 测试
- 并发登录失败保护测试 (BE-008)
- 并发分数更新保护测试 (BE-008)
- 安全设置校验测试
- CORS 配置验证测试
- 时区统一处理测试
- 数据脱敏验证测试
- Token 刷新机制测试

### 变更

#### API
- 限流状态码从 503 改为 429 (RATE-001)
- 学生分数更新添加乐观锁保护 (BE-008)
- 签到接口添加设备指纹识别
- 统计数据接口添加缓存

#### 安全
- 密码哈希算法升级为 bcrypt (SEC-003)
- JWT Token 时区统一为 Asia/Shanghai (SEC-004)
- HttpOnly Cookie 安全属性增强 (SEC-005)
- 审计日志中间件记录敏感操作 (SEC-006)

### 修复

#### P0 问题
- ScoreLog 重复记录问题
- 学生登录密码验证问题 (SEC-003)

#### P1 问题
- API 响应格式不一致
- test_teacher_can_import 测试失败
- Dialog 内存泄漏问题

### 移除
- 移除 `users` 表的 `salt` 列 (SEC-003)
- 移除 `students` 表的 `salt` 列 (SEC-003)

---

## [2.3.0] - 2026-03-26

### 修复
- 限流状态码从 503 Service Unavailable 改为 429 Too Many Requests (RATE-001)
- JWT Token 过期时间计算使用 Asia/Shanghai 时区 (TIME-001)

### 变更
- 登录失败保护：连续10次登录失败后锁定账号30分钟
- 限流配置支持通过环境变量配置

---

## [2.2.0] - 2026-03-25

### 安全升级 (SEC-003)

#### 变更
| 项目 | 旧实现 | 新实现 |
|------|--------|--------|
| 密码哈希算法 | SHA256 + salt | bcrypt（自动处理盐值） |
| 密码验证接口 | `verify_password_hash(pwd, hash, salt)` | `verify_password(pwd, hash)` |
| 密码生成接口 | `generate_password_hash(pwd)` | `hash_password(pwd)` |

#### 数据库变更
- 移除 `users` 表的 `salt` 列
- 移除 `students` 表的 `salt` 列

---

## [2.1.0] - 2026-03-20

### 新增
- 学生自助查询接口
- 重置学生密码接口
- 班级列表接口
- 乐观锁保护机制 (BE-008)
- 领域事件架构 (events.py + handlers.py)

---

## [2.0.0] - 2026-03-15

### 架构升级
- API 版本化：所有接口添加 `/api/v1` 前缀
- 统一响应格式：标准响应 `{success, data, message}`
- 常量规范化：API 响应字段使用 `ApiResponseConst` 常量

### 新增接口
- 健康检查 `/api/v1/health`
- 系统统计 `/api/v1/stats`
- 分数日志 `/api/v1/score/logs`
- 课堂会话管理 `/api/v1/class-session/*`

---

## [1.5.0] - 2026-03-10

### 新增
- 教师代签功能
- 签到记录查询
- 今日签到列表
- 签到统计

---

## [1.0.0] - 2026-03-01

### 初始版本发布

#### 认证模块
- 用户登录/登出
- JWT + HttpOnly Cookie 认证
- 密码修改
- RBAC 角色权限

#### 学生管理
- 学生增删改查
- 分数管理
- Excel 批量导入

#### 签到系统
- 网页签到
- 一机一签限制
- 实时签到状态

#### 用户管理
- 用户列表
- 创建/更新/删除用户
- 重置密码

---

## 版本兼容性

| 版本 | 状态 | 支持截止日期 |
|------|------|--------------|
| v3.0.x | ✅ 当前版本 | - |
| v2.3.x | ⚠️ 维护模式 | 2026-06-30 |
| v2.2.x | ❌ 已停止支持 | - |
| v2.1.x | ❌ 已停止支持 | - |
| v2.0.x | ❌ 已停止支持 | - |
| v1.x.x | ❌ 已停止支持 | - |

---

## 迁移指南

### 从 v2.x 迁移到 v3.0

#### 密码验证更新
```python
# 旧代码
from app.core.security import verify_password_hash
is_valid = verify_password_hash(password, stored_hash, salt)

# 新代码
from app.core.security import verify_password
is_valid = verify_password(password, stored_hash)
```

#### API 响应处理更新
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

#### JWT 时区更新
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

## 统计数据

### 测试统计

| 版本 | 后端测试 | 前端测试 | 覆盖率 |
|------|----------|----------|--------|
| v3.0.0 | 467 | 130 | 89% |
| v2.3.0 | 420 | 120 | 85% |
| v2.2.0 | 380 | 100 | 82% |
| v2.1.0 | 350 | 90 | 80% |
| v2.0.0 | 300 | 80 | 75% |
| v1.5.0 | 250 | 60 | 70% |
| v1.0.0 | 200 | 40 | 65% |

### 代码统计

| 版本 | 后端代码行数 | 前端代码行数 | 文档数 |
|------|--------------|--------------|--------|
| v3.0.0 | ~15,000 | ~20,000 | 20+ |
| v2.0.0 | ~10,000 | ~15,000 | 10+ |
| v1.0.0 | ~5,000 | ~8,000 | 5 |

---

## 相关文档

- [API 变更日志](./docs/API_CHANGELOG.md) - 详细的 API 变更记录
- [弃用说明](./docs/DEPRECATIONS.md) - 弃用功能和迁移指南
- [优化方案](./docs/OPTIMIZATION_PLAN.md) - 架构优化路线图
- [需求规格](./docs/REQUIREMENTS.md) - 功能需求规划

---

## 贡献者

感谢所有为 ClassHub 做出贡献的开发者！

---

**文档版本**: v1.0  
**最后更新**: 2026-04-05
