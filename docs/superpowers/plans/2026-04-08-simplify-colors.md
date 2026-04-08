# 颜色系统简化实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 ClassHub 前端颜色系统从多色杂乱体系简化为双主色 + 三状态色的精简系统

**Architecture:** 通过精简 CSS 变量、统一组件颜色、用透明度替代色相变化，实现视觉一致性

**Tech Stack:** Vue 3 + TypeScript + Tailwind CSS v4

---

## 文件结构

| 文件 | 职责 | 变更类型 |
|------|------|----------|
| `frontend-v3/src/styles/tokens.css` | 定义所有 CSS 颜色变量 | 修改：删除蓝绿紫橙主题，添加 Indigo/Neutral 主题 |
| `frontend-v3/src/views/admin/Dashboard.vue` | 管理员仪表板统计卡片 | 修改：4色卡片统一为 Indigo |
| `frontend-v3/src/views/teacher/Dashboard.vue` | 教师仪表板统计卡片 | 修改：4色卡片统一为 Indigo |
| `frontend-v3/src/views/teacher/Schedules.vue` | 课程表页面 | 修改：课程颜色简化为 Indigo 单色系 |
| `frontend-v3/src/components/ui/Badge.vue` | 徽章组件 | 修改：精简颜色变体 |

---

## Task 1: 精简 CSS 颜色变量 (tokens.css)

**Files:**
- Modify: `frontend-v3/src/styles/tokens.css:109-147`

- [ ] **Step 1: 查看当前颜色变量定义**

查看文件确认删除范围：
```bash
grep -n "card-blue\|card-green\|card-purple\|card-orange\|Grafana" frontend-v3/src/styles/tokens.css
```

- [ ] **Step 2: 删除旧的颜色变量**

删除以下内容：
- `--color-success-soft` 及相关的柔和状态色（109-117行）
- `--card-blue-*` 所有蓝色主题变量（120-125行）
- `--card-green-*` 所有绿色主题变量（127-132行）
- `--card-purple-*` 所有紫色主题变量（134-139行）
- `--card-orange-*` 所有橙色主题变量（141-147行）

- [ ] **Step 3: 添加新的精简颜色变量**

在边框定义前添加新的颜色变量：

```css
  /* ========== 卡片主题色变量 (精简为 Indigo 主色 + Neutral 中性色) ========== */
  /* 主色 Indigo 主题 - 用于主要卡片 */
  --card-indigo-bg: rgba(99, 102, 241, 0.15);
  --card-indigo-border: rgba(99, 102, 241, 0.4);
  --card-indigo-icon-bg: rgba(129, 140, 248, 0.3);
  --card-indigo-icon-text: #a5b4fc;
  --card-indigo-shadow: rgba(49, 46, 129, 0.3);
  --card-indigo-glow: rgba(99, 102, 241, 0.1);

  /* 中性色主题 - 用于普通卡片 */
  --card-neutral-bg: rgba(255, 255, 255, 0.03);
  --card-neutral-border: rgba(255, 255, 255, 0.1);
  --card-neutral-icon-bg: rgba(255, 255, 255, 0.1);
  --card-neutral-icon-text: rgba(255, 255, 255, 0.7);
  --card-neutral-shadow: rgba(0, 0, 0, 0.3);
  --card-neutral-glow: rgba(255, 255, 255, 0.05);

  /* 状态色主题 - 用于特定状态 */
  --card-success-bg: rgba(34, 197, 94, 0.15);
  --card-success-border: rgba(34, 197, 94, 0.4);
  --card-success-icon-bg: rgba(74, 222, 128, 0.3);
  --card-success-icon-text: #86efac;
  --card-success-shadow: rgba(5, 46, 22, 0.3);
  --card-success-glow: rgba(34, 197, 94, 0.1);

  --card-warning-bg: rgba(245, 158, 11, 0.15);
  --card-warning-border: rgba(245, 158, 11, 0.4);
  --card-warning-icon-bg: rgba(251, 191, 36, 0.3);
  --card-warning-icon-text: #fcd34d;
  --card-warning-shadow: rgba(120, 53, 15, 0.3);
  --card-warning-glow: rgba(245, 158, 11, 0.1);

  --card-error-bg: rgba(239, 68, 68, 0.15);
  --card-error-border: rgba(239, 68, 68, 0.4);
  --card-error-icon-bg: rgba(248, 113, 113, 0.3);
  --card-error-icon-text: #fca5a5;
  --card-error-shadow: rgba(127, 29, 29, 0.3);
  --card-error-glow: rgba(239, 68, 68, 0.1);
```

