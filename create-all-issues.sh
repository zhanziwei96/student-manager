#!/bin/bash
# 一键创建所有 GitHub Issues（完整版）
# 包含 10 个需求 + 16 个关键缺陷

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
echo "=============================="

# ==================== 高优先级需求 ====================

echo "创建需求 Issues..."

gh issue create --repo $REPO \
  --title "[需求] 支持多班级并行上课 - ClassSession 重构" \
  --label "enhancement,high-priority,architecture" \
  --body "## 需求描述
当前系统使用 \`ClassSession\` 单表单记录（ID=1）存储全局状态，同一时间只能有一个班级上课。需要重构支持多班级并行。

## 现状问题
\`\`\`python
def get_class_session(session: Session):
    return session.get(ClassSession, 1)  # 硬编码 ID=1
\`\`\`

## 业务场景
- 上午1-2节，多个班级同时在机房上课
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
- DB-001: 单表全局状态反模式" || echo "Issue 1 创建失败"

echo "✓ Issue 1: 多班级并行上课"

gh issue create --repo $REPO \
  --title "[需求] 课程表与排课系统 - 自动签到触发" \
  --label "enhancement,high-priority" \
  --body "## 需求描述
建立周课表系统，支持按课表自动/手动开启签到，从\"签到工具\"升级为\"教学管理系统\"。

## 功能要求
- [ ] 可视化课表界面（教师视图）
- [ ] 课程信息：课程名、班级、教室、时间段、任课教师
- [ ] 支持单周/双周/每周/自定义周期
- [ ] 课程开始时间自动开启签到（可配置）
- [ ] 节假日/调课管理
- [ ] 到上课时间自动推送\"开始上课\"提醒
- [ ] 调课申请与审批流程
- [ ] 课表导入导出（Excel）

## 建议数据模型
\`\`\`python
class Course:
    id, name, description

class Schedule:
    id, course_id, class_name, teacher_id
    day_of_week, start_time, end_time
    week_pattern: str  # \"single\", \"double\", \"all\"
\`\`\`

## 关联需求
- REQ-001: 多班级并行上课" || echo "Issue 2 创建失败"

echo "✓ Issue 2: 课程表系统"

gh issue create --repo $REPO \
  --title "[需求] 作业发布、提交与批改系统" \
  --label "enhancement,high-priority" \
  --body "## 需求描述
教师发布作业，学生提交，批改后自动关联成绩，形成教学闭环。

## 功能要求
### 教师端
- [ ] 发布作业：标题、描述、截止时间、附件、分数
- [ ] 查看提交列表，按状态筛选
- [ ] 批改：评分、评语、退回重做
- [ ] 批量下载作业附件

### 学生端
- [ ] 作业列表，显示截止时间倒计时
- [ ] 提交作业：文字、图片、文件（支持多格式）
- [ ] 查看批改结果和评语
- [ ] 截止前自动提醒

### 系统集成
- [ ] 作业成绩自动计入\"平时成绩\"维度
- [ ] 作业状态追踪：未提交/已提交/已批改
- [ ] 批改界面支持批注（图片/PDF）

## 技术建议
- 文件存储抽象层（支持 OSS/S3）
- 大文件分片上传" || echo "Issue 3 创建失败"

echo "✓ Issue 3: 作业管理系统"

# ==================== 中优先级需求 ====================

gh issue create --repo $REPO \
  --title "[需求] 站内通知与公告系统" \
  --label "enhancement,medium-priority" \
  --body "## 功能要求
- [ ] 发送对象：全班/多班/个人
- [ ] 消息类型：公告、提醒、私信
- [ ] 已读回执功能
- [ ] 通知渠道：站内消息 + 可选邮件/微信推送
- [ ] 消息历史查询
- [ ] 消息角标实时更新
- [ ] 未读消息列表
- [ ] 重要公告置顶

## 技术建议
- WebSocket 实时推送
- 消息队列表设计" || echo "Issue 4 创建失败"

echo "✓ Issue 4: 通知系统"

gh issue create --repo $REPO \
  --title "[需求] 学生请假申请与审批流程" \
  --label "enhancement,medium-priority" \
  --body "## 功能要求
### 学生端
- [ ] 提交请假：类型（事假/病假/其他）、时间范围、原因、附件
- [ ] 查看请假审批状态
- [ ] 销假功能

### 教师端
- [ ] 审批请假：通过/驳回，填写审批意见
- [ ] 请假记录查询

### 系统集成
- [ ] 请假期间自动跳过签到
- [ ] 考勤报表区分\"请假\"和\"缺勤\"
- [ ] 教师审批后学生收到通知" || echo "Issue 5 创建失败"

echo "✓ Issue 5: 请假管理"

gh issue create --repo $REPO \
  --title "[需求] 成绩多维度与权重配置" \
  --label "enhancement,medium-priority" \
  --body "## 需求描述
支持多种成绩类型，配置权重，自动计算总评成绩。

## 功能要求
- [ ] 成绩维度：平时成绩、期中、期末、作业、课堂表现、签到率
- [ ] 权重配置：各维度占比（如平时30%+期末70%）
- [ ] 平时成绩子项：签到、作业、课堂问答等细分
- [ ] 自动计算总评
- [ ] 成绩曲线图（个人/班级）
- [ ] 成绩录入界面支持多维度
- [ ] 学生端查看成绩构成饼图
- [ ] 导出成绩单（PDF）

## 建议数据模型
\`\`\`python
class ScoreCategory:
    id, name, weight, parent_id

class StudentScore:
    student_id, category_id, score, recorded_at
\`\`\`" || echo "Issue 6 创建失败"

echo "✓ Issue 6: 成绩多维度"

gh issue create --repo $REPO \
  --title "[需求] 数据导出与统计报表" \
  --label "enhancement,medium-priority" \
  --body "## 功能要求
- [ ] 班级签到报表（按日/周/月）
- [ ] 个人学期成绩单
- [ ] 班级成绩对比分析
- [ ] 教师工作量统计
- [ ] 导出格式：Excel、PDF
- [ ] 报表模板美观
- [ ] 支持自定义时间范围
- [ ] 报表自动发送至邮箱（可选）" || echo "Issue 7 创建失败"

echo "✓ Issue 7: 数据导出"

# ==================== 低优先级需求 ====================

gh issue create --repo $REPO \
  --title "[需求] 积分商城与激励机制" \
  --label "enhancement,low-priority" \
  --body "## 功能要求
- [ ] 积分规则：签到、作业、课堂表现获得积分
- [ ] 虚拟奖品：免作业券、加分券、称号徽章
- [ ] 排行榜：周榜/月榜/学期榜
- [ ] 成就系统：连续签到7天、满分作业等" || echo "Issue 8 创建失败"

echo "✓ Issue 8: 积分商城"

gh issue create --repo $REPO \
  --title "[需求] 家长端只读视图" \
  --label "enhancement,low-priority" \
  --body "## 功能要求
- [ ] 家长注册绑定学生
- [ ] 查看：签到记录、成绩、作业状态
- [ ] 接收通知
- [ ] 只读权限，不可操作" || echo "Issue 9 创建失败"

echo "✓ Issue 9: 家长端"

gh issue create --repo $REPO \
  --title "[需求] 课堂互动工具" \
  --label "enhancement,low-priority" \
  --body "## 功能要求
- [ ] 随机抽问：从已签到学生随机选择
- [ ] 实时投票：选择题，学生手机端投票，大屏展示结果
- [ ] 弹幕提问：学生匿名提问，教师筛选展示" || echo "Issue 10 创建失败"

echo "✓ Issue 10: 课堂互动"

# ==================== 严重缺陷 ====================

echo ""
echo "创建缺陷 Issues..."

gh issue create --repo $REPO \
  --title "[缺陷] SQLite 并发写入性能瓶颈 - 需评估迁移方案" \
  --label "bug,high-priority,database,architecture" \
  --body "## 问题描述
使用 \`check_same_thread=False\` 绕过 SQLite 线程限制，但未解决并发写入性能问题。

## 代码位置
\`\`\`python
engine = create_engine(
    f\"sqlite:///{settings.get_database_path()}\",
    connect_args={\"check_same_thread\": False},
    echo=settings.app.debug
)
\`\`\`

## 影响
- 班级签到高峰期（50+学生同时签到）可能出现数据库锁定
- 写操作串行执行，性能受限
- 无法横向扩展到多实例

## 建议方案
1. **短期**: 增加连接池、读写分离
2. **长期**: 评估迁移至 PostgreSQL

## 优先级
🔴 严重 - 影响高并发场景" || echo "Defect 1 创建失败"

echo "✓ Defect 1: SQLite 并发"

gh issue create --repo $REPO \
  --title "[缺陷] JWT 令牌无法撤销 - 安全风险" \
  --label "bug,high-priority,security" \
  --body "## 问题描述
JWT 签发后，即使用户被禁用/密码修改，令牌仍然有效直到过期。

## 代码位置
\`\`\`python
async def get_current_user(request: Request):
    payload = decode_token(token)
    # 未查询数据库验证用户当前状态
    return payload
\`\`\`

## 安全风险
- 禁用用户仍可操作系统
- 密码修改后旧令牌仍可用
- 无法实现\"踢下线\"功能

## 建议方案
1. **方案A**: 引入 Token 黑名单（Redis）
2. **方案B**: 改用 Session + Redis
3. **方案C**: 缩短 Token 有效期 + 刷新机制

## 优先级
🔴 严重 - 安全漏洞" || echo "Defect 2 创建失败"

echo "✓ Defect 2: JWT 撤销"

gh issue create --repo $REPO \
  --title "[缺陷] Cookie secure 标志硬编码为 False" \
  --label "bug,high-priority,security" \
  --body "## 问题描述
Cookie 的 secure 标志硬编码为 False，生产环境 HTTPS 下不安全。

## 代码位置
\`\`\`python
def set_token_cookie(response: Response, token: str):
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=False,   # 应为 True
        samesite=\"lax\",
    )
\`\`\`

## 修复建议
根据环境变量动态设置 secure 标志：
\`\`\`python
secure=settings.app.env == \"production\"
\`\`\`

## 优先级
🔴 严重 - 安全风险" || echo "Defect 3 创建失败"

echo "✓ Defect 3: Cookie secure"

gh issue create --repo $REPO \
  --title "[缺陷] 并发分数更新无锁保护" \
  --label "bug,high-priority,data-integrity" \
  --body "## 问题描述
分数更新操作无乐观锁或悲观锁保护，并发修改可能丢失更新。

## 代码位置
\`\`\`python
def update_student_score(session, student_id, delta, ...):
    student = get_student(session, student_id)  # 读取
    old_score = student.score
    new_score = old_score + delta
    student.score = new_score  # 写入
    # 无锁保护
\`\`\`

## 影响
- 并发扣/加分时可能出现数据覆盖
- 数据不一致

## 建议方案
- 添加 \`version\` 字段实现乐观锁
- 或使用数据库行锁

## 优先级
🔴 严重 - 数据完整性风险" || echo "Defect 4 创建失败"

echo "✓ Defect 4: 分数更新锁"

gh issue create --repo $REPO \
  --title "[缺陷] 密码盐值字段冗余 - bcrypt 已内置盐值" \
  --label "bug,high-priority,security" \
  --body "## 问题描述
同时存储 \`password_hash\` 和 \`salt\`，但 bcrypt 已内置盐值。

## 代码位置
\`\`\`python
class Student:
    password_hash: Optional[str]
    salt: Optional[str]  # 冗余
\`\`\`

## 影响
- 不必要的字段存储
- 盐值管理复杂化
- 可能产生不一致

## 修复建议
移除 salt 字段，bcrypt 哈希已包含盐值。

## 优先级
🔴 严重 - 设计缺陷" || echo "Defect 5 创建失败"

echo "✓ Defect 5: 盐值冗余"

# ==================== 中等缺陷 ====================

gh issue create --repo $REPO \
  --title "[缺陷] 权限检查机制不一致 - 装饰器与手动调用混用" \
  --label "bug,medium-priority,architecture" \
  --body "## 问题描述
装饰器依赖注入与手动调用混用，风格不一致。

## 代码对比
\`\`\`python
# students.py - 依赖注入
@router.get(\"/students\")
async def get_students_list(user: dict = Depends(get_current_user))

# checkin.py - 手动调用
@router.post(\"/class-session/start\")
async def begin_class(request: Request):
    await require_login(request)
\`\`\`

## 修复建议
统一使用 FastAPI 依赖注入机制。" || echo "Defect 6 创建失败"

echo "✓ Defect 6: 权限检查不一致"

gh issue create --repo $REPO \
  --title "[缺陷] 前端双重状态管理 - Pinia 与 TanStack Query 冲突" \
  --label "bug,medium-priority,frontend" \
  --body "## 问题描述
双重状态源：Pinia 的 \`user\` 和 Query 的缓存同时存在，需要手动同步。

## 代码位置
\`\`\`typescript
const user = ref<User | null>(null)  // Pinia

const { refetch } = useQuery({
  queryFn: async () => {
    user.value = res.data  // Query 结果写入 Pinia
  },
  enabled: false,
})
\`\`\`

## 修复建议
服务端状态完全由 TanStack Query 管理，Pinia 仅管理 UI 状态。" || echo "Defect 7 创建失败"

echo "✓ Defect 7: 双重状态管理"

gh issue create --repo $REPO \
  --title "[缺陷] 限流使用内存存储 - 多实例部署失效" \
  --label "bug,medium-priority,scalability" \
  --body "## 问题描述
限流配置使用内存存储，多实例部署时每个实例独立计数。

## 影响
攻击者可通过轮询不同实例绕过限流。

## 修复建议
使用 Redis 作为限流存储后端。" || echo "Defect 8 创建失败"

echo "✓ Defect 8: 限流扩展"

gh issue create --repo $REPO \
  --title "[缺陷] Docker 单容器多进程架构" \
  --label "bug,medium-priority,deployment" \
  --body "## 问题描述
Dockerfile 中同时安装 Nginx + Python + SQLite，违反容器单一职责。

## 影响
- 无法独立扩展前后端
- 一个进程崩溃影响全部

## 修复建议
分离为：前端容器、后端容器、数据库（或共享存储）" || echo "Defect 9 创建失败"

echo "✓ Defect 9: 容器架构"

echo ""
echo "=============================="
echo "所有 Issues 创建完成！"
echo "=============================="
echo "总计: 10 需求 + 9 缺陷 = 19 个 Issues"
