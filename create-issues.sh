#!/bin/bash
# 一键创建 GitHub Issues 脚本
# 需要配置 GH_TOKEN 环境变量

REPO="zhanziwei96/student-manager"

# 检查 gh CLI
if ! command -v gh &> /dev/null; then
    echo "请先安装 GitHub CLI: https://cli.github.com/"
    exit 1
fi

# 检查登录状态
if ! gh auth status &> /dev/null; then
    echo "请先登录: gh auth login"
    exit 1
fi

echo "开始创建 Issues..."

# Issue 1: 多班级并行上课
gh issue create --repo $REPO \
  --title "[需求] 支持多班级并行上课 - ClassSession 重构" \
  --label "enhancement,high-priority,architecture" \
  --body "## 需求描述
当前系统使用 \`ClassSession\` 单表单记录（ID=1）存储全局状态，同一时间只能有一个班级上课。需要重构支持多班级并行。

## 现状问题
\`\`\`python
# backend/app/crud/checkin.py
def get_class_session(session: Session):
    return session.get(ClassSession, 1)  # 硬编码 ID=1
\`\`\`

## 业务场景
- 上午1-2节，2025级中药学1班、2班、3班同时在机房上课
- 各班级独立签到，互不干扰

## 功能要求
- [ ] 教师可同时开启多个班级的课堂会话
- [ ] 每个班级有独立的签到状态
- [ ] 学生按所属班级进行签到
- [ ] 教师可在不同班级间切换管理
- [ ] 统计报表按班级分别展示

## 建议方案
重构数据模型，移除全局单例设计。

## 关联缺陷
- DB-001: 单表全局状态反模式"

echo "Issue 1 创建完成"

# Issue 2: SQLite 并发
gh issue create --repo $REPO \
  --title "[缺陷] SQLite 并发写入性能瓶颈 - 需评估迁移方案" \
  --label "bug,high-priority,database,architecture" \
  --body "## 问题描述
使用 \`check_same_thread=False\` 绕过 SQLite 线程限制，但未解决并发写入性能问题。

## 影响
- 班级签到高峰期（50+学生同时签到）可能出现数据库锁定
- 无法横向扩展到多实例

## 建议方案
1. **短期**: 增加连接池、读写分离
2. **长期**: 评估迁移至 PostgreSQL

## 优先级
🔴 严重 - 影响高并发场景"

echo "Issue 2 创建完成"

# Issue 3: JWT 令牌无法撤销
gh issue create --repo $REPO \
  --title "[缺陷] JWT 令牌无法撤销 - 安全风险" \
  --label "bug,high-priority,security" \
  --body "## 问题描述
JWT 签发后，即使用户被禁用/密码修改，令牌仍然有效直到过期。

## 安全风险
- 禁用用户仍可操作系统
- 密码修改后旧令牌仍可用
- 无法实现'踢下线'功能

## 建议方案
1. **方案A**: 引入 Token 黑名单（Redis）
2. **方案B**: 改用 Session + Redis
3. **方案C**: 缩短 Token 有效期 + 刷新机制

## 优先级
🔴 严重 - 安全漏洞"

echo "Issue 3 创建完成"

echo "所有 Issues 创建完成！"