- [ ] **Step 4: 验证 CSS 语法**

```bash
cd frontend-v3 && npx stylelint src/styles/tokens.css --syntax css || echo "No stylelint, skipping"
```

- [ ] **Step 5: Commit**

```bash
git add frontend-v3/src/styles/tokens.css
git commit -m "refactor(tokens): 精简卡片颜色变量为 Indigo 主色系

- 删除蓝绿紫橙四色主题变量
- 添加 Indigo/Neutral/Success/Warning/Error 五组精简主题
- 保持与暗色主题兼容性"
```

---

## Task 2: 统一 Admin Dashboard 统计卡片

**Files:**
- Modify: `frontend-v3/src/views/admin/Dashboard.vue:20-80`

- [ ] **Step 1: 查看当前统计卡片代码**

```bash
head -80 frontend-v3/src/views/admin/Dashboard.vue
```

确认 `statCards` computed 和 `CardColor` 类型定义位置。

- [ ] **Step 2: 修改 statCards 定义**

将第20-49行的 `statCards` computed 修改为：

```typescript
const statCards = computed(() => [
  {
    title: '学生总数',
    value: stats.value?.total_students ?? 0,
    icon: Users,
    trend: '+12%',
  },
  {
    title: '活跃学生',
    value: stats.value?.active_students ?? 0,
    icon: GraduationCap,
    trend: '+5%',
  },
  {
    title: '班级总数',
    value: stats.value?.total_classes ?? 0,
    icon: BookOpen,
    trend: '0%',
  },
  {
    title: '平均分数',
    value: Math.round(stats.value?.average_score ?? 0),
    icon: TrendingUp,
    trend: '+2%',
  },
])
```

- [ ] **Step 3: 删除 CardColor 类型和颜色相关函数**

删除第51-87行的内容：
- `type CardColor = 'blue' | 'green' | 'purple' | 'orange'`
- `getCardStyle` 函数
- `getCardIconStyle` 函数
- `getCardGlowStyle` 函数
- `getCardTextMutedColor` 函数
- `getTrendBadgeStyle` 函数

- [ ] **Step 4: 添加统一的卡片样式函数**

在 `statCards` 定义后添加：

```typescript
// 统一的 Indigo 卡片样式
const getCardStyle = () => ({
  backgroundColor: 'var(--card-indigo-bg)',
  borderColor: 'var(--card-indigo-border)',
  '--tw-shadow-color': 'var(--card-indigo-shadow)',
})

const getCardIconStyle = () => ({
  backgroundColor: 'var(--card-indigo-icon-bg)',
  color: 'var(--card-indigo-icon-text)',
})

const getCardGlowStyle = () => ({
  backgroundColor: 'var(--card-indigo-glow)',
})

const getTrendBadgeStyle = () => ({
  backgroundColor: 'var(--card-indigo-icon-bg)',
  color: 'var(--card-indigo-icon-text)',
})
```

- [ ] **Step 5: 更新模板中的样式绑定**

修改模板中第105-115行的样式绑定，移除所有 `card.color` 参数：

```vue
<Card
  v-for="card in statCards"
  :key="card.title"
  class="group relative overflow-hidden p-4 shadow-lg transition-all duration-300 hover:scale-[1.02]"
  :style="getCardStyle()"
>
```

