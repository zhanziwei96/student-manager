# ClassHub 测试指南

> 最后更新时间：2026-04-01（已同步 P0/P1 修复）

## 测试结构

```
tests/
├── README.md                      # 本文件
├── conftest.py                   # 全局 pytest 配置和 Fixtures
├── pytest.ini                   # pytest 配置文件
├── unit/                         # 单元测试（250+ 测试用例）
│   ├── crud/                    # CRUD 操作测试（11 文件）
│   │   ├── test_audit.py       # 审计日志 CRUD
│   │   ├── test_checkin.py     # 签到 CRUD
│   │   ├── test_class_session.py  # 课堂会话 CRUD
│   │   ├── test_concurrent_login_failure.py  # 并发登录失败保护（BE-008）
│   │   ├── test_concurrent_score_update.py   # 并发分数更新保护（BE-008）
│   │   ├── test_schedule.py    # 课表 CRUD
│   │   ├── test_student.py     # 学生 CRUD
│   │   ├── test_student_performance.py  # 学生性能测试
│   │   ├── test_student_permission.py   # 学生权限测试
│   │   ├── test_student_score_boundary.py  # 分数边界测试
│   │   └── test_user.py        # 用户 CRUD
│   ├── models/                  # 模型测试（3 文件）
│   │   ├── test_course_schedule.py  # 课程表模型
│   │   ├── test_student.py     # 学生模型
│   │   └── test_user.py        # 用户模型
│   ├── test_audit_middleware.py # 审计日志中间件测试（SEC-006）
│   ├── test_config.py          # 配置加载测试
│   ├── test_cors_config.py     # CORS 配置测试
│   ├── test_event_handlers.py  # 事件处理器测试
│   ├── test_events.py          # 领域事件测试
│   ├── test_exceptions.py      # 异常处理测试
│   ├── test_jwt.py             # JWT 工具测试
│   ├── test_jwt_cookie_secure.py  # Cookie 安全测试
│   ├── test_jwt_deps.py        # JWT 依赖测试
│   ├── test_middleware.py      # 审计中间件测试
│   ├── test_security.py        # 安全工具测试
│   ├── test_security_settings.py  # 安全设置校验测试（P0）
│   ├── test_timezone.py        # 时区统一处理测试（P1）
│   └── test_upload.py          # 文件上传安全测试
├── integration/                  # 集成测试（110+ 测试用例，15 文件）
│   ├── conftest.py             # 集成测试配置
│   ├── test_active_class_sessions.py   # 活跃课堂 API 测试
│   ├── test_checkin_api_enhanced.py    # 签到 API 测试
│   ├── test_concurrent_login.py        # 并发登录测试
│   ├── test_dashboard_data_masking.py  # 数据脱敏测试
│   ├── test_jwt_auth.py        # JWT 认证测试
│   ├── test_login_api_enhanced.py      # 登录 API 测试
│   ├── test_rate_limit.py      # 限流测试
│   ├── test_schedule_api.py    # 课表 API 测试
│   ├── test_schedule_teacher_assignment.py  # 教师分配测试
│   ├── test_smoke.py           # 冒烟测试
│   ├── test_students_api_enhanced.py   # 学生 API 测试
│   ├── test_system_api.py      # 系统 API 测试
│   ├── test_token_refresh.py   # Token 刷新测试
│   ├── test_user_api.py        # 用户管理 API 测试
│   └── test_users_api_enhanced.py      # 用户 API 增强测试
└── e2e/                          # E2E 测试（Playwright）
    └── README.md                # E2E 测试说明
└── browser/                      # 浏览器录制测试
    └── recorded_test.py         # 录制回放测试
```

## 测试统计

| 层级 | 测试文件数 | 测试用例数 | 说明 |
|------|-----------|-----------|------|
| Unit - CRUD | 11 | ~100 | 数据库操作测试（含并发、性能、边界） |
| Unit - Models | 3 | ~20 | 数据模型测试 |
| Unit - Core | 15 | ~165 | 核心模块测试（JWT、安全、事件、时区、健康检查等） |
| **Unit Total** | **29** | **285+** | 快速、独立运行 |
| Integration | 15 | 110+ | API 集成测试（含数据脱敏、Token刷新） |
| **Backend Total** | **44** | **380+** | **后端全部测试** |

