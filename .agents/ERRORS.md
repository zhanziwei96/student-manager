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

### 6. JWT Claims 使用
JWT Token 中包含的字段（claims）：

```python
# JWT Payload 结构
{
    "sub": "1",           # 用户ID
    "username": "admin",  # 用户名
    "name": "管理员",      # 显示名称
    "role": "admin",      # 角色: admin/teacher/student
    "is_admin": true,     # 是否管理员
    "exp": 1774265683     # 过期时间
}

# 从请求中获取用户信息
from app.core.jwt import get_current_user

@app.get("/api/me")
async def get_me(user: dict = Depends(get_current_user)):
    user_id = user.get("sub")
    role = user.get("role")
    is_admin = user.get("is_admin")
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
