# 执行约束清单

> **警告**: 本文件中的约束是我每次处理请求前**必须**回顾的内容。
> 不遵循这些约束会导致重复犯错。

---

## 通用禁令 (Universal Prohibitions)

以下行为**绝对禁止**：

| # | 禁令 | 违反后果 |
|---|------|----------|
| 1 | ❌ 不要在未检查服务状态的情况下重启服务 | 重复部署，端口冲突 |
| 2 | ❌ 不要快速连续执行停止+启动命令 | 残留进程导致启动失败 |
| 3 | ❌ 不要假设数据库/服务路径 | 操作错误的文件 |
| 4 | ❌ 不要在未验证的情况下认为操作成功 | 隐藏错误 |
| 6 | ❌ **禁止在碰到问题后回退组件版本** | 掩盖问题，重复犯错 |
| 7 | ❌ **禁止在非虚拟环境的 python 环境下运行 python 命令** | 模块找不到，环境混乱 |
| 8 | ❌ **禁止修改后端代码后不检查/更新对应测试** | 测试失效，覆盖率下降，隐藏回归错误 |
| 9 | ❌ **禁止在未阅读完所有相关代码的情况下直接修复整改** | 破坏项目结构一致性，重复造轮子，引入不一致的实现 |

---

## 执行前强制检查清单

每次执行命令前，按顺序检查：

```bash
# 1. 环境检查 (必须)
which python  # 确认是 miniconda 路径

# 2. 服务状态检查 (必须)
curl -s http://localhost:8000/api/health  # 后端是否已运行？
curl -s http://localhost:5173 > /dev/null && echo "前端运行中"  # 前端是否已运行？

# 3. 数据库路径确认 (涉及 DB 操作时必须)
python -c "from app.core.config import get_settings; print(get_settings().get_database_path())"
```

**决策逻辑**:
- 如果服务已运行 → 不需要重启
- 如果服务未运行 → 按重启流程执行（见下方）

---

## 服务重启强制流程

**禁止**直接执行 `python main.py` 或 `pnpm dev`。

必须按以下步骤：

```bash
# 后端重启
pkill -f "python main.py" 2>/dev/null || true
sleep 3  # 必须等待！
ps aux | grep "python.*main.py" | grep -v grep  # 检查残留
# 如有残留: pkill -9 -f "python.*main.py"
cd /home/yufeng/student-manager/backend
conda run -n student-manage ENV=production python main.py &
sleep 5
curl -s http://localhost:8000/api/health  # 必须验证！

# 前端重启
pkill -f "pnpm dev" 2>/dev/null || true
sleep 2
cd /home/yufeng/student-manager/frontend-v3
pnpm dev &
sleep 3
curl -s http://localhost:5173 > /dev/null && echo "前端运行中"  # 必须验证！
```

---

## 环境配置约束

### Conda 环境 (强制)
- **所有 Python 命令**必须在 `student-manage` 环境中执行
- **检查命令**: `which python` 应包含 `miniconda`
- **激活命令**: `conda activate student-manage`

### 环境变量格式 (强制)
```bash
# 正确 - 使用双下划线
DATABASE__PATH=./data/class_system.db
SECURITY__MAX_LOGIN_FAILURES=10

# 错误 - 单下划线会被忽略
DATABASE_PATH=xxx
```

### 环境变量设置时机 (强制)
必须在导入应用代码**之前**设置：
```bash
# 正确
export ENV=testing
python main.py

# 错误 - 在 Python 内设置不生效
python -c "import os; os.environ['ENV'] = 'testing'; from app.core.config import get_settings"
```

---

## 前端开发约束

### Tailwind CSS v4 (强制)
- 自定义 `@theme` 会**完全覆盖**默认主题
- 必须保留 `--spacing: 0.25rem` 基础单位
- **正确做法**: 使用 `@theme inline` 或显式定义 `--spacing`

```css
/* 正确 */
@theme inline {
  --color-primary: #6366f1;
}

/* 或 */
@theme {
  --spacing: 0.25rem;  /* 必须保留！ */
  --color-primary: #6366f1;
}
```

### API 响应处理 (强制)
- 后端返回格式: `{success: true, data: {...}, message: "..."}`
- **禁止**直接访问 `res.user`，必须访问 `res.data`

```javascript
// 错误
res.user.role

// 正确
res.data.role
```

---

## 后端开发约束

