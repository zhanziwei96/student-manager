# ClassHub 系统测试方案

## 概述

根据当前系统功能生成的完整测试方案，涵盖所有角色（管理员、教师、学生）的核心功能，以及领域事件、审计日志、中间件等基础设施测试。

## 测试环境准备

### 1. 环境检查
```bash
# 检查服务状态（可选，测试使用内存数据库）
curl http://localhost:8000/api/health
curl http://localhost:5173

# 激活 Conda 环境（必须）
conda activate student-manage
# 或: source /home/yufeng/miniconda3/bin/activate student-manage
```

### 2. 测试账号准备
| 角色 | 用户名 | 密码 | 说明 |
|------|--------|------|------|
| 管理员 | admin | admin123 | 系统管理员 |
| 教师 | teacher1 | teacher123 | 测试教师账号 |
| 学生 | S001 | S001 | 学号作为账号和密码 |

**测试环境**: 前端 http://localhost:5173 (frontend-v3)

---

## 一、登录模块测试

### 1.1 登录页面功能测试
| 测试项 | 测试步骤 | 预期结果 |
|--------|----------|----------|
| 页面加载 | 访问首页，点击"开始使用" | 成功跳转到登录页 |
| 角色选择-管理员 | 选择"管理员"角色，输入admin/admin123 | 登录成功，跳转/admin |
| 角色选择-教师 | 选择"教师"角色，输入teacher1/teacher123 | 登录成功，跳转/teacher |
| 角色选择-学生 | 选择"学生"角色，输入S001/S001 | 登录成功，跳转/student |
| 角色错误提示 | 选择"学生"角色，输入管理员账号 | 提示"用户名或密码错误" |
| 密码错误 | 输入错误密码 | 提示"密码错误（还剩 X 次机会）" |
| 空用户名 | 不输入用户名直接登录 | 提示请输入用户名 |
| 空密码 | 不输入密码直接登录 | 提示请输入密码 |

### 1.2 登录状态保持测试
| 测试项 | 测试步骤 | 预期结果 |
|--------|----------|----------|
| 刷新页面 | 登录后刷新页面 | 保持登录状态 |
| 多标签页 | 在新标签页打开系统 | 自动识别登录状态 |
| 登出功能 | 点击右上角"退出登录" | 清除登录状态，跳转到首页 |

---

## 二、管理员模块测试

### 2.1 学生管理测试
| 测试项 | 测试步骤 | 预期结果 |
|--------|----------|----------|
| 查看学生列表 | 进入管理员页面 | 显示所有学生 |
| 添加学生 | 点击"添加学生"，填写学号姓名 | 学生添加到列表 |
| 搜索学生 | 在搜索框输入学号/姓名 | 筛选显示匹配学生 |
| 班级筛选 | 选择班级下拉框 | 只显示该班级学生 |
| 查看状态 | 查看学生列表 | 显示账户启用/禁用状态 |

### 2.2 教师管理测试
| 测试项 | 测试步骤 | 预期结果 |
|--------|----------|----------|
| 查看教师列表 | 点击"教师管理" | 显示所有教师 |
| 创建教师 | 点击"创建教师"，填写信息 | 教师添加到列表 |
| 编辑教师 | 点击"编辑"，修改信息 | 信息更新成功 |
| 分配班级 | 为教师选择负责班级 | 班级分配成功 |
| 重置教师密码 | 点击"重置密码" | 密码重置成功 |

### 2.3 班级管理测试
| 测试项 | 测试步骤 | 预期结果 |
|--------|----------|----------|
| 查看班级列表 | 点击"班级管理" | 显示所有班级 |
| 班级统计 | 查看班级卡片 | 显示学生数和平均分 |
| 班级排序 | 查看列表 | 按班级名称排序 |

