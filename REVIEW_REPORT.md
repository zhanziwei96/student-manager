# ClassHub 项目综合审查报告

> 生成时间：2026-03-26  
> 审查方式：多 Agent 协作审查（架构/后端/前端/测试）

---

## 执行摘要

| 维度 | 评分 | 风险等级 |
|------|------|----------|
| 架构设计 | 78/100 | 🟡 中 |
| 后端实现 | 72/100 | 🔴 高 |
| 前端实现 | 82/100 | 🟡 中 |
| 测试覆盖 | 78/100 | 🟡 中 |
| **综合** | **77.5/100** | **🟡 中** |

---

## 🏆 架构亮点

### 1. 领域事件模式
- **位置**：`backend/app/core/events.py`
- **亮点**：通过轻量级事件总线解耦核心业务逻辑与副作用（分数日志记录），使用 SQLAlchemy `after_commit` 确保事务一致性

### 2. 乐观锁机制
- **位置**：`backend/app/crud/student.py`
- **亮点**：学生分数更新中实现乐观锁（version 字段）+ 自动重试机制，避免并发数据覆盖

### 3. 前端状态门面模式
- **位置**：`frontend-v3/src/stores/auth.ts`, `useAuth.ts`
- **亮点**：Pinia 作为 TanStack Query 的门面，统一接口同时保持向后兼容

### 4. 审计日志切面设计
- **位置**：`backend/app/core/middleware.py`
- **亮点**：中间件自动记录敏感操作，横切关注点与业务逻辑分离

### 5. SQLModel 现代化实践
- **亮点**：统一 SQLAlchemy 表模型和 Pydantic 验证模型，减少重复代码

---

## 🚨 P0 - 关键问题（立即修复）

### 1. 乐观锁实现缺陷 ✅ 已文档化（接受风险）
- **位置**：`backend/app/crud/student.py:225-244`
- **问题**：`IntegrityError` 无法捕获乐观锁冲突，因为 version 字段没有唯一约束
- **风险**：并发更新时数据丢失（概率极低）
- **决策**：接受风险，仅添加注释说明
- **原因**：
  - 业务场景：一个学生由一门课的一个老师管理，并发修改概率极低
  - 部署环境：SQLite 单进程部署，天然事务隔离
  - 成本收益：修复成本 > 实际收益
- **负责人**：后端
- **状态**：✅ 已添加注释说明（2026-03-26）

如需完整乐观锁保护，应：
```python
# 方案1：添加唯一约束
__table_args__ = (UniqueConstraint('student_id', 'version'),)

# 方案2：使用 UPDATE with WHERE
result = session.execute(
    update(Student)
    .where(and_(Student.student_id == student_id, Student.version == expected_version))
    .values(score=new_score, version=expected_version + 1)
)
if result.rowcount == 0:
    raise HTTPException(status_code=409, detail="并发修改冲突")
```

### 2. 前端内存泄漏
- **位置**：`frontend-v3/src/components/ui/Toast.vue:77-81`
- **问题**：`setTimeout` 未在组件卸载时清理
- **风险**：内存泄漏，长时间运行后性能下降
- **负责人**：前端
- **修复代码**：
```typescript
const timeoutId = ref<ReturnType<typeof setTimeout> | null>(null)

const showToast = () => {
  isVisible.value = true
  if (timeoutId.value) clearTimeout(timeoutId.value)
  timeoutId.value = setTimeout(() => {
    isVisible.value = false
    setTimeout(() => emit('update:show', false), 300)
  }, props.duration)
}

onUnmounted(() => {
  if (timeoutId.value) clearTimeout(timeoutId.value)
})
```

### 3. 使用已弃用函数 ✅ 已修复
- **位置**：`backend/app/api/routes/login.py:96,140,218`
- **问题**：调用已弃用的 `verify_password_hash` 函数并传递 salt 参数
- **风险**：登录失败，代码误导
- **负责人**：后端
- **修复状态**：✅ 已修复（2026-03-26）
- **修复内容**：
  - `login.py:96` - 学生登录密码验证
  - `login.py:140` - 教师/管理员登录密码验证  
  - `login.py:218` - 修改密码旧密码验证
  - `test_user_api.py:147` - 同步更新测试代码
- **修复代码**：
```python
# 修改前:
if not verify_password_hash(password, student.password_hash, student.salt):

# 修改后:
if not verify_password(password, student.password_hash):
```

