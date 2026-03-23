# ClassHub 测试指南

## 测试结构（新架构）

```
tests/
├── README.md                 # 本文件
├── conftest.py              # 全局 pytest 配置和 Fixtures
├── pytest.ini              # pytest 配置文件
├── integration/             # 集成测试（API 层）
│   ├── conftest.py         # 集成测试配置
│   ├── test_auth_api.py    # 认证 API 测试
│   ├── test_student_api.py # 学生管理 API 测试
│   ├── test_user_api.py    # 用户管理 API 测试
│   └── test_smoke.py       # 冒烟测试
└── unit/                    # 单元测试
    ├── crud/               # CRUD 操作测试
    │   ├── test_student.py # 学生 CRUD 测试
    │   ├── test_user.py    # 用户 CRUD 测试
    │   └── test_checkin.py # 签到 CRUD 测试
    ├── models/             # 模型测试
    │   ├── test_student.py # 学生模型测试
    │   └── test_user.py    # 用户模型测试
    └── test_security.py    # 安全工具测试
```

## 测试统计

| 层级 | 测试文件数 | 测试用例数 | 说明 |
|------|-----------|-----------|------|
| Unit - CRUD | 3 | 29 | 数据库操作测试 |
| Unit - Models | 2 | 10 | 数据模型测试 |
| Unit - Security | 1 | 5 | 安全工具测试 |
| **Unit Total** | **6** | **44** | 快速、独立运行 |
| Integration | 4 | 24 | API 集成测试 |
| **Total** | **10** | **68** | **全部通过** |

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

# 安全工具测试
pytest tests/unit/test_security.py -v

# 认证相关
pytest tests/integration/test_auth_api.py -v

# 学生管理
pytest tests/integration/test_student_api.py -v

# 用户管理
pytest tests/integration/test_user_api.py -v
```

### 4. 查看测试覆盖率

```bash
# 安装 coverage 工具
pip install pytest-cov

# 生成覆盖率报告
pytest tests/ --cov=app --cov-report=html

# 查看报告
open htmlcov/index.html
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
# tests/unit/crud/test_new.py
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
