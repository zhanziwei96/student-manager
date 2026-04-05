# ClassHub 贡献者指南

---

**文档版本**: v1.0  
**最后更新**: 2026-04-05  
**适用版本**: v3.0.0+  
**状态**: ✅ 已同步代码

---

## 欢迎

感谢你对 ClassHub 项目的关注！本指南将帮助你了解如何参与项目贡献。

## 贡献方式

### 1. 报告问题 (Bug Report)

发现 bug 或有功能建议？请通过 Issue 提交：

1. 检查是否已有相关 Issue
2. 使用对应的 Issue 模板
3. 提供详细的环境信息和复现步骤

### 2. 提交代码 (Pull Request)

想要提交代码修复或新功能？请遵循以下流程：

#### 准备工作

```bash
# 1. Fork 项目到你的账号
# 2. 克隆你的 Fork
git clone https://github.com/YOUR_USERNAME/student-manager.git
cd student-manager

# 3. 添加上游仓库
git remote add upstream https://github.com/ORIGINAL_OWNER/student-manager.git

# 4. 创建功能分支
git checkout -b feature/your-feature-name
```

#### 开发流程

```bash
# 1. 同步上游代码
git fetch upstream
git rebase upstream/main

# 2. 开发你的功能
# ... 编写代码 ...

# 3. 运行测试
pytest tests/ -v                    # 后端测试
cd frontend-v3 && pnpm test:run     # 前端测试

# 4. 提交代码
git add .
git commit -m "feat: 添加新功能描述"
git push origin feature/your-feature-name
```

#### 提交规范

**Commit Message 格式**:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type 类型**:

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | 修复 bug |
| `docs` | 文档更新 |
| `style` | 代码格式（不影响功能） |
| `refactor` | 重构 |
| `test` | 测试相关 |
| `chore` | 构建/工具相关 |

**示例**:

```bash
feat(auth): 添加 JWT Token 刷新机制

- 实现 /api/v1/refresh-token 接口
- 添加 Token 过期自动刷新逻辑
- 更新前端 axios 拦截器

Closes #123
```

### 3. 改进文档

文档贡献同样重要：

- 修正错别字或表述不清的地方
- 补充示例代码
- 更新过时的截图或说明
- 翻译文档（如需要）

## 开发规范

### 代码风格

#### Python (后端)

- 遵循 PEP 8 规范
- 使用类型注解
- 最大行长度 100 字符

```python
# ✅ 正确
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

def update_student_score(
    session: Session,
    student_id: int,
    score_change: float,
    changed_by: int
) -> Student:
    """更新学生分数"""
    pass

# ❌ 错误
from datetime import *

def update_student_score(session, student_id, score_change, changed_by):
    pass
```

#### TypeScript/Vue (前端)

- 使用 Composition API + `<script setup>`
- 组件名使用 PascalCase
- Props 使用类型定义

```vue
<script setup lang="ts">
// ✅ 正确
interface Props {
  title: string
  visible: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
}>()

// ❌ 错误
const props = defineProps(['title', 'visible'])
</script>
```

### 测试要求

#### 后端测试

修改后端代码后必须检查并更新测试：

```bash
# 1. 查找相关测试文件
# 单元测试: tests/unit/test_<模块>.py
# 集成测试: tests/integration/test_<模块>_api*.py

# 2. 运行相关测试
pytest tests/unit/test_<模块>.py -v
pytest tests/integration/test_<模块>_api*.py -v

# 3. 确保测试通过
pytest tests/ -v
```

#### 前端测试

```bash
cd frontend-v3

# 运行测试
pnpm test:run

# 生成覆盖率报告
npx vitest run --coverage
```

### API 设计规范

#### 响应格式

使用统一响应格式：

```python
from app.models.constants import ApiResponseConst, MessageConst

# ✅ 正确
return {
    ApiResponseConst.SUCCESS: True,
    ApiResponseConst.DATA: data,
    ApiResponseConst.MESSAGE: MessageConst.OPERATION_SUCCESS
}

# ❌ 错误
return {"success": True, "data": data}
```

#### 错误处理

```python
from fastapi import HTTPException

# ✅ 正确
raise HTTPException(status_code=400, detail="参数错误")

# ❌ 错误
return {"error": "参数错误"}
```