### 2.4 签到管理测试
| 测试项 | 测试步骤 | 预期结果 |
|--------|----------|----------|
| 查看签到记录 | 点击"签到管理" | 显示今日签到记录 |
| 班级筛选 | 选择班级 | 只显示该班级签到 |
| 签到时间 | 查看记录 | 显示具体签到时间 |

### 2.5 课表管理测试
| 测试项 | 测试步骤 | 预期结果 |
|--------|----------|----------|
| 查看课表 | 点击"课表管理" | 显示所有课程安排 |
| 导入课表 | 上传课表文件 | 成功导入课程 |
| 删除课程 | 点击"删除" | 课程从列表移除 |
| 查看教室 | 查看课程详情 | 显示上课教室信息 |

---

## 三、教师模块测试

### 3.1 班级控制测试
| 测试项 | 测试步骤 | 预期结果 |
|--------|----------|----------|
| 查看负责班级 | 进入教师页面 | 显示教师负责的所有班级 |
| 开始上课 | 选择班级点击"开始上课" | 上课状态激活，显示班级名 |
| 签到统计实时更新 | 学生签到后查看统计 | 已签到人数增加，签到率更新 |
| 结束上课 | 点击"结束上课" | 上课状态关闭 |

### 3.2 学生管理测试
| 测试项 | 测试步骤 | 预期结果 |
|--------|----------|----------|
| 查看学生列表 | 查看"我的学生"区域 | 只显示教师负责班级的学生 |
| 快速加分-课堂提问 | 点击"课堂提问"按钮 | 学生分数+2，立即显示 |
| 快速扣分-违反纪律 | 点击"违反纪律"按钮 | 学生分数-2，立即显示 |
| 快速扣分-旷课 | 点击"旷课"按钮 | 学生分数-5，立即显示 |
| 自定义分数 | 点击"加分"/"扣分"按钮 | 弹出分数调整对话框 |
| 分数输入 | 输入分数变化值和原因 | 分数更新 |
| 搜索学生 | 输入学号或姓名 | 筛选显示匹配学生 |
| 班级筛选 | 选择班级 | 只显示该班级学生 |
| 签到状态 | 查看学生卡片 | 显示已签到/未签到 |
| **乐观更新** | 点击快速分数按钮 | UI立即更新，无需刷新 |

### 3.3 签到管理测试
| 测试项 | 测试步骤 | 预期结果 |
|--------|----------|----------|
| 查看签到状态 | 上课中查看统计 | 显示已签到和未签到人数 |
| 签到率计算 | 查看签到率百分比 | 计算正确（已签到/应到） |

### 3.4 课表管理测试
| 测试项 | 测试步骤 | 预期结果 |
|--------|----------|----------|
| 查看今日课表 | 进入教师仪表板 | 显示今日课程 |
| 管理课表 | 点击"管理课表" | 跳转到课表管理页 |
| 查看课程时间 | 查看课表 | 显示上课时间 |
| 查看教室 | 查看课表 | 显示上课教室 |

---

## 四、学生模块测试

### 4.1 个人信息测试
| 测试项 | 测试步骤 | 预期结果 |
|--------|----------|----------|
| 查看个人信息 | 进入学生页面 | 显示学号、姓名、班级、分数 |
| 查看排名 | 查看仪表板 | 显示班级排名 |
| 签到状态 | 查看"签到状态" | 显示今日是否已签到 |
| 上课状态 | 教师开始上课后查看 | 显示"上课中"标签 |

### 4.2 签到功能测试
| 测试项 | 测试步骤 | 预期结果 |
|--------|----------|----------|
| 签到按钮显示 | 教师上课后 | 显示"立即签到"按钮 |
| 签到按钮隐藏 | 教师未上课或已签到 | 不显示签到按钮 |
| 执行签到 | 点击"立即签到" | 签到成功，状态更新为"已签到" |
| 重复签到 | 已签到后再次点击 | 提示"今日已签到" |