### 测试覆盖率

- **代码覆盖率**: 92%
- **测试通过率**: 100% (380+/380+)
- **失败测试**: 0

## 新增测试文件说明（P0/P1 修复）

### 并发保护测试（BE-008）

| 测试文件 | 测试数 | 说明 |
|----------|--------|------|
| `test_concurrent_score_update.py` | 4 | 乐观锁防止并发更新数据丢失 |
| `test_concurrent_login_failure.py` | 7 | 并发登录失败计数保护 |

### 安全测试（P0/P1）

| 测试文件 | 测试数 | 说明 |
|----------|--------|------|
| `test_security_settings.py` | 7 | JWT 密钥校验、生产环境安全配置 |
| `test_cors_config.py` | 6 | CORS 白名单配置验证 |
| `test_audit_middleware.py` | 7 | 审计日志中间件（SEC-006） |
| `test_timezone.py` | 9 | 时区统一处理验证（Asia/Shanghai） |
| `test_health_check.py` | 13 | 健康检查增强（P2-3） |
| `test_upload.py` | ~15 | 文件类型白名单、路径遍历防护 |
| `test_jwt_cookie_secure.py` | ~8 | Cookie 安全属性验证 |

### 集成测试增强

| 测试文件 | 说明 |
|----------|------|
| `test_active_class_sessions.py` | 活跃课堂 API 测试 |
| `test_concurrent_login.py` | 并发登录场景测试 |
| `test_dashboard_data_masking.py` | 敏感数据脱敏验证 |
| `test_schedule_teacher_assignment.py` | 教师课表分配测试 |
| `test_token_refresh.py` | JWT Token 刷新机制测试 |

## 运行测试

### 1. 运行全部测试

```bash
# 激活环境
conda activate student-manage

# 运行全部测试
pytest tests/ -v

# 快速模式（无详细回溯）
pytest tests/ -q
```

### 2. 按层级运行

```bash
# 仅单元测试（推荐，速度快）
pytest tests/unit -v

# 仅集成测试
pytest tests/integration -v

# 仅冒烟测试
pytest tests/integration/test_smoke.py -v
pytest -m smoke
```

### 3. 按模块运行

```bash
# CRUD 测试
pytest tests/unit/crud -v

# 模型测试
pytest tests/unit/models -v

# 并发保护测试（BE-008）
pytest tests/unit/crud/test_concurrent_*.py -v

# JWT 测试
pytest tests/unit/test_jwt.py -v
pytest tests/unit/test_jwt_deps.py -v

# 安全测试
pytest tests/unit/test_security.py -v
pytest tests/unit/test_upload.py -v

# 认证相关
pytest tests/integration/test_jwt_auth.py -v
pytest tests/integration/test_login_api_enhanced.py -v

# 学生管理
pytest tests/integration/test_students_api_enhanced.py -v

# 用户管理
pytest tests/integration/test_users_api_enhanced.py -v
```

### 4. 查看测试覆盖率

```bash
# 安装 coverage 工具
pip install pytest-cov

# 生成覆盖率报告
pytest tests/ --cov=app --cov-report=html

# 查看报告
open htmlcov/index.html

# 终端显示覆盖率
pytest tests/ --cov=app --cov-report=term

# 显示覆盖率缺口
pytest tests/ --cov=app --cov-report=term-missing
```

## 测试配置

### pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
asyncio_mode = strict
asyncio_default_fixture_loop_scope = function
markers =
    smoke: 冒烟测试（核心业务流程）
    integration: 集成测试
    unit: 单元测试
```

### 环境要求

- Python 3.11+
- pytest 9.0+
- pytest-asyncio
- sqlmodel
- httpx (集成测试)
- 其他依赖见 `backend/requirements.txt`

## Fixtures 说明

### 数据库相关

- `engine` - SQLModel 内存数据库引擎
- `session` - 数据库会话（每个测试独立）

### 测试数据

- `test_student` - 预创建的学生
- `test_user` - 预创建的教师用户
- `test_admin` - 预创建的管理员用户

### 使用示例

```python
def test_example(session, test_student):
    # session: 数据库会话
    # test_student: 已创建的学生对象
    student = get_student(session, test_student.student_id)
    assert student is not None
