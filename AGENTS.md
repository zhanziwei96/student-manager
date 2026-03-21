# ClassHub AI 助手注意事项

**本文档供 AI 助手在处理本项目时参考**

> ⚠️ **重要提醒**: 在处理任何请求前，请先阅读以下文档：
> 
> 1. **本文件 (AGENTS.md)** - 了解项目背景和技术约束
> 2. **[DEPLOYMENT.md](./DEPLOYMENT.md)** - 查看环境部署状态，如果环境已就绪则无需重复部署
> 3. **[TEST_PLAN.md](./TEST_PLAN.md)** - 查看测试方案，了解功能测试用例
> 
> **环境检查命令**（优先执行）：
> ```bash
> curl http://localhost:8000/health  # 后端
> curl http://localhost:3000          # 前端
> redis-cli ping                      # Redis
> ```
> 如果以上都正常返回，说明**环境已就绪，无需重复部署**。

---

## 文档导航

| 文档 | 路径 | 用途 |
|------|------|------|
| 本文件 | `./AGENTS.md` | AI助手注意事项、技术约束、最佳实践 |
| 部署文档 | `./DEPLOYMENT.md` | 环境部署指南、服务启动方法、问题排查 |
| 测试方案 | `./TEST_PLAN.md` | 功能测试用例、性能测试、安全测试方案 |
| 项目说明 | `./README.md` | 项目介绍、快速开始、使用说明 |

---

---

## 1. 项目概览

### 1.1 基本信息
| 项目 | 内容 |
|------|------|
| 名称 | ClassHub 班级管理系统 |
| 架构 | FastAPI + Vue3 + DDD |
| 前端 | Vue 3.5 + Naive UI 2.44 + Vite 8 |
| 后端 | Python 3.11 + FastAPI |
| 数据库 | SQLite |
| 缓存 | Redis |
| 状态管理 | Pinia |

### 1.2 目录结构
```
student-manager/
├── backend/           # FastAPI 后端 (DDD架构)
│   ├── interface/     # API 层 (Controllers)
│   ├── application/   # 应用服务层
│   ├── domain/        # 领域层 (实体、值对象)
│   └── infrastructure/# 基础设施层 (DB, Cache, Security)
├── frontend/          # Vue3 前端
│   ├── src/views/     # 页面组件
│   ├── src/api/       # API 请求
│   └── src/stores/    # Pinia 状态管理
├── data/              # SQLite 数据库文件
└── uploads/           # 上传文件存储
```

---

## 2. 技术栈约束

### 2.1 前端 - 必须使用 Naive UI
**⚠️ 重要**: 本项目已完全从 Element Plus 迁移到 Naive UI

| Element Plus | Naive UI 替代 |
|--------------|---------------|
| el-button | n-button |
| el-input | n-input |
| el-select | n-select |
| el-card | n-card |
| el-table | n-data-table |
| el-dialog | n-modal |
| el-form | n-form |
| el-alert | n-alert |
| el-tag | n-tag |
| el-dropdown | n-dropdown |