### 4.3 分数历史测试
| 测试项 | 测试步骤 | 预期结果 |
|--------|----------|----------|
| 查看分数历史 | 滚动到"分数变化历史" | 显示所有分数变更记录 |
| 加分记录 | 查看正数变更 | 显示为绿色 |
| 扣分记录 | 查看负数变更 | 显示为红色 |
| 变更原因 | 查看记录详情 | 显示变更原因和操作人 |
| 时间排序 | 查看记录顺序 | 按时间倒序排列（最新在上） |

### 4.4 修改密码测试
| 测试项 | 测试步骤 | 预期结果 |
|--------|----------|----------|
| 打开修改密码 | 点击"修改密码" | 弹出密码修改对话框 |
| 旧密码验证 | 输入错误旧密码 | 提示"旧密码错误" |
| 成功修改 | 输入正确信息 | 密码修改成功，提示成功 |

---

## 五、公共页面测试

### 5.1 首页测试
| 测试项 | 测试步骤 | 预期结果 |
|--------|----------|----------|
| 首页显示 | 访问 http://localhost:5173 | 显示ClassHub首页 |
| 统计数据 | 查看首页统计 | 显示正确学生数、班级数、今日签到 |
| 开始使用 | 点击"开始使用" | 跳转到登录页 |

---

## 六、前端功能测试 (FE-006)

### 6.1 乐观更新测试

> **功能说明**: FE-006 重构后，分数更新采用 TanStack Query 乐观更新模式

| 测试项 | 测试步骤 | 预期结果 |
|--------|----------|----------|
| 快速按钮响应 | 点击"课堂提问"按钮 | UI立即显示新分数（无需等待服务器） |
| 网络延迟处理 | 模拟慢速网络后点击 | UI先更新，后台同步 |
| 错误回滚 | 模拟网络错误后点击 | 分数自动回滚到原值 |
| 批量更新 | 快速点击多个学生 | 每个学生的分数都正确更新 |
| 加载状态 | 点击快速按钮 | 按钮禁用，防止重复点击 |

### 6.2 Feature 组件测试

| 测试项 | 测试步骤 | 预期结果 |
|--------|----------|----------|
| StudentCard | 查看教师学生页面 | 卡片显示学生信息、分数、操作按钮 |
| ScoreDialog | 点击"加分"按钮 | 弹出分数调整对话框 |
| StudentFilters | 查看筛选区域 | 班级筛选和搜索功能正常 |
| QuickScoreButton | 查看快速操作区 | 三个快速分数按钮正常显示 |

### 6.3 状态管理测试

| 测试项 | 测试步骤 | 预期结果 |
|--------|----------|----------|
| TanStack Query | 查看网络请求 | 使用 useQuery/useMutation |
| 缓存更新 | 更新分数后 | 缓存自动更新，UI同步 |
| 数据一致性 | 刷新页面 | 数据与服务器一致 |

---

## 七、权限控制测试

### 7.1 角色权限测试
| 测试项 | 测试步骤 | 预期结果 |
|--------|----------|----------|
| 学生访问管理员页 | 学生登录后访问/admin | 重定向到/student |
| 教师访问管理员页 | 教师登录后访问/admin | 重定向到/teacher |
| 未登录访问 | 未登录访问任何内部页 | 重定向到登录页 |
| 已登录访问登录页 | 已登录用户访问/login | 根据角色重定向到对应首页 |

### 7.2 API权限测试
| 测试项 | 测试步骤 | 预期结果 |
|--------|----------|----------|
| 学生访问管理员API | 学生调用/admin/users | 返回403无权访问 |
| 教师访问其他班级 | 教师访问非负责班级学生 | 只能看到负责班级数据 |
| 过期Token | 使用过期session调用API | 返回401需要登录 |

### 7.3 权限检查机制一致性 (BE-002)

> **修复说明**: 已统一使用 FastAPI 依赖注入方式进行权限检查