```

## 系统测试步骤

### 环境准备

```bash
# 1. 检查后端服务
curl http://localhost:8000/health

# 2. 检查前端服务 (frontend-v3)
curl -I http://localhost:5173
```

### 系统测试执行步骤

#### Step 1: 用户认证流程测试

访问 http://localhost:5173 进行测试

| 步骤 | 操作 | 验证点 |
|-----|------|--------|
| 1.1 | 访问登录页 | 页面正常加载 |
| 1.2 | 输入错误密码 | 提示"用户名或密码错误" |
| 1.3 | 输入正确凭据 | 登录成功，JWT Token 写入 Cookie |
| 1.4 | 检查 Cookie | 存在 access_token cookie |
| 1.5 | 点击登出 | 清除 token，返回登录页 |

#### Step 2: 学生管理流程测试

| 步骤 | 操作 | 验证点 |
|-----|------|--------|
| 2.1 | 教师登录 | 登录成功 |
| 2.2 | 添加学生 | 学生添加到列表 |
| 2.3 | 搜索学生 | 可按姓名/学号搜索 |
| 2.4 | 更新分数 | 分数更新，显示变更记录 |
| 2.5 | 删除学生 | 学生从列表移除 |

#### Step 3: 签到功能测试

| 步骤 | 操作 | 验证点 |
|-----|------|--------|
| 3.1 | 开始课堂 | 点击"开始课堂" |
| 3.2 | 学生签到 | 输入学号签到成功 |
| 3.3 | 重复签到 | 提示"今日已签到" |
| 3.4 | 结束课堂 | 签到功能关闭 |

#### Step 4: 用户管理流程测试

| 步骤 | 操作 | 验证点 |
|-----|------|--------|
| 4.1 | 管理员登录 | 登录成功 |
| 4.2 | 创建教师用户 | 创建成功 |
| 4.3 | 新用户登录 | 可用新凭据登录 |
| 4.4 | 重置密码 | 密码重置成功 |
| 4.5 | 删除用户 | 用户从列表移除 |

## 添加新测试

### 添加 CRUD 单元测试

```python
import pytest
from sqlmodel import Session
from app.crud import new_function

def test_new_function(session: Session):
    """测试新功能"""
    result = new_function(session, ...)
    assert result is not None
```

### 添加模型单元测试

```python
# tests/unit/models/test_new.py
from app.models import NewModel

def test_new_model_creation():
    """测试模型创建"""
    model = NewModel(...)
    assert model.id is not None
```

### 添加集成测试

```python
# tests/integration/test_new_api.py
import pytest

@pytest.mark.asyncio
async def test_new_api(client):
    response = await client.get("/api/new-endpoint")
    assert response.status_code == 200
```

## CI/CD 集成

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest pytest-asyncio httpx
      - name: Run unit tests
        run: pytest tests/unit -v
      - name: Run integration tests
        run: pytest tests/integration -v
      - name: Generate coverage
        run: pytest tests/ --cov=app --cov-report=xml
```

## 常见问题

### Q1: 测试报错 "No module named 'app'"
**解决**: 确保在 student-manager 目录下运行测试，conftest.py 已添加 backend 到路径

### Q2: 单元测试很慢
**原因**: SQLModel 创建表需要时间
**优化**: 使用内存数据库，pytest-xdist 并行运行

```bash
pip install pytest-xdist
pytest tests/unit -n auto
```

### Q3: 如何调试测试
```python
def test_debug(session):
    # 打印调试信息
    result = some_function(session)
    print(f"Debug: {result}")
    
    # 或使用 breakpoint
    breakpoint()
```

## 维护者

如有问题，请联系开发团队。

---

**测试框架**: pytest + pytest-asyncio  
**测试覆盖率**: 89%  
**最后更新**: 2026-03-27