修改第118行的文字颜色类：
```vue
<p class="mt-3 text-xs font-medium text-indigo-200/80">
```

修改第131行的图标样式绑定：
```vue
:style="getCardIconStyle()"
```

修改第141行的趋势徽章样式：
```vue
:style="getTrendBadgeStyle()"
```

修改第151行的背景光晕样式：
```vue
:style="getCardGlowStyle()"
```

- [ ] **Step 6: 运行类型检查**

```bash
cd frontend-v3 && npx vue-tsc --noEmit 2>&1 | head -20
```

- [ ] **Step 7: Commit**

```bash
git add frontend-v3/src/views/admin/Dashboard.vue
git commit -m "refactor(admin-dashboard): 统一统计卡片为 Indigo 主题

- 移除4色卡片配置
- 所有统计卡片统一使用 Indigo 主色
- 简化样式函数，移除颜色参数"
```

---

## Task 3: 统一 Teacher Dashboard 统计卡片

**Files:**
- Modify: `frontend-v3/src/views/teacher/Dashboard.vue`

- [ ] **Step 1: 查看教师 Dashboard 结构**

```bash
head -100 frontend-v3/src/views/teacher/Dashboard.vue
```

确认是否有与 admin Dashboard 类似的统计卡片代码。

- [ ] **Step 2: 如果存在统计卡片，按 Task 2 相同方式修改**

修改步骤与 Task 2 相同：
1. 移除 `color` 属性
2. 删除 `CardColor` 类型
3. 删除颜色相关函数
4. 添加统一的 Indigo 样式函数
5. 更新模板绑定

- [ ] **Step 3: 如果不存在统计卡片，跳过此任务**

- [ ] **Step 4: Commit**

```bash
git add frontend-v3/src/views/teacher/Dashboard.vue
git commit -m "refactor(teacher-dashboard): 统一统计卡片为 Indigo 主题" || echo "No changes to commit"
```

---

## Task 4: 简化课程表颜色 (Schedules.vue)

**Files:**
- Modify: `frontend-v3/src/views/teacher/Schedules.vue`

- [ ] **Step 1: 查找课程主题色相关代码**

```bash
grep -n "getCourseTheme\|course.*color\|bg-blue\|bg-green\|bg-purple\|bg-orange" frontend-v3/src/views/teacher/Schedules.vue | head -30
```

- [ ] **Step 2: 查看课程主题函数定义**

```bash
grep -A 20 "getCourseTheme" frontend-v3/src/views/teacher/Schedules.vue
```

- [ ] **Step 3: 修改课程主题函数**

将颜色分配逻辑改为统一的 Indigo 透明度：

```typescript
// 简化的课程主题 - 统一使用 Indigo 单色系
const getCourseTheme = (courseName?: string) => {
  if (!courseName) {
    return {
      bg: 'bg-indigo-500/10',
      border: 'border-indigo-500/30',
      text: 'text-indigo-300',
      icon: 'text-indigo-400',
      accent: 'bg-indigo-500/20',
    }
  }
  
  // 使用哈希值决定透明度层次，而非色相
  const hash = courseName.split('').reduce((acc, char) => {
    return acc + char.charCodeAt(0)
  }, 0)
  
  const level = hash % 3
  const themes = [
    { bg: 'bg-indigo-500/25', border: 'border-indigo-500/40', text: 'text-indigo-200', icon: 'text-indigo-300', accent: 'bg-indigo-500/30' },
    { bg: 'bg-indigo-500/15', border: 'border-indigo-500/30', text: 'text-indigo-300', icon: 'text-indigo-400', accent: 'bg-indigo-500/20' },
    { bg: 'bg-indigo-500/10', border: 'border-indigo-500/20', text: 'text-indigo-300/80', icon: 'text-indigo-400/80', accent: 'bg-indigo-500/15' },
  ]
  
  return themes[level]
}
```

- [ ] **Step 4: 更新调课标签颜色**

