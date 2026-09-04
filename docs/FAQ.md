# ClassHub 常见问题解答 (FAQ)

---

**文档版本**: v1.1  
**最后更新**: 2026-04-13  
**适用版本**: v3.0.0+  
**状态**: 已同步代码

---

---

## 目录

1. [环境配置问题](#环境配置问题)
2. [服务启动问题](#服务启动问题)
3. [数据库问题](#数据库问题)
4. [测试问题](#测试问题)
5. [API使用问题](#api使用问题)
6. [前端开发问题](#前端开发问题)

---

## 环境配置问题

### Q1: 运行 Python 命令时提示 "ModuleNotFoundError: No module named 'app'"

**原因**: 没有激活 Conda 环境，使用了系统 Python

**解决**:
```bash
# 方法1: 激活环境后运行
conda activate student-manage
python main.py

# 方法2: 使用 conda run
conda run -n student-manage python main.py

# 验证当前 Python 路径
which python  # 应输出包含 miniconda 的路径
```

---

### Q2: 如何确认当前使用的是正确的 Python 环境？

```bash
# 检查 Python 路径
which python
# 期望输出: /home/yufeng/miniconda3/envs/student-manage/bin/python

# 检查 Python 版本
python --version
# 期望输出: Python 3.11.x

# 检查已安装的包
conda list | grep fastapi
```

---

### Q3: 前端依赖安装失败或报错

**解决**:
```bash
cd frontend-v3

# 清理后重新安装
rm -rf node_modules pnpm-lock.yaml
pnpm install

# 如果仍然失败，检查 pnpm 版本
pnpm --version
# 期望: 8.x 或更高
```

---

## 服务启动问题

### Q4: 启动后端时提示 "Address already in use"

**原因**: 端口 8000 被占用

**解决**:
```bash
# 查找占用端口的进程
lsof -i :8000

# 停止占用进程
pkill -f "python main.py"
# 或
kill -9 <PID>

# 等待3秒后重新启动
sleep 3
conda run -n student-manage python main.py
```

---

### Q5: 服务启动后无法访问，curl 无响应

**排查步骤**:
```bash
# 1. 检查进程是否存在
ps aux | grep "python.*main.py"

# 2. 检查端口监听
lsof -i :8000

# 3. 查看后端日志
tail -20 backend/logs/app.log

# 4. 检查配置文件
python -c "from app.core.config import get_settings; print(get_settings().app.env)"

# 5. 确认数据库路径正确
python -c "from app.core.config import get_settings; print(get_settings().get_database_path())"
```

---

### Q6: 如何正确重启服务？

**完整流程**:
```bash
# 1. 检查当前状态
curl -s --max-time 5 http://localhost:8000/api/v1/health

# 2. 停止服务
pkill -f "python main.py"
sleep 3  # 必须等待！

# 3. 检查残留
ps aux | grep "python.*main.py" | grep -v grep

# 4. 如有残留，强制结束
pkill -9 -f "python.*main.py"

# 5. 启动服务
cd /home/yufeng/student-manager/backend
conda run -n student-manage ENV=production python main.py &
sleep 5

# 6. 验证启动
curl -s --max-time 5 http://localhost:8000/api/v1/health
```

---

## 数据库问题

### Q7: 数据库文件在哪里？

```bash
# 查看配置的数据库路径
python -c "from app.core.config import get_settings; print(get_settings().get_database_path())"

# 默认路径
backend/app/data/class_system.db
```

---

### Q8: 如何备份数据库？

```bash
# 手动备份
cp backend/app/data/class_system.db backup/class_system_$(date +%Y%m%d).db

# 或使用备份脚本
./backup/backup-data.sh
```

---

### Q9: 如何查看数据库表结构？

数据库使用 PostgreSQL（开发=本地安装，生产=Docker 容器）：

```bash
# 本地开发库（backend/.env 的 DATABASE__URL）
psql postgresql://yufeng:yufeng@localhost:5432/classhub

# 生产环境（Docker 容器）
docker exec -it classhub-postgres psql -U classhub -d classhub

# 查看所有表
\dt

# 查看表结构
\d users
\d students

# 查看数据量
SELECT COUNT(*) FROM students;
```

---

### Q10: 数据库迁移失败怎么办？

**解决**:
```bash
# 1. 停止后端服务
pkill -f "python main.py"

# 2. 恢复备份
mv backend/app/data/class_system.db backend/app/data/class_system.db.failed
mv backend/app/data/class_system.db.backup.YYYYMMDD backend/app/data/class_system.db

# 3. 重新启动后端
conda run -n student-manage python main.py

# 4. 检查迁移脚本
# 确保使用正确的迁移脚本顺序，参见 migrations/README.md
```

---

## 测试问题

### Q11: 运行测试时提示 "ImportError: cannot import name 'Literal'"

**原因**: Python 版本过低

**解决**:
```bash
# 检查 Python 版本
python --version
# 必须 >= 3.11

# 切换到正确的 Conda 环境
conda activate student-manage
```

---

### Q12: 测试提示 "ModuleNotFoundError: No module named 'app'"

**原因**: 运行路径不正确

**解决**:
```bash
# ✅ 正确 - 在项目根目录运行
pytest tests/ -v

# ❌ 错误 - 不要在 tests 目录内运行
cd tests
pytest -v  # 这会报错！
```

---

### Q13: 如何运行特定测试文件？

```bash
# 后端单元测试
pytest tests/unit/test_jwt.py -v
pytest tests/unit/crud/test_student.py -v

# 后端集成测试
pytest tests/integration/test_students_api_enhanced.py -v

# 前端测试
cd frontend-v3
npx vitest run test/components/Toast.spec.ts
```

---

### Q14: 测试失败时如何调试？

**后端测试**:
```bash
# 详细错误输出
pytest tests/unit/test_xxx.py -v --tb=long

# 进入调试模式
pytest tests/unit/test_xxx.py -v --pdb

# 打印调试信息
pytest tests/unit/test_xxx.py -v -s
```

**前端测试**:
```bash
cd frontend-v3

# 详细输出
npx vitest run --reporter=verbose

# UI 模式
npx vitest --ui

# 调试模式
npx vitest --inspect-brk
```

---

## API使用问题

### Q15: API 返回格式是什么？

```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功"
}
```

**注意**: 前端必须通过 `res.data` 访问数据，不能直接访问 `res.xxx`。

```typescript
// ❌ 错误
const user = res.user;

// ✅ 正确
const user = res.data.user;
```

---

### Q16: 登录接口返回 429 是什么意思？

**含义**: 请求过于频繁，被限流保护拦截

**默认限流配置**:
- 登录: 5次/分钟
- 签到: 10次/分钟
- 分数更新: 10次/分钟

**解决**: 等待1分钟后重试，或检查是否有循环调用

---

### Q17: JWT Token 在哪里？如何查看？

Token 存储在 HttpOnly Cookie 中，无法通过 JavaScript 直接访问。

后端可以通过以下方式查看：
```python
from fastapi import Request

@app.get("/debug/token")
def debug_token(request: Request):
    token = request.cookies.get("access_token")
    return {"token": token}
```

---

### Q18: 如何测试 API 是否正常工作？

```bash
# 健康检查
curl http://localhost:8000/api/v1/health

# 登录测试
curl -X POST http://localhost:8000/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123","role":"admin"}'

# 获取统计信息（需要登录后的 Cookie）
curl http://localhost:8000/api/v1/stats \
  -H "Cookie: access_token=YOUR_TOKEN_HERE"
```

---

## 前端开发问题

### Q19: 修改代码后样式不生效？

**解决**:
```bash
cd frontend-v3

# 重启开发服务器
pkill -f "pnpm dev"
pnpm dev

# 或强制刷新浏览器缓存
Ctrl + Shift + R  # Windows/Linux
Cmd + Shift + R   # Mac
```

---

### Q20: Tailwind CSS 样式不生效或报错？

**可能原因**:
1. 使用了 `@theme` 但没有保留 `--spacing`

**解决**:
```css
/* ✅ 正确 */
@theme inline {
  --color-primary: #6366f1;
}

/* 或 */
@theme {
  --spacing: 0.25rem;  /* 必须保留！ */
  --color-primary: #6366f1;
}
```

---

### Q21: 如何添加新的 API 调用？

**步骤**:
1. 在 `frontend-v3/src/api/` 创建或修改对应模块
2. 使用 `ofetch` 进行 HTTP 请求
3. 记得处理 `res.data` 格式

```typescript
// frontend-v3/src/api/student.ts
import { http } from '@/lib/api'

export async function getStudents() {
  const res = await http.get('/students')
  return res.data  // ✅ 注意这里
}
```

---

### Q22: 前端如何调试 API 请求？

**方法1**: 浏览器开发者工具
- F12 打开开发者工具
- Network 标签页查看请求/响应

**方法2**: 添加日志
```typescript
const response = await api.getStudents()
console.log('API Response:', response)  // 检查结构
console.log('Data:', response.data)      // 确认数据位置
```

---

## 其他问题

### Q23: 忘记管理员密码怎么办？

```bash
# 进入后端目录
cd backend

# 激活环境
conda activate student-manage

# 使用 Python 脚本重置密码
python -c "
from app.core.db import get_session
from app.crud.user import get_user_by_username
from app.core.security import hash_password
session = next(get_session())
user = get_user_by_username(session, 'admin')
user.password_hash = hash_password('new_password')
session.commit()
print('密码已重置')
"
```

---

### Q24: 如何查看后端日志？

```bash
# 实时查看日志
tail -f backend/logs/app.log

# 查看最新100行
tail -100 backend/logs/app.log

# 搜索特定错误
grep "ERROR" backend/logs/app.log
```

---

### Q25: 系统默认账号是什么？

| 角色 | 用户名 | 密码 | 说明 |
|------|--------|------|------|
| 管理员 | admin | admin123 | 系统管理员 |
| 教师 | zhanziwei | zha123 | 示例教师账号 |
| 学生 | 学号 | 学号 | 学号作为账号和密码 |

**注意**: 首次登录后请立即修改默认密码。教师账号遵循"姓名拼音首字母+123"的规则。

---

## 问题反馈

如果以上解答无法解决您的问题：

1. 查看 [README.md](../README.md) 了解项目概况
2. 查看 [GETTING_STARTED.md](../GETTING_STARTED.md) 获取详细环境搭建和故障排查
3. 查看 [docs/DOCUMENTATION_MAP.md](./DOCUMENTATION_MAP.md) 浏览完整文档导航
4. 查看 `.agents/ERRORS.md` 了解约束清单和纠错记录
5. 检查后端日志: `backend/logs/app.log`
6. 运行测试确认环境: `pytest tests/integration/test_smoke.py -v`

---

**文档版本**: v1.1
**最后更新**: 2026-04-13
