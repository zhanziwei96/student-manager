# 移动端优先改造实施计划（教师端 + 学生端）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 教师端（13 页）和学生端（8 页）按 Apple HIG 改造为移动端优先；管理员端不动（仅全局令牌升级带来的被动改善）。

**Architecture:** 不动路由与 API；改造集中在四层：设计令牌（tokens.css）→ 核心组件（BottomNav / Sheet / 手势 composable）→ 布局（DashboardLayout）→ 页面（首屏信息架构重构 + 全页面对比度/触控巡检）。新交互组件（底部 Sheet、下拉刷新、滑动返回）作为可复用单元落在 `components/ui/` 与 `composables/`。

**Tech Stack:** Vue 3.5 + TypeScript + Tailwind v4 + radix-vue + TanStack Query + vitest；手势用原生 TouchEvent（不引第三方手势库——极简优先）

**Spec:** `student-manager-vs-Apple-HIG-差距分析.md`（仓库根目录）+ 用户决策：全做（**不含 Dark Mode**）、签到作中央主操作、全局令牌允许改

## 用户决策（已确认）

| 决策项 | 结论 |
|---|---|
| 范围 | P0（对比度/字号/触控）+ P1（手势/信息架构）+ P2（材质/Action Sheet/圆角/图标），**排除 Dark Mode** |
| 底部导航 | 签到作中央主操作；教师 tab=仪表板/学生/课表/更多，学生 tab=仪表板/小组/成绩/更多 |
| 全局令牌 | 允许改 tokens.css（管理员页面被动受益可接受） |
| 管理员页面 | 不动（无移动端适配需求） |

## 关键现状（已核实）

- `tokens.css`：`--color-text-tertiary/muted/placeholder` 均为 `#a3a3a3`（对比度 2.5:1，HIG 要求 ≥4.5:1）；`--touch-target-min: 2.75rem`（44px）已定义；圆角二元（`--radius-container: 0.75rem` / `--radius-full`）
- `DESIGN_SYSTEM.md:189-197` 明确禁 `backdrop-blur`/渐变/发光/阴影 → **Task 7 需在文档中开"移动端教师/学生页面例外"**
- `BottomNav.vue`：教师 8 tab / 学生 7 tab（HIG ≤5），3 个死链：`/teacher/group-tasks`、`/student/group-evaluations`、`/student/group-results`（路由表均无）
- 布局 `DashboardLayout.vue`：移动端=顶部 header(h-14)+底部 BottomNav(h-16)+MobileDrawer；主内容区 `p-4 pt-16 pb-20`；`viewport-fit=cover` 已设但**无 `safe-area-inset` 处理**
- `MobilePicker.vue`（309 行）已有"移动端检测 + 底部弹层"模式 → Action Sheet 参照
- 字号：`text-sm` 318 处、`text-xs` 148 处、`text-[11px]` 3 处；全 px 固定
- 高德 Key 裸奔问题（分析报告第五节）→ **不在本计划范围**，另行处理

## Global Constraints

- 前端命令在 `frontend-v3/` 下用 `pnpm`；测试 `pnpm test:run`；类型检查 `pnpm exec vue-tsc --noEmit`（必须退出码 0）
- 后端无需改动；若动到后端文件立即停止并上报
- Tailwind v4：自定义 `@theme` 保留 `--spacing: 0.25rem`（tokens.css 用 `@theme inline`，可覆盖）
- 管理员页面（`views/admin/`）不改；`DashboardLayout.vue` 改动需保持管理员桌面端行为不变
- 每个 Task 完成必须：`pnpm exec vue-tsc --noEmit` 通过 + `pnpm test:run` 全绿（或仅剩与本任务无关的既有失败，需列出清单）
- 视觉验证：每个涉及页面结构的 Task，用 `pnpm dev` 起服务后以 375px 视口截图/走查（报告里说明验证方式）
- 提交粒度：每个 Task 一个 commit

## 任务清单

- [x] **Task 0 — 设计令牌升级（tokens.css）**：✅ 1c78dea + e58ebb1（双评审通过；质量评审抓出 @theme inline 死令牌已修）