### JWT Claims (强制)
Token 中包含以下字段：
```python
{
    "sub": "1",           # 用户ID
    "username": "admin",  # 用户名
    "name": "管理员",      # 显示名称
    "role": "admin",      # 角色
    "is_admin": true,     # 是否管理员
}
```

**禁止假设字段存在** - 始终使用 `.get()` 方法：
```python
user_id = user.get("sub")  # 正确
user_id = user["sub"]      # 可能报错
```

### API 响应常量 (强制)
**禁止**硬编码响应字段名，必须使用常量：
```python
from app.models.constants import ApiResponseConst, MessageConst

# 正确
return {
    ApiResponseConst.SUCCESS: True,
    ApiResponseConst.MESSAGE: MessageConst.USER_CREATED,
    ApiResponseConst.DATA: user.model_dump()
}

# 错误
return {"success": True, "message": "用户创建成功"}
```

---

## 测试执行约束

### 运行路径 (强制)
```bash
# 正确 - 在项目根目录运行
pytest tests/ -v

# 错误 - 不要 cd 到 tests 目录
```

### 修改后流程 (强制)
修改或新增功能后，**必须**询问用户是否需要运行测试：

> "修改/新增功能已完成，是否需要运行测试？
> - 运行全部测试: pytest tests/ -v
> - 仅单元测试: pytest tests/unit -v
> - 仅集成测试: pytest tests/integration -v
> - 不需要测试"

**禁止**擅自决定不运行测试。

### 修改后端代码后检查清单 (强制)
修改后端代码后，**必须**执行以下检查：

```bash
# 1. 查找相关测试文件
# 单元测试: tests/unit/test_<模块>.py 或 tests/unit/<模块>/test_*.py
# 集成测试: tests/integration/test_<模块>_api*.py

# 2. 检查测试是否覆盖修改的代码
# 查看测试文件，确认是否有对应的测试用例

# 3. 运行相关测试验证
pytest tests/unit/test_<修改模块>.py -v
pytest tests/integration/test_<修改模块>_api*.py -v

# 4. 如果测试不存在或失效，必须补充或修复
```

**示例流程**:
```bash
# 修改了 backend/app/crud/student.py
# 1. 检查单元测试
ls tests/unit/crud/test_student.py
# 2. 检查集成测试  
ls tests/integration/test_students_api*.py
# 3. 运行相关测试
pytest tests/unit/crud/test_student.py tests/integration/test_students_api_enhanced.py -v
# 4. 如有失败，修复测试后再提交
```

---

## 错误排查约束

遇到问题时，**按顺序**执行：

1. **查看后端日志输出**（不是猜测）
2. **检查进程**: `ps aux | grep python`
3. **验证配置**: `python -c "from app.core.config import get_settings; print(get_settings().app.env)"`

**禁止**在没有查看日志的情况下尝试修复。

---

## 数据库操作约束

### 路径确认 (强制)
执行任何数据库操作前，**必须**确认实际路径：
```bash
python -c "from app.core.config import get_settings; print(get_settings().get_database_path())"
```

通常是: `/home/yufeng/student-manager/backend/data/class_system.db`

### 集成测试隔离 (强制)
集成测试使用内存数据库，**禁止**连接到生产数据库。

---

## 纠错记录

以下是我曾经犯过的错误，需要时刻警惕：

| 日期 | 错误 | 约束 |
|------|------|------|
| - | 未检查服务状态就重启 | 执行前必须检查 health |
| - | 快速停止+启动导致残留进程 | 必须 sleep 3 秒 |
| - | 未激活 Conda 环境 | 必须检查 which python |
| - | Tailwind v4 覆盖默认主题 | 必须保留 --spacing |
| - | 访问 res.user 而非 res.data | 必须使用 res.data.xxx |
| - | 修改测试文件逻辑 | 禁止修改测试 |
| - | 未验证就确认成功 | 必须用 curl 验证 |
| 2026-03-23 | 碰到问题回退组件版本 | **禁止回退版本**，应先尝试修复或报告 |
| 2026-03-24 | 使用系统自带 python 运行脚本 | **必须激活 Conda 环境**，使用 `conda run -n student-manage python` 或先 `conda activate student-manage` |
| 2026-03-25 | 修改后端代码后未检查测试 | **禁止修改后端代码后不检查测试文件**，必须进行测试适配或补充 |
| 2026-03-26 | 未阅读完相关代码就修复整改 | **禁止在未阅读完所有相关代码的情况下直接修复整改**，必须先了解项目结构和可复用函数

---

**最后更新**: 2026-03-26
**版本**: v2 (约束清单格式)