查找调课类型标签定义：
```bash
grep -B 2 -A 5 "modify\|makeup\|cancel" frontend-v3/src/views/teacher/Schedules.vue | head -40
```

将标签颜色改为：
- 调课: Indigo 主色
- 补课: Warning 琥珀色
- 停课: Error 红色

```typescript
const adjustmentTypeColors = {
  modify: 'text-indigo-300 bg-indigo-500/10 border-indigo-500/30',
  makeup: 'text-amber-300 bg-amber-500/10 border-amber-500/30',
  cancel: 'text-red-300 bg-red-500/10 border-red-500/30',
}
```

- [ ] **Step 5: 运行类型检查**

```bash
cd frontend-v3 && npx vue-tsc --noEmit 2>&1 | head -20
```

- [ ] **Step 6: Commit**

```bash
git add frontend-v3/src/views/teacher/Schedules.vue
git commit -m "refactor(schedules): 简化课程表颜色为 Indigo 单色系

- 课程颜色统一使用 Indigo 不同透明度
- 调课标签简化为 Indigo/Warning/Error 三色
- 移除蓝绿紫橙随机颜色分配"
```

---

## Task 5: 更新 Badge 组件颜色变体

**Files:**
- Modify: `frontend-v3/src/components/ui/Badge.vue`

- [ ] **Step 1: 查看 Badge 组件当前实现**

```bash
cat frontend-v3/src/components/ui/Badge.vue
```

- [ ] **Step 2: 精简颜色变体**

如果 Badge 组件有 variant 属性，简化为：
- `default` - 中性灰色
- `primary` - Indigo 主色
- `success` - 成功绿色
- `warning` - 警告琥珀色
- `error` - 错误红色

移除 `blue`, `green`, `purple`, `orange` 等多余变体。

- [ ] **Step 3: Commit**

```bash
git add frontend-v3/src/components/ui/Badge.vue
git commit -m "refactor(badge): 精简颜色变体为 5 种标准色

- 保留 default/primary/success/warning/error
- 移除 blue/green/purple/orange 变体"
```

---

## Task 6: 运行前端测试

**Files:**
- Test: `frontend-v3/test/`

- [ ] **Step 1: 运行所有前端测试**

```bash
cd frontend-v3 && pnpm test:run
```

- [ ] **Step 2: 检查是否有样式相关测试失败**

```bash
cd frontend-v3 && pnpm test:run 2>&1 | grep -E "FAIL|Error|failed"
```

- [ ] **Step 3: 如有失败，修复测试**

检查失败测试是否期望了旧的颜色值，更新期望值。

- [ ] **Step 4: Commit 测试修复**

```bash
git add frontend-v3/test/
git commit -m "test: 更新颜色相关测试期望值" || echo "No test changes"
```

---

## Task 7: 最终验证

- [ ] **Step 1: 启动开发服务器**

```bash
cd frontend-v3 && pnpm dev &
sleep 5
echo "Server started"
```

- [ ] **Step 2: 检查页面颜色**

访问 http://localhost:5173 并验证：
- 统计卡片统一为 Indigo 色
- 课程表不再有多彩颜色
- 状态指示器语义清晰

- [ ] **Step 3: 运行构建检查**

```bash
cd frontend-v3 && pnpm build 2>&1 | tail -20
```

- [ ] **Step 4: Commit 最终验证**

```bash
git log --oneline -5
```

---

## 成功标准

- [ ] `tokens.css` 只包含 Indigo/Neutral/Success/Warning/Error 五组卡片颜色
- [ ] Admin Dashboard 统计卡片统一为 Indigo
- [ ] Teacher Dashboard 统计卡片统一为 Indigo
- [ ] 课程表使用 Indigo 单色系
- [ ] Badge 组件颜色变体精简为 5 种
- [ ] 所有前端测试通过
- [ ] 构建成功无错误

---

## 回滚计划

如果发现问题，可以按提交顺序回滚：

```bash
# 查看提交历史
git log --oneline -10

# 回滚到特定提交
git reset --hard <commit-hash>
```
