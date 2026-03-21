# ClassHub 测试指南

## 测试结构

```
tests/
├── README.md                 # 本文件
├── conftest.py              # 根级别 pytest 配置
├── integration/             # 集成测试（Interface 层）
│   ├── conftest.py         # 集成测试配置（临时数据库、FastAPI 应用）
│   ├── test_auth_api.py    # 认证 API 测试（登录、登出、权限）
│   ├── test_student_api.py # 学生管理 API 测试（CRUD、分数）
│   ├── test_user_api.py    # 用户管理 API 测试（管理员功能）
│   └── test_smoke.py       # 冒烟测试（核心业务流程）
└── unit/                    # 单元测试
    ├── application/        # Application 层（用例编排）
    │   ├── conftest.py    # Mock Repository
    │   ├── test_student_app_service.py
    │   └── test_user_app_service.py
    ├── domain/            # Domain 层（核心业务）
    │   ├── test_entities/ # 实体测试
    │   └── test_value_objects/ # 值对象测试
    └── infrastructure/    # Infrastructure 层（数据访问）
        └── test_repositories/ # Repository 实现测试
```

## 测试统计

| 层级 | 测试数 | 说明 |
|------|--------|------|
| Domain | 100 | 实体、值对象、领域逻辑 |
| Application | 33 | 应用服务、用例编排 |
| Infrastructure | 55 | Repository、数据库访问 |
| Integration | 24 | API 集成测试（含 3 个冒烟测试）|
| **总计** | **212** | **全部通过** |

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
# 仅单元测试
pytest tests/unit -v

# 仅集成测试
pytest tests/integration -v

# 仅冒烟测试
pytest tests/integration/test_smoke.py -v
pytest -m smoke
```

### 3. 按模块运行

```bash
# Domain 层
pytest tests/unit/domain -v

# Application 层
pytest tests/unit/application -v

# Infrastructure 层
pytest tests/unit/infrastructure -v

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
pytest tests/ --cov=backend --cov-report=html

# 查看报告
open htmlcov/index.html
```

## 测试配置

### pytest.ini

```ini
[pytest]
testpaths = tests
asyncio_mode = strict
markers =
    smoke: 冒烟测试（核心业务流程）
    integration: 集成测试
    unit: 单元测试
```

### 环境要求

- Python 3.11+
- pytest 9.0+
- pytest-asyncio
- httpx (集成测试)
- 其他依赖见 `backend/requirements.txt`

## 系统测试步骤

系统测试是在完整部署环境下进行的端到端测试，验证整个系统是否满足需求规格。

### 环境准备

#### 1.1 检查服务状态

```bash
# 1. 检查 Redis
redis-cli ping
# 期望输出: PONG

# 2. 检查后端服务
curl http://localhost:8000/health
# 期望输出: {"status": "healthy", ...}

# 3. 检查前端服务
curl -I http://localhost:3000
# 期望输出: HTTP/1.1 200 OK
```

#### 1.2 准备测试数据

```bash
# 确保数据库中有基础数据
# 如果不存在 admin 用户，需要创建:
cd backend
conda activate student-manage
python << 'EOF'
from infrastructure.persistence.database import Database
from domain.entities.user import User, UserRole
from domain.value_objects.password import Password