> 原 Task 0 中「字号 rem 化 + text-xs 语义收敛」实际拆到 Task 9 执行（Tailwind 字号本为 rem，无需动令牌）
- [x] **Task 1 — 底部 Sheet 组件**：✅ d52403c + 17c8f9c（双评审通过；评审跟进 Esc 关闭 + aria-labelledby + 令牌工具类）
- [x] **Task 2 — BottomNav 重构**：✅ 17ab2db + 36f9a40（双评审通过；评审抓出 /teacher/session 前缀撞车 /teacher/sessions-history 已修 + 2 回归测试）。注：签到中央按钮选中态为路由匹配（非「有活跃课堂才高亮」），实现侧有意为之，UX 更直觉
- [x] **Task 3 — 布局移动端优先化**：✅ c841317（双评审通过）。注：抽屉「我的」与更多面板的修改密码/退出为**有意保留的双入口**；管理员移动端底部留白与抽屉 safe-top 遮挡为既有行为，不在本计划修
- [x] **Task 4 — 学生端首屏重构**：✅ c36781b（双评审通过）。Minor 留档：签到卡片加载中间态会闪现「无课堂」态（staleTime 缓存缓解，未修）；桌面端 CTA 全宽过宽（有意取舍）
- [x] **Task 5 — 教师端首屏重构**：✅ 446fa23 + 质量评审跟进（CTA 换 Button variant="cta" 补齐焦点环/与学生端一致；次级提示补 focus-visible）。**计划条文修订**：原写「移动端隐藏次要统计」→ 实现侧有意保留全部统计卡（移动端 2 列展示有价值，不隐藏）。**已知程序瑕疵**：446fa23 混入学生端 spec 改动（并行 add 目录误收），该 commit 单独检出时学生端 2 测试为红（UI 在后续 c36781b 才落地）；分支历史不 rewrite，合并 main 时建议 squash
- [x] **Task 6 — 手势 composable 三件套**：✅ 33f7bc3 + 717fdc6（双评审通过；质量评审抓出 activeRowId API 陷阱/基线偏移/clamp/v-if 挂载 4 项已修）：`composables/usePullToRefresh.ts`（触摸下拉>80px 触发 `refetch`，带阻力曲线与回弹动画，作用于列表页容器）；`composables/useSwipeBack.ts`（详情页左缘右滑>阈值→`router.back()`，同时保留返回按钮）；`composables/useSwipeActions.ts`（列表行左滑露出操作按钮）。各含单测（模拟 TouchEvent 序列）
- [x] **Task 7 — 手势落地到页面**：✅ 3638ebd + 68ff977 + cb2ae2e + 0b1573f（双评审通过；评审抓出窗口级滚动布局下 PTR 顶部守卫失效已修 + 指示器提取为共享组件 PullToRefreshIndicator）。注：学生端失物招领无行级操作 API，仅加下拉刷新（待后端加接口）：下拉刷新应用到学生端（Dashboard/我的成绩/我的小组/问答/失物招领）与教师端（Dashboard/学生/课表/小组/问答/失物招领）列表页；滑动返回应用到失物招领详情、问答详情、OfferingGrades；行滑动操作应用到失物招领列表（标记已解决/删除）
- [x] **Task 8 — 移动端弹窗 Sheet 化**：✅ c7be205 + footer 堆叠修复（双评审通过；ResponsiveDialog 桌面 Dialog/移动 BottomSheet 分流；15 个弹窗迁移；危险操作移动端红字）：移动端（<768px）下教师/学生页面的确认类 Dialog（删除确认、转班确认等）与筛选弹层统一迁移到 BottomSheet（危险操作红字 Action 样式）；桌面端保持居中 Dialog 不变。复用 MobilePicker 的移动端检测模式
- [x] **Task 9 — 对比度与字号全页面巡检**：✅ 4b8516e（118 处 #a3a3a3→#525252 + text-[11px]→text-xs；管理员 34 处不动）（教师+学生 21 页）**：`text-[#a3a3a3]`（190 处全局，教师/学生端逐页替换为令牌色 `text-secondary` 或 `#525252`）；`text-[11px]` → `text-xs`（对齐 Caption 下限）；正文级文字移动端 ≥14px（text-sm 底线），表格密集区允许 text-sm 但行高调高；每页 vitest 快照/DOM 断言更新
- [x] **Task 10 — 触控目标巡检**：✅ e1573a7 + 721e454（双评审通过；评审抓出 h-8 覆盖与 min-h 冲突的瘦高按钮 + Button 全局改动波及管理员——44px 热区改为 max-md 断点限定，桌面端/管理员恢复原尺寸）（教师+学生页面 + ui 组件）**：全量审计图标按钮/表格行操作/列表行点击区/Badge 点击：可点元素 min 44×44px（视觉尺寸可小，但点击热区用 `min-h-[44px] min-w-[44px]` + 负边距补偿）；BottomNav tab、首屏主按钮、表单控件逐一验证
- [x] **Task 11 — P2 视觉材质与形态**：✅ 13b3004（双评审通过；分组列表 inset grouped 应用到 3 页、MyGrades/MyOfferings 已是 divide-y 表格属合理跳过、Card 圆角响应式、BottomNav 选中态 stroke-width 2.5、DESIGN_SYSTEM 移动端例外章节）：BottomNav/header 毛玻璃（Task 3 已落，本任务做页面级）：卡片圆角移动端 16px、分组列表（iOS inset grouped：同组卡片合并为单一容器+内部分隔线，替代独立卡片堆叠）应用到设置类/列表类页面；选中态图标填充化（lucide `fill` 属性或换填充图标）；更新 `DESIGN_SYSTEM.md`：新增「移动端例外」章节（教师/学生页面允许 backdrop-blur 材质层、底部 Sheet、加大圆角，管理员/桌面端禁令不变）
- [ ] **Task 12 — 测试与端到端验收**：`pnpm test:run` 全绿 + `vue-tsc` 干净；375×812（iPhone 13 mini）与 390×844 视口走查 8 条链路（学生：登录→首屏签到→小组→成绩→问答→失物招领；教师：登录→开始上课→课表→学生→小组）；撰写验收记录；更新 `docs/superpowers/plans/` 计划勾选状态

## 风险与注意事项

| 风险 | 缓解 |
|---|---|
| 全局令牌改动波及管理员页面 | Task 0 完成后先对管理员页做视觉回归（截图对比），对比度/字号变深变大属预期改善 |
| 手势与浏览器系统手势冲突 | useSwipeBack 仅在触摸起点距左缘 <24px 时激活，避让系统边缘手势（HIG 要求） |
| 微信 WebView 兼容（tokens.css 硬编码 HEX 的历史原因） | 材质层用 `@supports (backdrop-filter: blur(1px))` 包裹，不支持时降级为实色背景 |
| vitest 大面积断言失效 | 每 Task 内同步改测试；jest-dom 断言类名变化的逐一更新 |