**主题配置**: 深色主题 (#0a0a0f 背景，#6366f1 主色)

### 2.2 后端 - DDD 架构约束
必须遵循分层架构：
```
Interface → Application → Domain ← Infrastructure
```

- **Interface**: 只处理 HTTP 请求/响应，调用 Application 服务
- **Application**: 编排领域对象，处理事务
- **Domain**: 核心业务逻辑，不依赖外部框架
- **Infrastructure**: 数据库、缓存、安全实现

### 2.3 安全约束
- 所有密码必须加盐哈希存储
- 使用 Session 认证（不是 JWT）
- XSS 防护：输出必须 HTML 转义
- 限流：登录 5次/分钟，签到 10次/分钟

---

## 3. 常见业务规则

### 3.1 学生管理
```
- 学号唯一，不能为空
- 班级可为空（未分班）
- 默认分数 70 分
- 删除班级会级联删除该班级所有学生
```

### 3.2 签到规则
```
- 学生一天只能签到一次
- 签到需要学号+姓名匹配
- 课堂必须处于"上课中"状态才能签到
- 老师可以代签到（记录代签人）
```

### 3.3 分数规则
```
- 分数变更必须记录原因
- 支持批量重置（仅管理员）
- 分数变更日志不可删除
```

### 3.4 权限规则
```
- 管理员(admin): 全部权限
- 教师(teacher): 管理分配班级
- 学生(公开): 仅签到/查询自己
```

---

## 4. API 规范

### 4.1 响应格式
```json
{
  "success": true|false,
  "message": "操作描述",
  "data": {}
}
```

### 4.2 状态码使用
| 状态码 | 使用场景 |
|--------|----------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 参数错误 |
| 401 | 未登录 |
| 403 | 无权限 |
| 429 | 限流触发 |
| 500 | 服务器错误 |

### 4.3 重要端点
```
POST   /api/login              # 限流 5/分钟
GET    /api/students           # 支持缓存
POST   /api/students           # 添加学生
POST   /api/students/{id}/score # 限流 10/分钟
POST   /api/checkin            # 限流 10/分钟
POST   /api/student/query      # 公开接口
GET    /health                 # 健康检查
```

---

## 5. 常见问题与解决方案

### 5.1 Session 问题
**问题**: `SessionMiddleware must be installed`

**解决**: 
- CacheMiddleware 中使用 try/except 访问 request.session
- 不要直接用 hasattr 检查 session

### 5.2 Naive UI 消息问题
**问题**: `No outer <n-message-provider /> founded`

**解决**:
- 确保 App.vue 中包裹了 n-message-provider
- 在 setup 外使用需通过 window.$message

### 5.3 限流器导入问题
**问题**: `cannot import name 'default_identifier'`

**解决**:
- 使用自定义的 identifier 和 callback 函数
- 不要导入 fastapi_limiter.depends 中的默认函数

### 5.4 缓存 Key 规范
```python
# 学生列表
CacheKeyBuilder.student_list(class_name)
# 学生统计
CacheKeyBuilder.student_stats()
# 班级列表
CacheKeyBuilder.class_list()
```

---

## 6. 代码风格指南

### 6.1 Python 后端
```python
# ✅ 正确：使用类型注解
def get_student(self, student_id: str) -> Optional[Student]:
    pass

# ✅ 正确：异常处理分层
try:
    # 领域操作
except DomainException as e:
    # 转换为 HTTP 异常
    raise HTTPException(status_code=400, detail=str(e))

# ✅ 正确：依赖注入
def get_student_service():
    db = Database()
    repo = SQLiteStudentRepository(db)
    return StudentAppService(repo)
```

### 6.2 Vue 前端
```vue
<!-- ✅ 正确：使用 Naive UI 组件 -->
<n-button type="primary" @click="handleSubmit">
  提交
</n-button>

<!-- ✅ 正确：深色主题样式 -->
<style scoped>
.card {
  background: rgba(19, 19, 31, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.08);
}
</style>
```

---

## 7. 修改检查清单

在对代码进行修改前，确认以下事项：

### 7.1 前端修改
- [ ] 使用的是 Naive UI 组件（n-*），不是 Element Plus
- [ ] 样式符合深色主题设计
- [ ] API 调用使用封装好的 request.js
- [ ] 新增路由已在 router 中注册

### 7.2 后端修改
- [ ] 接口遵循 DDD 分层架构
- [ ] 认证检查使用 require_login / require_admin
- [ ] 限流已配置（敏感接口）
- [ ] XSS 防护已应用（sanitize_* 函数）
- [ ] 缓存更新/清除逻辑已考虑

### 7.3 数据库修改
- [ ] 迁移脚本放在 migrations/ 目录
- [ ] 已在 MigrationManager 中注册
- [ ] 考虑向后兼容性

---

## 8. 环境管理

### 8.1 启动命令
```bash
# 后端（需先激活 conda 环境）
conda activate student-manage
cd backend && python main.py

# 前端
cd frontend && pnpm dev

# 完整启动（后台）
make dev
```

### 8.2 健康检查
```bash
# 后端健康
curl http://localhost:8000/health

# 前端访问
open http://localhost:3000
```

---

## 9. 调试技巧

### 9.1 后端调试
```python
# 添加日志
from infrastructure.logging import logger
logger.debug(f"调试信息: {value}")
logger.info("操作信息")
logger.error("错误信息", exc_info=True)
```

### 9.2 前端调试
```javascript
// API 请求调试
const res = await api.getStudents()
console.log('API响应:', res)

// Pinia 状态调试
const userStore = useUserStore()
console.log('用户信息:', userStore.userInfo)
```

---

## 10. 文档维护规则（重要）

### 10.1 环境变更时必须更新 DEPLOYMENT.md
**⚠️ 如果代码涉及到环境或依赖变更，必须同步更新 DEPLOYMENT.md：**

| 变更类型 | 需要更新的文档 | 更新内容示例 |
|----------|----------------|--------------|
| 新增 Python 依赖 | DEPLOYMENT.md | 在"安装后端依赖"章节添加新包 |
| 新增 Node.js 依赖 | DEPLOYMENT.md | 在"安装前端依赖"章节添加新包 |
| 新增服务/中间件 | DEPLOYMENT.md | 添加服务安装和启动说明 |
| 环境变量变更 | DEPLOYMENT.md | 更新环境配置章节 |
| 启动命令变化 | DEPLOYMENT.md | 更新启动命令示例 |
| 端口变更 | DEPLOYMENT.md | 更新服务配置表格 |

**更新后检查**：确保 DEPLOYMENT.md 中的安装步骤能在干净环境中复现

### 10.2 功能变更时必须检查 TEST_PLAN.md
**⚠️ 如果项目有变化或新增功能，必须检查 TEST_PLAN.md 是否需要更新：**

| 变更类型 | 检查内容 | 可能需要更新的章节 |
|----------|----------|-------------------|
| 新增 API 接口 | 添加对应测试用例 | 5. 接口测试用例 |
| 修改接口逻辑 | 更新测试预期结果 | 4. 功能测试用例 |
| 新增功能模块 | 添加完整测试用例集 | 4. 功能测试用例 |
| 权限规则变化 | 更新权限测试点 | 7. 安全测试方案 |
| 性能要求变化 | 更新性能指标 | 6. 性能测试方案 |
| 限流规则变化 | 更新限流测试 | 4.3 限流测试 |

**检查清单**：
- [ ] 新功能是否有对应的测试用例？
- [ ] 修改的功能测试用例是否需要调整？
- [ ] 接口清单是否完整？
- [ ] 优先级划分是否合理？

---

## 11. 禁止事项

❌ **不要做的**:
1. 引入 Element Plus 组件（项目已迁移到 Naive UI）
2. 在 Domain 层使用 FastAPI/数据库相关的导入
3. 直接操作数据库而不经过 Repository
4. 在日志中记录密码等敏感信息
5. 修改测试文件中的断言逻辑（除非修复bug）
6. 删除 migrations/ 目录中的历史迁移文件
7. 提交包含数据库密码的配置文件
8. **遗漏 DEPLOYMENT.md 文档更新**（环境/依赖变更后必须更新）
9. **遗漏 TEST_PLAN.md 文档检查**（新增功能后必须检查测试方案）

✅ **应该做的**:
1. 每次修改后运行健康检查
2. 添加/修改功能时同步更新测试用例
3. 重大变更前创建备份
4. 遵循现有的代码风格
5. 复杂逻辑添加注释说明
6. **环境/依赖变更后立即更新 DEPLOYMENT.md**
7. **功能变更后检查并更新 TEST_PLAN.md**

---

## 12. 快速参考

### 12.1 常用导入
```python
# 后端
from fastapi import APIRouter, Request, HTTPException, Depends
from infrastructure.security.session import require_login, require_admin
from infrastructure.cache import get_cache_client, CacheKeyBuilder
from infrastructure.logging import logger

# 前端
import { useMessage, useDialog } from 'naive-ui'
import { useUserStore } from '@/stores/user'
import * as api from '@/api'
```

### 12.2 常用路径别名
| 别名 | 对应路径 |
|------|----------|
| @ | frontend/src |
| @components | frontend/src/components |
| @views | frontend/src/views |
| @api | frontend/src/api |

### 12.3 主题颜色
```css
/* 主色 */
--primary-color: #6366f1;
--primary-light: #818cf8;

/* 强调色 */
--accent-color: #06b6d4;

/* 背景 */
--bg-primary: #0a0a0f;
--bg-card: rgba(19, 19, 31, 0.8);

/* 文字 */
--text-primary: #ffffff;
--text-muted: #94a3b8;
```

---

## 13. 版本信息

| 日期 | 版本 | 说明 |
|------|------|------|
| 2025-03-21 | v3.1 | 新增文档导航，整合 DEPLOYMENT.md 和 TEST_PLAN.md 引用 |
| 2025-03-21 | v3.0 | 从 Element Plus 迁移到 Naive UI，Vite 8 升级 |

---

## 14. 相关文档索引

### 14.1 必读文档（按优先级排序）
1. **AGENTS.md** (本文档) - AI助手操作指南
2. **DEPLOYMENT.md** - 环境部署与服务管理
3. **TEST_PLAN.md** - 测试方案与用例
4. **README.md** - 项目总体介绍

### 14.2 其他参考文档
- `backend/README.md` - 后端详细说明
- `frontend/README.md` - 前端详细说明
- `SECURITY_SOLUTION.md` - 安全解决方案
- `OPTIMIZATION_STATUS.md` - 优化状态记录

---

**最后更新**: 2025-03-21  
**维护者**: Kimi Code CLI  

**快速链接**: [部署文档](./DEPLOYMENT.md) | [测试方案](./TEST_PLAN.md) | [项目说明](./README.md)
