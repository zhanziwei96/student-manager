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
# 错误 - 修改了错误的数据库
sqlite3 ./data/student_manage.db "..."

# 正确 - 先确认实际路径
python -c "from infrastructure.config import get_settings; import os; print(os.path.abspath(get_settings().database.path))"
# 通常是: /home/yufeng/student-manager/backend/data/student_manage.db
```

### 3. 配置不生效
```python
# 修改配置后，清除缓存
import sys
for mod in list(sys.modules.keys()):
    if 'infrastructure.config' in mod:
        del sys.modules[mod]
```

---

## 配置类错误

### 4. 嵌套配置格式错误
```bash
# 错误
DB_PATH=xxx

# 正确 - 使用双下划线
DATABASE__PATH=./data/student_manage.db
RATE_LIMIT__MULTIPLIER=100
```

### 5. 环境变量未设置
```bash
# 必须在导入前设置
export ENV=testing
python main.py

# 验证
python -c "from infrastructure.config import get_settings; print(get_settings().env)"
```

---

## 开发类错误

### 6. 混淆 UI 框架
- 项目使用 **Naive UI**，不是 Element Plus
- `el-button` → `n-button`
- `el-input` → `n-input`

### 7. DDD 架构违规
- Domain 层不能导入 Infrastructure 层
- 正确: Domain 层硬编码常量
- 错误: Domain 层使用 `ScoreConfig`

### 8. 使用 print 而不是 logging
**错误**: 直接使用 `print()` 输出日志信息

```python
# ❌ 错误
print(f"数据库路径: {db_path}")
print("服务启动")
```

**正确**: 使用项目统一的日志模块

```python
# ✅ 正确
from infrastructure.logging import logger
logger.info(f"数据库路径: {db_path}")

# 或使用便捷函数
from infrastructure.logging import info, error, warning, debug
info("服务启动")
error("数据库连接失败")
warning("配置未找到，使用默认值")
```

**日志文件位置**: `backend/logs/YYYY-MM-DD.log`

---

## 测试类错误

### 9. 测试数据库冲突
- 集成测试使用临时文件数据库
- 用户名使用 UUID 避免冲突

### 10. 测试路径问题
```bash
# 在项目根目录运行
pytest tests/ -v

# 不要 cd 到 tests 目录
```

---

## 检查清单

执行命令前检查:
- [ ] Conda 环境已激活 (`which python` 显示 miniconda 路径)
- [ ] 服务已启动 (`curl http://localhost:8000/health`)
- [ ] 数据库路径正确

遇到错误时:
- [ ] 查看日志 `tail -20 backend/logs/*.log`
- [ ] 检查进程 `ps aux | grep python`
- [ ] 验证配置 `python -c "from config import get_settings; print(...)"`