| 测试项 | 测试步骤 | 预期结果 |
|--------|----------|----------|
| 依赖注入方式-开始上课 | 教师调用 POST /class-session/start | 正常验证并返回课堂信息 |
| 依赖注入方式-结束上课 | 教师调用 POST /class-session/end | 正常验证并结束课堂 |
| 依赖注入方式-学生查询 | 学生调用 GET /class-session/{class_name} | 正常验证并返回课堂状态 |
| 未登录访问 | 未登录调用受保护端点 | 返回401需要登录 |

**架构规范**:
```python
# ✅ 正确：使用 FastAPI 依赖注入
@router.post("/class-session/start")
async def begin_class(
    user: dict = Depends(get_current_user)
):
    # 直接使用 user 参数

# ❌ 错误：手动调用 require_login
await require_login(request)  # 已废弃
```

---

## 八、自动化测试

### 8.1 测试命令
```bash
# 运行全部测试
pytest tests/ -v

# 仅单元测试
pytest tests/unit -v

# 仅集成测试
pytest tests/integration -v

# 仅前端相关测试（新增）
pytest tests/unit/crud/test_student.py -v
pytest tests/integration/test_students_api_enhanced.py -v

# 生成覆盖率报告
pytest tests/ --cov=backend/app --cov-report=html
pytest tests/ --cov=backend/app --cov-report=term
```

### 8.2 测试结构

```
tests/
├── unit/                          # 单元测试
│   ├── test_jwt.py               # JWT 工具测试
│   ├── test_jwt_deps.py          # JWT 依赖测试
│   ├── test_config.py            # 配置加载测试 - BE-001
│   ├── test_events.py            # 领域事件基础设施
│   ├── test_event_handlers.py    # 事件处理器
│   ├── test_middleware.py        # 审计中间件
│   ├── test_security.py          # 安全工具
│   ├── test_exceptions.py        # 异常处理
│   ├── test_upload.py            # 文件上传安全 - SEC-001
│   ├── models/                   # 模型测试
│   │   ├── test_user.py          # 用户模型
│   │   └── test_student.py       # 学生模型
│   └── crud/                     # CRUD 测试
│       ├── test_user.py          # 用户 CRUD
│       ├── test_student.py       # 学生 CRUD - 含乐观更新测试
│       ├── test_checkin.py       # 签到 CRUD
│       ├── test_audit.py         # 审计日志
│       ├── test_concurrent_score_update.py    # 并发分数更新 - BE-008
│       └── test_concurrent_login_failure.py   # 并发登录失败 - BE-008
│
├── integration/                   # 集成测试
│   ├── test_jwt_auth.py          # JWT 认证集成
│   ├── test_login_api_enhanced.py # 登录 API
│   ├── test_students_api_enhanced.py # 学生 API - 含乐观更新场景
│   ├── test_users_api_enhanced.py # 用户 API
│   ├── test_checkin_api_enhanced.py # 签到 API
│   ├── test_user_api.py          # 用户 API 基础
│   └── test_system_api.py        # 系统 API
│
└── browser/                       # 浏览器测试（新增建议）
    └── test_optimistic_update.py  # 乐观更新 E2E 测试
```

### 8.3 测试统计

| 类别 | 数量 | 说明 |
|------|------|------|
| **单元测试** | **200+** | 独立测试各模块功能 |
| **集成测试** | **100+** | 测试 API 端到端流程 |
| **浏览器测试** | **建议新增** | Playwright 乐观更新测试 |
| **总计** | **300+** | 全量测试覆盖 |

### 8.4 覆盖率报告

**总体覆盖率: 92%**

新增模块:
| 模块 | 覆盖率 | 说明 |
|------|--------|------|
| `backend/app/core/upload.py` | 100% | 文件上传安全 - SEC-001 |
| `frontend/src/features/students/` | 建议新增 | 前端 Feature 组件 |

