# 项目待修复问题清单

> 生成时间: 2026-04-12
> 状态: 基于代码审查结果整理，按优先级排序

---

## P0 级别（关键）

### P0-2 JWT 安全机制
- **状态**: 已确认，用户要求暂缓修复
- **问题描述**:
  - `SECURITY_SECRET_KEY` 在部分环境文件中仍为默认值 `dev-secret-key-change-in-production`
  - JWT Token 缺少主动刷新/吊销机制
  - Token 有效期较长，一旦被截取无法快速作废
- **影响**: 认证安全基线不达标，存在水平越权风险
- **建议修复**:
  - 生产环境强制校验密钥长度和随机性
  - 引入 Refresh Token 机制或 Token 黑名单
  - 缩短 Access Token 有效期
- **相关文件**:
  - `backend/app/core/config.py`
  - `backend/.env.production`
  - `backend/app/core/jwt.py`

---

## P1 级别（高优）

### P1-3 后端 API 响应格式仍有混用
- **状态**: 大部分已修复，个别残留
- **问题描述**:
  - 虽然有 `ApiResponseConst` 和 `MessageConst` 强制规范，但部分老旧接口或边缘接口仍混用硬编码字段名
  - 少数接口返回的数据嵌套层次与其他接口不一致
- **影响**: 前端需要额外兼容逻辑，增加维护成本
- **建议修复**: 全量扫描 `backend/app/api/routes/` 下所有 `return {` 语句，统一使用常量
- **相关文件**:
  - `backend/app/api/routes/` 下所有路由文件

### P1-4 签到列表查询缺少分页/限制
- **状态**: 未修复
- **问题描述**:
  - `get_all_checkins`、`get_today_checkins` 虽然有 `limit` 参数但在多处调用时未传值
  - 教师端和 Admin 端查看签到记录时，学期末可能一次性返回数千条记录
- **影响**: 前端渲染卡顿，后端内存和带宽压力增加
- **建议修复**:
  - 为所有列表查询接口设置合理的默认 `limit`（如 100 或 200）
  - 教师端页面增加分页组件（服务端分页）
- **相关文件**:
  - `backend/app/crud/checkin.py`
  - `backend/app/api/routes/checkin.py`
  - `frontend-v3/src/views/teacher/CheckinManagement.vue`（如存在）

### P1-5 数据库索引缺失影响查询性能
- **状态**: 已修复
- **问题描述**:
  - `students` 表的 `class_name` 字段没有索引，班级含 400+ 学生时按班级查询会变慢
  - `score_logs` 表的 `student_id + created_at` 缺少复合索引，分数历史查询性能低
  - `checkin_records` 的 `checkin_time` 单字段查询没有覆盖索引优化
- **影响**: 数据量增长后查询响应时间显著增加
- **建议修复**:
  - `students(class_name)`
  - `score_logs(student_id, created_at DESC)`
  - 评估 `checkin_records(session_id, student_id)` 索引是否已足够
- **相关文件**:
  - `backend/app/models/student.py`
  - `backend/app/models/checkin.py`
  - 新增 Alembic migration

---

## 已修复问题（供参考）

| 编号 | 问题 | 修复时间 |
|------|------|----------|
| P0-1 | PostgreSQL 连接池配置（NullPool → QueuePool） | 2026-04-12 |
| P0-3 | 前端 `any` 类型滥用（API 层和 Vue 组件） | 2026-04-12 |
| P0-4 | 数据库 schema/migration 不一致 | 2026-04-12 |
| P0-5 | 签到竞态条件（前后端同时修复） | 2026-04-12 |
| P1-1 | 前端 API 响应解构残余不规范（schedulesApi.import 等） | 2026-04-12 |
| P1-2 | 前端网络/业务错误处理不完善（Checkin.vue + TanStack Query retry） | 2026-04-12 |
| P1-5 | 数据库索引缺失影响查询性能 | 2026-04-12 |

---

## 推荐下一步行动

1. **如果要修用户体验**: 优先处理 **P1-4（签到列表分页）**
2. **如果要修性能**: 优先处理 **P1-5（数据库索引）**
3. **如果要修代码规范**: 优先处理 **P1-3（后端 API 响应格式混用）**
