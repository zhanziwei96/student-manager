# 常见错误速查

## 环境类错误

### 1. 未激活 Conda 环境
```bash
# 错误
python -m pytest tests/  # 使用系统 Python

# 正确
conda activate student-manage
python -m pytest tests/
```

### 2. 数据库路径混淆
```bash
# 正确 - 先确认实际路径
python -c "from app.core.config import get_settings; print(get_settings().get_database_path())"
# 通常是: /home/yufeng/student-manager/backend/data/class_system.db
```

---

## 配置类错误

### 3. 嵌套配置格式错误
```bash
# 错误
DATABASE_PATH=xxx

# 正确 - 使用双下划线
DATABASE__PATH=./data/class_system.db
SECURITY__MAX_LOGIN_FAILURES=10
```

### 4. 环境变量未设置
```bash
# 必须在导入前设置
export ENV=testing
python main.py

# 验证
python -c "from app.core.config import get_settings; print(get_settings().app.env)"
```

---

## 开发类错误

### 5. 混淆 UI 框架
- 项目使用 **Naive UI**，不是 Element Plus
- `el-button` → `n-button`
- `el-input` → `n-input`

### 6. 魔法字符串
使用常量类避免拼写错误：

```python
from app.models.constants import (
    UserRoleConst,      # ADMIN, TEACHER, STUDENT
    SessionKeyConst,    # USER_ID, USERNAME, ROLE, IS_ADMIN
    ApiResponseConst,   # SUCCESS, DATA, MESSAGE
)

# 正确
role = UserRoleConst.ADMIN
user_id = request.session.get(SessionKeyConst.USER_ID)
```

### 7. API 响应格式
使用常量返回统一响应：

```python
from app.models.constants import ApiResponseConst, MessageConst

return {
    ApiResponseConst.SUCCESS: True,
    ApiResponseConst.MESSAGE: MessageConst.USER_CREATED,
    ApiResponseConst.DATA: user.model_dump()
}
```

---

## 前端问题

### 8. API 响应数据访问错误

**问题**: 登录成功后 UI 仍显示"未登录"

**原因**: 后端返回 `{success: true, data: {...}}`，但前端代码访问了 `res.user`

**错误代码**:
```javascript
// Login.vue
if (res.user.role !== form.role) {  // ❌ 应该是 res.data.role
userStore.setUser(res.user.id, ...)  // ❌ 应该是 res.data.xxx
```

**正确代码**:
```javascript
if (res.data.role !== form.role) {
userStore.setUser(res.data.id, res.data.username, res.data.name, res.data.role)
```

---

### 9. 登录 401 错误显示样式问题（后端待修复）

**问题**: 登录 401 错误显示 "Request failed with status code 401" 而不是 Naive UI 风格提示

**原因**: 后端 `login.py` 中 `raise HTTPException` 直接抛出的错误没有走 `http_exception_handler` 统一转换格式，返回的是 FastAPI 默认的 `{detail: "..."}` 格式，而非项目统一的 `{success: false, message: "..."}`

**影响范围**: 
- 登录接口 401 错误
- 登录接口 403 错误（账号锁定/禁用）

**后端修复方案**: 
需要在 `backend/app/api/routes/login.py` 中统一返回格式，例如：
```python
# 而不是 raise HTTPException(status_code=401, detail='用户名或密码错误')
return {
    ApiResponseConst.SUCCESS: False,
    ApiResponseConst.MESSAGE: '用户名或密码错误'
}
```

**前端暂不处理**，等待后端接口统一

---

### 10. API 响应格式说明

**后端统一格式**:
```json
// 成功 (HTTP 2xx)
{"success": true, "data": {...}, "message": "..."}

// 错误 (HTTP 4xx/5xx)
{"success": false, "message": "错误信息"}
```

**前端处理规范**:
- 成功响应: 检查 `res.success`，数据在 `res.data`，消息在 `res.message`
- 错误响应: 错误信息在 `error.response.data?.message`

---

## 测试类错误

### 10. 测试路径问题
```bash
# 在项目根目录运行
pytest tests/ -v

# 不要 cd 到 tests 目录
```

### 11. 集成测试数据库
集成测试使用内存数据库，与生产数据库隔离。

---

## 检查清单

执行命令前检查:
- [ ] Conda 环境已激活 (`which python` 显示 miniconda 路径)
- [ ] 服务已启动 (`curl http://localhost:8000/api/health`)
- [ ] 数据库路径正确

遇到错误时:
- [ ] 查看后端输出日志
- [ ] 检查进程 `ps aux | grep python`
- [ ] 验证配置 `python -c "from app.core.config import get_settings; print(get_settings().app.env)"`

---

## 重启服务正确步骤

### 后端服务重启

```bash
# 1. 停止服务
pkill -f "python main.py" 2>/dev/null || true

# 2. 等待几秒确保完全停止（重要！）
sleep 3

# 3. 检查是否还有残留进程
ps aux | grep "python.*main.py" | grep -v grep

# 4. 如有残留，强制终止
pkill -9 -f "python.*main.py" 2>/dev/null || true
sleep 2

# 5. 启动服务（生产环境）
cd /home/yufeng/student-manager/backend
conda run -n student-manage ENV=production python main.py &

# 6. 等待几秒后验证
sleep 5
curl -s http://localhost:8000/api/health
```

### 前端服务重启

```bash
# 1. 停止服务
pkill -f "pnpm dev" 2>/dev/null || true

# 2. 等待几秒
sleep 2

# 3. 启动服务
cd /home/yufeng/student-manager/frontend
pnpm dev &

# 4. 验证
curl -s http://localhost:3000 > /dev/null && echo "前端运行中"
```

**关键要点**:
- 必须等待几秒确保进程完全停止后再启动
- 不要连续快速执行停止和启动命令
- 启动后必须验证健康检查接口再确认成功