核心模块:
| 模块 | 覆盖率 | 说明 |
|------|--------|------|
| `backend/app/core/events.py` | 100% | 领域事件基础设施 |
| `backend/app/events/handlers.py` | 100% | 事件处理器 |
| `backend/app/crud/audit.py` | 100% | 审计日志 CRUD |
| `backend/app/crud/user.py` | 100% | 用户 CRUD |
| `backend/app/api/routes/users.py` | 100% | 用户 API |
| `backend/app/models/*` | 90-100% | 数据模型层 |
| `backend/app/api/routes/*.py` | 86-100% | API 路由层 |
| `backend/app/core/middleware.py` | 93% | 审计中间件 |
| `backend/app/crud/student.py` | 72% | 学生 CRUD（含乐观锁） |
| `backend/app/crud/user.py` | 87% | 用户 CRUD（含乐观锁） |
| `backend/app/crud/checkin.py` | 96% | 签到 CRUD |

### 8.5 测试覆盖的核心功能

**JWT 认证**
- Token 创建和解码
- Token 过期处理
- HttpOnly Cookie 设置和清除
- 受保护路由访问控制
- 管理员权限验证

**领域事件 (DB-003 修复)**
- `ScoreUpdated` 事件发布与订阅
- 事务边界管理（after_commit 模式）
- 事件处理器执行
- ScoreLog 自动记录

**乐观更新 (FE-006 新增)**
- 前端 UI 立即响应
- 缓存自动更新
- 错误自动回滚
- 后台数据同步

**审计日志**
- 敏感操作自动记录
- 中间件路由匹配
- 资源标识提取
- 审计日志查询

**文件上传安全 (SEC-001)**
- 文件类型白名单验证（扩展名 + MIME类型）
- 危险文件黑名单（30+种可执行文件）
- 文件大小限制检查
- 路径遍历攻击防护（`../`, `./` 清理）
- 文件名安全处理（UUID重命名）
- 临时文件自动清理
- 运行命令: `pytest tests/unit/test_upload.py -v`

**CRUD 操作**
- 学生增删改查
- 用户增删改查
- 签到记录管理
- 分数更新与历史（含乐观更新）
- **并发保护** (BE-008): 乐观锁防止并发更新数据丢失

**权限控制 (BE-002, BE-003)**
- 角色基础访问控制
- 资源级别权限（教师只能访问自己班级）
- 登录失败锁定
- 账号启用/禁用
- **权限检查机制统一** (BE-002)
- **业务逻辑分层** (BE-003) - 权限过滤在 CRUD 层处理

---

## 九、测试最佳实践

### 9.1 测试数据库隔离
- 单元测试：使用 `MagicMock` 隔离数据库
- 集成测试：使用内存 SQLite (`sqlite:///:memory:`)
- 测试数据：每个测试独立，自动清理

### 9.2 延迟导入模式
事件处理器使用延迟导入避免测试引擎冲突：
```python
def handle_score_updated(event):
    from app.core.db import engine  # 延迟导入
    with Session(engine) as session:
        ...
```

### 9.3 前端乐观更新测试建议
```typescript
// 测试乐观更新行为
test('分数更新应立即反映在UI上', async () => {
  const { result } = renderHook(() => useStudentScore())
  const initialScore = student.score
  
  // 触发更新
  act(() => {
    result.current.updateScore(student.id, 2, '测试')
  })
  
  // UI 应立即更新
  expect(student.score).toBe(initialScore + 2)
})
```

### 9.4 测试环境准备
```bash
# 1. 确认 Conda 环境
which python  # 应包含 miniconda

# 2. 安装依赖
pip install -r backend/requirements.txt

# 3. 运行测试前检查
python -c "from app.core.config import get_settings; print('配置加载正常')"

# 4. 执行测试
pytest tests/ -v
```

---

## 十、常见问题排查

### 10.1 测试失败排查
```bash
# 查看详细错误
pytest tests/unit/test_xxx.py -v --tb=long

# 单个测试调试
pytest tests/unit/test_events.py::TestEventBus::test_subscribe_and_publish -v

# 覆盖率缺口分析
pytest tests/ --cov=backend/app --cov-report=term-missing
```