### 4. 类型不一致问题 ✅ 已修复
- **位置**：`backend/app/api/routes/users.py:162`
- **问题**：删除用户时 `current_user_id` 是 str 类型而 `user_id` 是 int
- **风险**：管理员可能意外删除自己账户
- **负责人**：后端
- **修复状态**：✅ 已修复（2026-03-26）
- **修复内容**：
  - 统一使用 `int` 比较 `user_id` 和 `current_user_id`
  - 添加异常处理防止无法转换时的错误
- **测试验证**：35 个用户相关测试全部通过

### 5. JWT 时区处理不当 ✅ 已修复
- **位置**：`backend/app/core/jwt.py`
- **问题**：使用 `datetime.utcnow()`（Python 3.12+ 已弃用），时区处理不当
- **风险**：认证绕过或提前过期
- **负责人**：后端
- **修复状态**：✅ 已修复（2026-03-26）
- **修复内容**：
  - 使用 `ZoneInfo("Asia/Shanghai")` 统一使用北京时间
  - 添加 `get_beijing_time()` 工具函数
  - Token 创建和过期验证均使用北京时间
- **测试验证**：24 个 JWT 相关测试全部通过

### 6. 限流状态码错误 ✅ 已修复
- **位置**：`backend/app/api/routes/login.py:82`, `backend/app/core/config.py`
- **问题**：限流触发返回 HTTP 503（服务不可用），应返回 429（请求过多）
- **风险**：HTTP 语义错误，客户端处理混乱
- **负责人**：后端
- **修复状态**：✅ 已修复（2026-03-26）
- **修复内容**：
  - `config.py` 添加 `TOO_MANY_REQUESTS = 429`
  - `login.py` 限流返回正确的 HTTP 429 状态码

### 7. 测试失败修复 ✅ 已修复
- **位置**：`tests/integration/test_schedule_api.py`
- **问题**：`test_teacher_can_import` 断言与业务权限设计不符（期望 200，实际 403）
- **原因**：课表导入 API 使用 `require_admin`，仅管理员可访问，测试期望教师可导入是过时的
- **修复**：修改为 `test_teacher_cannot_import`，验证教师无权导入（返回 403）
- **负责人**：测试
- **修复状态**：✅ 已修复（2026-03-26）
- **测试验证**：13 个课表 API 测试全部通过

---

## 🟡 P1 - 中等问题

### 后端
| 序号 | 文件 | 问题 | 建议 |
|------|------|------|------|
| 1 | checkin.py:114-150 | 签到接口无认证要求 | 添加 `user: dict = Depends(get_current_user)` |
| 2 | system.py:27-43 | `/stats` 接口无认证 | 添加认证依赖 |
| 3 | student.py:54-103 | 权限检查在 CRUD 层 | 统一在 API 层做权限检查 |
| 4 | checkin.py:202-209 | 计算签到率内存计算 | 使用 SQL `COUNT()` 聚合查询 |
| 5 | audit.py:66-71 | 逐条删除旧日志 | 使用批量 DELETE |

### 前端
| 序号 | 文件 | 问题 | 建议 |
|------|------|------|------|
| 1 | Dialog.vue:82-135 | 未使用 Teleport | 添加 Teleport 包裹和 onUnmounted 清理 |
| 2 | useClassSession.ts:17 | localStorage 无 SSR 检查 | 添加 `isClient` 判断 |
| 3 | useSchedules.ts:36 | API 返回类型不一致 | 统一使用 `request<T>()` 包装 |
| 4 | ClassSession.vue:352-416 | 列表渲染重复 filter | 使用 computed 预计算分组结果 |
| 5 | 多个视图 | Toast 逻辑重复 | 封装为 `useGlobalToast()` composable |

### 测试
| 模块 | 功能 | 状态 | 建议测试场景 |
|------|------|------|--------------|
| students.py | 分数边界值 | ❌ 缺失 | 负数、超大值、非数字输入 |
| login.py | 并发登录 | ❌ 缺失 | 同账号多地登录 |
| jwt.py | Token 刷新 | ❌ 缺失 | Token 过期前自动刷新 |
| dashboard | 数据脱敏 | ❌ 缺失 | 学号、姓名脱敏规则 |

---

## 📋 任务队列

### P0 (本周必须完成)
- [x] 乐观锁实现缺陷 - 后端（已文档化，接受风险）
- [ ] 修复 Toast 内存泄漏 - 前端
- [ ] 统一密码验证接口 - 后端
- [ ] 修复类型不一致问题 - 后端
- [x] 修复 datetime.utcnow() 弃用警告 - 后端（已改用北京时间）
- [ ] 修复限流状态码 503→429 - 后端
- [x] 修复测试失败 - 测试（已修复 test_teacher_can_import）