db = Database()
with db.connection() as conn:
    # 检查 admin 是否存在
    cursor = conn.execute("SELECT 1 FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        # 创建 admin 用户
        admin = User(
            username="admin",
            name="系统管理员",
            password=Password.create_from_plain("admin123"),
            role=UserRole.ADMIN
        )
        conn.execute('''
            INSERT INTO users (username, password_hash, salt, name, role, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (admin.username, admin.password.hash_value, admin.password.salt,
              admin.name, admin.role.value, 1))
        print("✓ admin 用户已创建")
    else:
        print("✓ admin 用户已存在")
EOF
```

### 系统测试执行步骤

#### Step 1: 用户认证流程测试

| 步骤 | 操作 | 验证点 |
|-----|------|--------|
| 1.1 | 访问登录页 http://localhost:3000 | 页面正常加载，显示登录表单 |
| 1.2 | 输入错误密码登录 | 提示"用户名或密码错误" |
| 1.3 | 输入正确凭据登录 (admin/admin123) | 登录成功，跳转到管理界面 |
| 1.4 | 检查浏览器 Cookie | 存在 session cookie |
| 1.5 | 点击登出 | 返回登录页，清除 session |

#### Step 2: 学生管理流程测试

| 步骤 | 操作 | 验证点 |
|-----|------|--------|
| 2.1 | 以教师身份登录 | 登录成功 |
| 2.2 | 进入"学生管理"页面 | 显示学生列表 |
| 2.3 | 点击"添加学生" | 弹出添加表单 |
| 2.4 | 填写学号、姓名、班级，提交 | 学生添加到列表，默认分数 70 |
| 2.5 | 搜索学生 | 可按姓名/学号搜索到该学生 |
| 2.6 | 更新学生分数 (+10分) | 分数更新为 80，显示变更记录 |
| 2.7 | 删除学生 | 学生从列表中移除 |

#### Step 3: 签到功能测试

| 步骤 | 操作 | 验证点 |
|-----|------|--------|
| 3.1 | 教师开始课堂 | 点击"开始课堂"，选择班级 |
| 3.2 | 学生签到 | 输入学号签到成功 |
| 3.3 | 查看签到列表 | 显示已签到学生 |
| 3.4 | 重复签到 | 提示"今日已签到" |
| 3.5 | 结束课堂 | 签到功能关闭 |

#### Step 4: 用户管理流程测试（管理员）

| 步骤 | 操作 | 验证点 |
|-----|------|--------|
| 4.1 | 以 admin 登录 | 登录成功，显示管理菜单 |
| 4.2 | 进入"用户管理" | 显示用户列表 |
| 4.3 | 创建教师用户 | 填写用户名、密码、分配班级 |
| 4.4 | 新用户登录验证 | 可用新凭据登录 |
| 4.5 | 重置用户密码 | 密码重置成功 |
| 4.6 | 禁用用户 | 该用户无法登录 |
| 4.7 | 删除用户 | 用户从列表移除 |

#### Step 5: 数据持久化测试

| 步骤 | 操作 | 验证点 |
|-----|------|--------|
| 5.1 | 创建学生/用户 | 数据创建成功 |
| 5.2 | 重启后端服务 | 服务正常启动 |
| 5.3 | 重新登录 | 数据仍然存在 |

#### Step 6: 并发测试（可选）

```bash
# 使用 ab 或 locust 进行压力测试
# 安装: pip install locust

# 创建 locustfile.py
# 运行: locust -f locustfile.py --host=http://localhost:8000
```

### 系统测试验收标准

| 测试项 | 通过标准 |
|-------|---------|
| 功能完整性 | 所有核心功能（增删改查、登录、签到）正常工作 |
| 数据一致性 | 页面显示数据与数据库一致 |
| 权限控制 | 教师/管理员权限正确，越权操作被拒绝 |
| 性能 | 页面加载 < 3秒，API 响应 < 1秒 |
| 稳定性 | 连续运行 8 小时无崩溃 |
| 兼容性 | Chrome/Firefox/Edge 最新版本正常 |

### 系统测试检查清单

- [ ] 环境准备完成（Redis、后端、前端均已启动）
- [ ] admin 用户可正常登录
- [ ] 教师用户可正常登录
- [ ] 学生 CRUD 功能正常
- [ ] 签到功能正常（开始/签到/结束）
- [ ] 分数更新功能正常
- [ ] 用户管理功能正常（仅限管理员）
- [ ] 权限控制正确（教师无法访问管理功能）
- [ ] 数据持久化正常（重启后数据不丢失）
- [ ] 页面显示正常（无样式错乱）
- [ ] 无控制台报错
- [ ] 网络请求无 500 错误

### 系统测试失败处理

1. **服务无法启动**
   ```bash
   # 检查端口占用
   lsof -i :8000  # 后端
   lsof -i :3000  # 前端
   
   # 检查日志
   tail -f backend/logs/*.log
   ```

2. **数据库连接失败**
   ```bash
   # 检查数据库文件权限
   ls -la backend/data/*.db
   
   # 检查数据库完整性
   sqlite3 backend/data/student_manage.db "PRAGMA integrity_check;"
   ```

3. **前端页面白屏**
   ```bash
   # 检查前端控制台（F12）
   # 检查后端 CORS 配置
   # 检查 API 响应格式
   ```

---

## 测试类型说明

### 1. 单元测试（Unit Tests）

**位置**: `tests/unit/`

**特点**:
- 不依赖外部服务
- 使用 Mock 对象隔离依赖
- 执行速度快

**示例**:
```bash
# 测试值对象
pytest tests/unit/domain/test_value_objects/test_score.py -v

# 测试应用服务（Mock Repository）
pytest tests/unit/application/test_student_app_service.py -v
```

### 2. 集成测试（Integration Tests）

**位置**: `tests/integration/`

**特点**:
- 使用真实 FastAPI 应用
- 使用临时 SQLite 数据库
- 完整 HTTP 请求/响应流程

**示例**:
```bash
# 运行所有集成测试
pytest tests/integration/ -v

# 查看详细流程输出
pytest tests/integration/test_smoke.py -v -s
```

### 3. 冒烟测试（Smoke Tests）

**位置**: `tests/integration/test_smoke.py`

**特点**:
- 快速验证核心业务流程
- 不依赖外部服务启动
- 执行时间 < 3 秒

**运行**:
```bash
pytest tests/integration/test_smoke.py -v

# 或使用标记
pytest -m smoke -v
```

**覆盖流程**:
1. 管理员登录
2. 创建学生
3. 查询学生列表
4. 更新学生分数
5. 创建教师用户
6. 切换用户登录
7. 权限验证
8. 登出

## 数据库说明

### 单元测试
- 使用 Mock Repository，不涉及真实数据库

### 集成测试
- 使用临时 SQLite 文件数据库（`tempfile.mkstemp`）
- 每个测试会话创建一个独立数据库
- 测试结束后自动清理

### 测试数据
- 用户名使用 UUID 生成，避免唯一性冲突
- 测试前自动创建必要数据（用户、学生等）

## 常见问题

### Q1: 集成测试报错 "sqlite3.OperationalError: no such table"
**原因**: 数据库未正确初始化
**解决**: 检查 `conftest.py` 中的数据库初始化逻辑

### Q2: 测试用户冲突 "UNIQUE constraint failed: users.username"
**原因**: 多个测试使用相同用户名
**解决**: 已使用 UUID 生成随机用户名，如仍冲突检查测试是否共享数据库

### Q3: 集成测试很慢
**原因**: 每个测试都创建新的数据库
**优化**: 集成测试设计为 session 级别共享数据库，如需更快可使用单元测试

### Q4: 如何调试集成测试
```python
# 在测试中添加断点
import pytest

@pytest.mark.asyncio
async def test_example(client):
    response = await client.get("/api/students")
    print(response.json())  # 查看响应
    assert response.status_code == 200
```

## 添加新测试

### 添加单元测试

```python
# tests/unit/domain/test_value_objects/test_new_vo.py
import pytest
from domain.value_objects.new_vo import NewVO

def test_new_vo_creation():
    vo = NewVO(value=100)
    assert vo.value == 100
```

### 添加集成测试

```python
# tests/integration/test_new_api.py
import pytest
import uuid

@pytest.mark.asyncio
async def test_new_feature(client, test_user):
    # 登录
    await client.post("/api/login", json={...})
    
    # 测试新功能
    response = await client.get("/api/new-endpoint")
    assert response.status_code == 200
```

## CI/CD 集成

```yaml
# .github/workflows/test.yml 示例
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest pytest-asyncio httpx
      - name: Run tests
        run: pytest tests/ -v --tb=short
```

## 相关文档

- `../backend/CONFIG_GUIDE.md` - 后端配置指南
- `../TEST_PLAN.md` - 测试计划文档
- `../migrations/README.md` - 数据库迁移指南

## 维护者

如有问题，请联系开发团队。