### 10.2 乐观更新测试 (FE-006)

乐观更新测试验证前端 UI 立即响应：

```bash
# 运行学生相关测试
pytest tests/unit/crud/test_student.py -v
pytest tests/integration/test_students_api_enhanced.py -v
```

**测试覆盖场景**:
| 测试文件 | 测试场景 | 验证点 |
|---------|---------|--------|
| `test_student.py` | 分数更新 | 分数正确计算 |
| `test_students_api_enhanced.py` | API 响应 | 返回最新分数 |
| `test_concurrent_score_update.py` | 并发更新 | version 字段递增 |

### 10.3 并发保护测试 (BE-008)

并发保护测试验证乐观锁机制是否正确工作：

```bash
# 运行并发保护测试
pytest tests/unit/crud/test_concurrent_score_update.py tests/unit/crud/test_concurrent_login_failure.py -v
```

**测试覆盖场景**:
| 测试文件 | 测试场景 | 验证点 |
|---------|---------|--------|
| `test_concurrent_score_update.py` | 并发分数更新 | version 字段递增、冲突检测 |
| `test_concurrent_login_failure.py` | 并发登录失败 | 失败计数准确、锁定机制正确 |

**乐观锁机制验证**:
```python
# 1. 检查模型有 version 字段
student = session.get(Student, "S001")
assert student.version == 1  # 默认值为 1

# 2. 更新后版本递增
update_student_score(session, "S001", 5.0, "测试", "teacher")
session.refresh(student)
assert student.version == 2  # 版本号递增
```

### 10.4 文件上传安全测试 (SEC-001)

文件上传安全测试验证上传功能的安全控制：

```bash
# 运行文件上传安全测试
pytest tests/unit/test_upload.py -v
```

**测试覆盖场景**:
| 测试类别 | 测试数量 | 验证点 |
|---------|---------|--------|
| 文件名验证 | 7 | 空文件名、路径遍历 (`../`, `./`) |
| 扩展名验证 | 10+ | 白名单、危险扩展名黑名单 (30+) |
| MIME类型验证 | 10+ | 危险MIME类型黑名单 |
| 安全文件名生成 | 4 | UUID重命名、长文件名截断 |
| 完整上传流程 | 5 | 正常上传、超大文件拒绝、清理机制 |
| 文件清理 | 3 | 临时文件删除、旧文件清理 |

**安全验证示例**:
```python
# 1. 危险扩展名被拒绝
with pytest.raises(HTTPException):
    _validate_extension("virus.exe", [".xlsx"])

# 2. 路径遍历被清理
result = _validate_filename("../../../etc/passwd")
assert result == "etcpasswd"  # 危险字符被移除

# 3. 文件名使用UUID
filename = _generate_safe_filename("students.xlsx")
assert filename != "students.xlsx"  # UUID重命名
assert filename.endswith(".xlsx")  # 保留扩展名
```

### 10.5 常见错误

| 错误 | 原因 | 解决 |
|------|------|------|
| `ImportError: cannot import name 'Literal'` | Python 3.7 环境问题 | 确保使用 Python 3.11+ |
| `ModuleNotFoundError` | 未激活 Conda 环境 | 运行 `conda activate student-manage` |
| 测试挂起/超时 | 数据库引擎冲突 | 检查 `handlers.py` 使用延迟导入 |
| 覆盖率下降 | 新增代码未测试 | 补充对应测试文件 |
| 乐观更新失败 | QueryClient 配置错误 | 检查 onMutate/onError/onSettled |

---

**文档版本**: 2026-03-26 (FE-006 乐观更新重构)  
**适用系统版本**: ClassHub v3.0.0  
**架构**: FastAPI + SQLModel + Vue 3 + TanStack Query  
**测试框架**: pytest + pytest-cov + pytest-asyncio  
**覆盖率**: 92% (300+ 测试用例)