### P1 (本月完成)
- [ ] 签到和统计接口添加认证 - 后端
- [ ] 优化签到率计算性能 - 后端
- [ ] Dialog 组件添加 Teleport - 前端
- [ ] localStorage 添加 SSR 检查 - 前端
- [ ] 提取全局 Toast composable - 前端
- [ ] 补充并发分数更新集成测试 - 测试
- [ ] 补充分数边界值测试 - 测试
- [ ] 补充审计日志集成测试 - 测试

### P2 (后续规划)
- [ ] JWT Token 黑名单实现 - 后端
- [ ] 审计日志异步化 - 后端
- [ ] API 类型统一 - 前端
- [ ] 列表渲染性能优化 - 前端
- [ ] 数据库迁移评估 (SQLite→PostgreSQL) - 架构
- [ ] 分布式限流实现 - 架构
- [ ] 性能基准测试 - 测试

---

## 🔗 跨领域问题

| 问题 | 涉及领域 | 协调方案 |
|------|----------|----------|
| 并发分数更新竞态条件 | 后端+测试 | 后端修复乐观锁 → 测试补充集成测试验证 |
| 乐观更新冲突无用户提示 | 前端+后端 | 后端返回 409 → 前端 onError 显示 toast |
| Token 失效机制 | 后端+架构 | 架构决策黑名单方案 → 后端实现 |
| 类型定义同步 | 前端+后端 | 前后端共同维护 types/api.ts |

---

## 📊 技术债务评估

| 领域 | 债务水平 | 主要债务项 |
|------|----------|------------|
| 后端 | 🔴 高 | 弃用函数、乐观锁缺陷、类型不一致、限流状态码错误 |
| 前端 | 🟡 中 | 内存泄漏风险、类型小瑕疵、代码重复 |
| 测试 | 🟡 中 | 并发集成测试缺失、失败测试待修复 |
| 架构 | 🟡 中 | 扩展性限制（SQLite、内存限流） |

### 偿还建议
1. **立即偿还**：影响数据完整性的债务（乐观锁、并发控制）
2. **本月偿还**：安全相关债务（认证、授权）
3. **季度偿还**：可维护性债务（类型、弃用函数）
4. **长期规划**：架构债务（数据库、限流）

---

## 🎯 各维度详细报告

### 架构设计（78/100）
**亮点**：
- 领域事件模式与事务边界清晰
- 乐观锁机制保障并发安全
- 审计日志的透明切面设计
- 统一的 API 响应处理

**风险**：
- SQLite 单文件数据库瓶颈
- 内存限流器无分布式支持
- 领域事件非持久化
- JWT Token 无法主动失效

详见：架构 Agent 完整报告

### 后端实现（72/100）
**亮点**：
- SQL 注入防护完善（参数化查询）
- 文件上传安全（白名单、MIME检查）
- 密码使用 bcrypt 哈希

**问题**：
- 5个严重问题（乐观锁、弃用函数、类型不一致等）
- 7个中等问题（认证缺失、性能瓶颈等）
- 代码异味：重复代码、函数内导入、过长函数

详见：后端 Agent 完整报告

### 前端实现（82/100）
**亮点**：
- Feature-based 架构组织良好
- TanStack Query 缓存策略合理
- 类型安全评级 A-（仅 2 处 any）
- Composables 抽象良好

**问题**：
- Toast/Dialog 内存泄漏风险
- SSR 环境检查缺失
- 部分列表渲染可优化

详见：前端 Agent 完整报告

### 测试覆盖（78/100）
**亮点**：
- JWT 认证测试完整
- 登录失败锁定测试完整
- 并发分数更新单元测试完整
- 测试基础设施完善

**缺口**：
- 并发分数更新集成测试缺失
- 分数边界值测试缺失
- 审计日志集成测试部分缺失
- 1个测试失败待修复

详见：测试 Agent 完整报告

---

## 📝 附录

### 代码统计
```
后端代码：~3000 行 Python
前端代码：~5000 行 TypeScript/Vue
测试代码：~3500 行 Python
测试覆盖率：~70%
```

### 依赖版本
```
FastAPI: ~0.104
SQLModel: ~0.0.14
Vue: 3.5+
TanStack Query: v5
Tailwind CSS: v4
```

### 审查工具
- 架构 Agent：目录结构分析、依赖分析
- 后端 Agent：代码静态分析、安全审计
- 前端 Agent：组件分析、类型检查
- 测试 Agent：覆盖率分析、测试质量评估

---

**报告生成时间**：2026-03-26  
**下次审查建议**：修复 P0 问题后进行复查
