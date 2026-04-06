# MobilePicker 组件设计文档

> **移动端底部弹窗选择器组件设计方案**

---

## 背景与问题

当前项目中存在多种选择器实现方式混用：
- 原生 `<select>`：样式不可控，iOS 滚轮体验差
- `SearchableSelect.vue`：下拉面板在移动端容易被截断
- 需要统一、移动端友好的选择器组件

## 设计目标

1. **移动端优先**：底部弹窗交互，符合 iOS/Android 用户习惯
2. **大列表支持**：20+ 选项流畅滚动，支持搜索过滤
3. **主题一致**：完全支持暗黑主题，与应用设计系统统一
4. **渐进增强**：桌面端保持可用，移动端体验最佳

---

## 组件规格

### Props 接口

```typescript
interface MobilePickerOption {
  value: string | number
  label: string
  subtitle?: string    // 副标题，如"本周"
  disabled?: boolean
}

interface MobilePickerProps {
  modelValue?: string | number
  options: MobilePickerOption[]
  title?: string                    // 弹窗标题
  placeholder?: string              // 触发按钮占位符
  disabled?: boolean
  searchable?: boolean              // 是否启用搜索
  searchPlaceholder?: string        // 搜索框占位符
  clearable?: boolean               // 是否可清空
}
```

### Events

```typescript
interface MobilePickerEmits {
  'update:modelValue': (value: string | number | undefined) => void
  'change': (value: string | number | undefined, option: MobilePickerOption) => void
}
```

---

## 交互设计

### 1. 触发器（Trigger）

```
┌─────────────────────────────────────┐
│ 选择周次                    ▼       │  ← 未选择状态
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ 第 8 周 (本周)              ▼       │  ← 已选择状态（显示副标题）
└─────────────────────────────────────┘
```

**样式规范**：
- 宽度：100%
- 高度：44px（移动端触摸目标）
- 边框：1px solid rgba(255,255,255,0.1)
- 背景：rgba(255,255,255,0.05)
- 圆角：8px
- 文字：白色，16px

### 2. 底部弹窗（Mobile Bottom Sheet）

```
┌─────────────────────────────────────┐
│                                     │  ← 遮罩层（半透明黑色）
│    ┌─────────────────────────┐      │
│    │ ───── 指示条 ─────      │      │  ← 可拖拽关闭
│    │ 选择周次           完成 │      │  ← 标题栏
│    ├─────────────────────────┤      │
│    │ 🔍 搜索周次...          │      │  ← 搜索框（可选）
│    ├─────────────────────────┤      │
│    │ 第 6 周                 │      │
│    │ 第 7 周                 │      │
│    │ ✓ 第 8 周            本周│      │  ← 当前选中项
│    │ 第 9 周                 │      │
│    │ ...                     │      │
│    └─────────────────────────┘      │
│                                     │
└─────────────────────────────────────┘
```

**弹窗规格**：
- 位置：底部固定
- 圆角：20px 20px 0 0
- 背景：#1a1a2e
- 最大高度：屏幕高度的 70%
- 动画：从底部滑入 200ms ease-out

### 3. 桌面端回退（Desktop Fallback）

桌面端（屏幕宽度 ≥ 768px）使用传统下拉面板：
- 固定在触发器下方
- 最大高度 300px
- 支持键盘导航（↑↓ 选择，Enter 确认，Esc 关闭）

---

## 使用场景

### 场景 1：周次选择（Schedules.vue）

```vue
<MobilePicker
  v-model="selectedWeek"
  title="选择周次"
  placeholder="全部周次"
  searchable
  clearable
  :options="weekOptions.map(w => ({
    value: w,
    label: `第${w}周`,
    subtitle: w === currentWeek ? '本周' : undefined
  }))"
/>
```

### 场景 2：班级选择（ClassSession.vue）

```vue
<MobilePicker
  v-model="selectedClass"
  title="选择班级"
  placeholder="请选择班级"
  :options="classes.map(c => ({
    value: c.name,
    label: c.name
  }))"
/>
```

### 场景 3：签到筛选（Checkins.vue）

```vue
<MobilePicker
  v-model="selectedClass"
  title="筛选班级"
  placeholder="全部班级"
  clearable
  :options="classOptions"
/>
```

---

## 技术实现

### 文件结构

```
frontend-v3/src/components/ui/
├── MobilePicker/
│   ├── MobilePicker.vue      # 主组件
│   ├── MobilePickerTrigger.vue   # 触发器
│   ├── MobilePickerSheet.vue     # 底部弹窗
│   └── useMobilePicker.ts        # 组合式函数
```

### 响应式断点

```typescript
// 使用 CSS 媒体查询或 JS 检测
const isMobile = computed(() => window.innerWidth < 768)
```

### 手势支持

- **点击触发器**：打开弹窗
- **点击遮罩**：关闭弹窗
- **下滑指示条**：关闭弹窗
- **点击选项**：选择并关闭
- **点击完成按钮**：关闭弹窗

### 动画规格

```css
/* 弹窗滑入 */
@keyframes slideUp {
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

/* 遮罩淡入 */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.sheet {
  animation: slideUp 200ms ease-out;
}

.overlay {
  animation: fadeIn 150ms ease-out;
}
```

---

## 无障碍（A11y）

- 弹窗打开时焦点转移到搜索框或第一个选项
- 支持键盘导航（↑↓ 移动，Enter 选择，Esc 关闭）
- 遮罩层阻止背景滚动
- 正确的 ARIA 标签（`role="dialog"`, `aria-modal="true"`）

---

## 浏览器兼容性

| 浏览器 | 版本 | 支持状态 |
|--------|------|----------|
| Safari (iOS) | 14+ | ✅ 完全支持 |
| Chrome (Android) | 90+ | ✅ 完全支持 |
| Chrome (Desktop) | 90+ | ✅ 完全支持 |
| Safari (macOS) | 14+ | ✅ 完全支持 |
| Firefox | 88+ | ✅ 完全支持 |

---

## 替代方案对比

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| 原生 Select | 系统级辅助功能 | iOS 滚轮体验差，样式不可控 | ❌ 不采用 |
| 底部弹窗（本方案） | 移动端体验好，完全可定制 | 需要额外实现 | ✅ **采用** |
| 传统下拉面板 | Desktop 一致性好 | 移动端容易被截断 | ❌ 不采用 |

---

## 实施计划

1. **Phase 1**：实现基础 MobilePicker 组件
2. **Phase 2**：添加搜索功能
3. **Phase 3**：替换 Schedules.vue 中的原生 select
4. **Phase 4**：替换其他页面中的不一致选择器

---

**设计文档版本**: 1.0  
**最后更新**: 2026-04-06  
**状态**: 待实现
