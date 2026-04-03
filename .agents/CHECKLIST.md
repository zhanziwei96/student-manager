# 执行前强制检查清单

> **警告**: 每次执行操作前，我必须显式勾选以下清单。用户看到未勾选时可随时打断要求重新确认。

---

## 通用操作检查清单

### 网络请求（curl）
- [ ] curl 命令已设置超时，避免长时间等待：
  - 使用 `--max-time 10` 或 `--connect-timeout 5`

### 服务状态检查（任何服务操作前）
- [ ] 后端状态：`curl -s --max-time 5 http://localhost:8000/api/v1/health`
- [ ] 前端状态：`curl -s --max-time 5 http://localhost:5173 > /dev/null && echo "前端运行中"`

### 禁止行为（强制）
- [ ] 禁止未经用户明确同意擅自修改功能或简化需求
- [ ] 禁止在未阅读完所有相关代码的情况下直接修复整改
- [ ] 禁止碰到问题后回退组件版本（应先尝试修复或报告）
- [ ] 禁止快速连续执行停止+启动命令
- [ ] 禁止在非虚拟环境的 python 环境下运行 python 命令
- [ ] 禁止在未验证的情况下认为操作成功
- [ ] 禁止假设数据库/服务路径

---

## 后端操作检查清单

### 执行任何 Python 命令前
- [ ] 已确认使用 `conda run -n student-manage` 或已激活环境 (`conda activate student-manage`)
- [ ] 已验证：`which python` 输出包含 `miniconda`

### 修改后端代码后（必须）
- [ ] 已查找相关单元测试：`tests/unit/test_<模块>.py` 或 `tests/unit/<模块>/test_*.py`
- [ ] 已查找相关集成测试：`tests/integration/test_<模块>_api*.py`
- [ ] 已检查测试是否覆盖修改的代码
- [ ] 已运行相关测试验证：`pytest tests/unit/test_<模块>.py -v`
- [ ] 如有测试失败，已补充或修复测试

### 涉及数据库操作前
- [ ] 已确认实际数据库路径：`python -c "from app.core.config import get_settings; print(get_settings().get_database_path())"`

### 服务重启前（必须）
- [ ] 已检查当前状态：`make status` 或 `curl -s --max-time 5 http://localhost:8000/api/v1/health`
- [ ] 如需重启：
  - [ ] 执行 `pkill -f "python main.py" 2>/dev/null || true`
  - [ ] **必须等待 3 秒**：`sleep 3`
  - [ ] 检查残留进程：`ps aux | grep "python.*main.py" | grep -v grep`
  - [ ] 如有残留，使用 `pkill -9 -f "python.*main.py"`
  - [ ] 在正确目录启动：`cd /home/yufeng/student-manager/backend`
  - [ ] 使用正确命令：`conda run -n student-manage ENV=production python main.py &`
  - [ ] **必须等待 5 秒**：`sleep 5`
  - [ ] **必须验证**：`curl -s --max-time 5 http://localhost:8000/api/v1/health`

### 代码规范检查
- [ ] JWT Claims 使用 `.get()` 方法，不使用 `["key"]`
- [ ] API 响应使用常量：`ApiResponseConst.SUCCESS`, `ApiResponseConst.DATA`, `ApiResponseConst.MESSAGE`
- [ ] 密码验证使用新接口：`verify_password()`, `hash_password()`（禁止旧接口）
- [ ] JWT 时区使用 `Asia/Shanghai`：`datetime.now(ZoneInfo("Asia/Shanghai"))`
- [ ] 限流返回 429 状态码（禁止 503）
- [ ] 环境变量格式使用双下划线：`DATABASE__PATH`（非单下划线）

### 错误排查顺序（强制）
1. [ ] 查看后端日志输出
2. [ ] 检查进程：`ps aux | grep python`
3. [ ] 验证配置：`python -c "from app.core.config import get_settings; print(...)"`
- [ ] **禁止在没有查看日志的情况下尝试修复**

---

## 前端操作检查清单

### 服务重启前（必须）
- [ ] 已检查当前状态：`curl -s --max-time 5 http://localhost:5173 > /dev/null && echo "前端运行中"`
- [ ] 如需重启：
  - [ ] 执行 `pkill -f "pnpm dev" 2>/dev/null || true`
  - [ ] **必须等待 2 秒**：`sleep 2`
  - [ ] 在正确目录启动：`cd /home/yufeng/student-manager/frontend-v3`
  - [ ] 使用正确命令：`pnpm dev &`
  - [ ] **必须等待 3 秒**：`sleep 3`
  - [ ] **必须验证**：`curl -s --max-time 5 http://localhost:5173 > /dev/null && echo "前端运行中"`

### 修改 Vue/TS 文件后（必须）
- [ ] 已评估是否需要创建新测试
- [ ] 已评估是否需要修改已有测试
- [ ] 已运行前端测试验证：`pnpm test:run`（在 frontend-v3 目录）

### Tailwind CSS v4 约束
- [ ] 自定义 `@theme` 时保留 `--spacing: 0.25rem` 基础单位
- [ ] 或使用 `@theme inline` 避免覆盖默认主题

### API 响应处理（强制）
- [ ] **禁止直接访问 `res.xxx`**，必须访问 `res.data.xxx`
- [ ] 错误示例：`res.user.role` → 正确：`res.data.user.role`

---

## 测试操作检查清单

### 运行测试前
- [ ] 已在项目根目录（`tests/` 目录外运行）

### 修改后端代码后（强制）
1. [ ] 查找相关单元测试文件：`tests/unit/test_<模块>.py` 或 `tests/unit/<模块>/test_*.py`
2. [ ] 查找相关集成测试文件：`tests/integration/test_<模块>_api*.py`
3. [ ] 查看测试文件，确认是否有对应的测试用例覆盖修改
4. [ ] 运行相关测试验证：`pytest tests/unit/test_<模块>.py -v`
5. [ ] 运行集成测试验证：`pytest tests/integration/test_<模块>_api*.py -v`
6. [ ] **如有失败，必须修复测试后再提交**（禁止删除测试用例）

### 修改 Vue/TS 代码后（强制）
- [ ] 根据当前测试内容评估：
  - [ ] 是否需要创建新测试？
  - [ ] 是否需要修改已有测试？
- [ ] 运行前端测试：`pnpm test:run`（在 frontend-v3 目录）

### 提交代码前
- [ ] 运行全部后端测试：`pytest tests/ -v`
- [ ] 运行全部前端测试：`pnpm test:run`
- [ ] 确认没有失败的测试

### 询问用户（必须）
修改/新增功能后，**必须**询问：
> "修改/新增功能已完成，是否需要运行测试？
> - 运行全部测试: `pytest tests/ -v`
> - 仅单元测试: `pytest tests/unit -v`
> - 仅集成测试: `pytest tests/integration -v`
> - 不需要测试"

---

## 使用说明

### 方案 1：用户主动要求
关键操作前，用户可直接说：
> "先过一遍检查清单再执行"

这会强制我回顾约束并逐项勾选。

### 方案 2：失败触发
当我犯错后，用户可要求我必须：
1. 重新阅读 ERRORS.md 和 CHECKLIST.md
2. 总结违反了哪些项
3. 得到用户确认后再继续

### 方案 3：置顶提醒
CLAUDE.md 顶部已放置简化版清单，我每次会话都能看到。

---

**最后更新**: 2026-04-03
**版本**: v1