## 分支管理

### 分支命名规范

```
feature/<功能描述>      # 新功能
fix/<bug描述>           # Bug修复
docs/<文档描述>         # 文档更新
refactor/<重构描述>     # 代码重构
test/<测试描述>         # 测试相关
chore/<工具描述>        # 构建/工具
```

### 示例

```bash
feature/student-import-excel
fix/login-rate-limit
docs/api-examples
refactor/split-user-service
```

## PR 提交规范

### PR 标题格式

```
[<type>] <简短描述>
```

**示例**:

```
[feat] 添加学生 Excel 批量导入功能
[fix] 修复登录限流状态码错误
[docs] 更新 API 使用示例
```

### PR 描述模板

```markdown
## 变更说明
简要描述本次变更的内容

## 变更类型
- [ ] 新功能
- [ ] Bug修复
- [ ] 文档更新
- [ ] 代码重构
- [ ] 性能优化
- [ ] 测试相关

## 测试情况
- [ ] 本地测试通过
- [ ] 新增测试用例
- [ ] 更新现有测试

## 检查清单
- [ ] 代码遵循项目规范
- [ ] 测试全部通过
- [ ] 文档已更新
- [ ] Commit 信息规范

## 相关 Issue
Fixes #123
Closes #456
```

## 代码审查流程

### 审查 checklist

- [ ] 代码逻辑正确
- [ ] 测试覆盖充分
- [ ] 文档已更新
- [ ] 无安全漏洞
- [ ] 性能影响评估
- [ ] 向后兼容性

### 审查反馈处理

1. 认真对待每条审查意见
2. 如有异议，礼貌沟通说明
3. 修改后及时更新 PR
4. 解决所有评论后请求重新审查

## 发布流程

### 版本号规范

遵循 [语义化版本](https://semver.org/lang/zh-CN/)：

```
主版本号.次版本号.修订号
```

- **主版本号**: 不兼容的 API 修改
- **次版本号**: 向下兼容的功能新增
- **修订号**: 向下兼容的问题修复

### 发布检查清单

- [ ] 所有测试通过
- [ ] 文档已更新
- [ ] CHANGELOG.md 已更新
- [ ] 版本号已更新
- [ ] Tag 已创建
- [ ] Release Notes 已编写

## 安全规范

### 敏感信息

- 不要将密钥、密码提交到代码仓库
- 使用环境变量管理敏感配置
- 定期轮换生产环境密钥

### 代码安全

- 防范 SQL 注入（使用参数化查询）
- 防范 XSS 攻击（输出转义）
- 防范 CSRF 攻击（使用 Token）
- 文件上传安全检查

## 社区规范

### 行为准则

- 尊重所有参与者
- 接受建设性批评
- 关注对社区最有利的事情
- 展现同理心

### 沟通渠道

- Issue: 功能讨论、Bug 报告
- PR: 代码审查、技术讨论
- Discussions: 一般性讨论

## 开发资源

### 必读文档

1. [CLAUDE.md](./CLAUDE.md) - 开发规范和约束
2. [backend/README.md](./backend/README.md) - 后端架构
3. [frontend-v3/docs/ARCHITECTURE.md](./frontend-v3/docs/ARCHITECTURE.md) - 前端架构
4. [docs/API_CHANGELOG.md](./docs/API_CHANGELOG.md) - API 变更记录

### 常用命令

```bash
# 启动开发环境
make dev-backend    # 终端1
make dev-frontend   # 终端2

# 运行测试
pytest tests/ -v
cd frontend-v3 && pnpm test:run

# 代码检查
cd frontend-v3 && pnpm lint
```

## 获取帮助

遇到问题？可以通过以下方式获取帮助：

1. 查看 [docs/FAQ.md](./docs/FAQ.md)
2. 搜索已有 Issue
3. 创建新 Issue 并打上 `question` 标签
4. 查看 [.agents/ERRORS.md](./.agents/ERRORS.md) 常见错误

## 许可证

通过提交代码，你同意将你的贡献在 [MIT License](./LICENSE) 下发布。

---

**感谢你的贡献！**

---

**文档版本**: v1.0  
**最后更新**: 2026-04-05
