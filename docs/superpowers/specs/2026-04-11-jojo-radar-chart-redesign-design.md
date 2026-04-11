# JoJo 雷达图 1:1 还原设计文档

## 目标

将现有 `JojoRadarChart.vue` 的绘制样式完全替换为参考图（JoJo 替身六维面板）风格，同时保留项目的动态数据绑定能力。

## 需求确认

| 问题 | 决策 |
|------|------|
| 样式策略 | 完全替代现有雷达图样式 |
| 刻度表示 | 使用实际数值（0-100）替代 A-E 字母 |
| 维度标签 | 继续使用任务配置的动态维度名 |
| 数据层数 | 仅显示一层：**最终得分** |
| 实现方式 | 方式 2：将绘制逻辑拆分为独立函数，提升可维护性 |

## 视觉设计规范

### 1. 外边框（`drawOuterRing`）

- 在半径 `r + 40` 处绘制圆环
- 使用 `createLinearGradient` 模拟金属光泽（灰-白-灰渐变）
- 外侧加 `lineWidth = 2` 的深色描边（`#333`）

### 2. 内部背景（`drawInnerBackground`）

- 清除现有纸张噪点纹理
- 使用 `createRadialGradient` 绘制径向渐变背景
  - 中心色：`#ffffe0`（浅黄）
  - 中间色（70%）：`#fffacd`
  - 边缘色：`#ffe4b5`（稍深的黄色）
- 内边缘加 `lineWidth = 1` 的灰色描边（`#666`）

### 3. 网格与刻度（`drawGrid`）

- **同心圆**：绘制 5 层线框圆环，不填充，仅描边（`rgba(0,0,0,0.2)`）
- **放射轴线**：从圆心向 6 个维度方向延伸（`rgba(0,0,0,0.4)`）
- **轴线小刻度**：在每条轴线的 5 个等分点处绘制垂直于轴线的短横线（3px）
- **刻度数值**：在垂直轴（正上方）左侧依次标出 20/40/60/80/100

### 4. 数据多边形（`drawDataPolygon`）

- 仅接收 `finalScores` 一套数据
- 将 0-100 映射到最大半径 `r`
- 绘制闭合红色多边形
  - 填充色：`rgba(220, 50, 60, 0.6)`
  - 描边色：`#1a1a1a`
  - 描边宽度：2
- **移除**顶点白点标记

### 5. 维度标签（`drawLabels`）

- 使用传入的 `dimensions` 动态数组
- 标签位置放在轴线外侧（`r + 28` 处）
- 字体：bold 13px "Noto Sans SC", "Microsoft YaHei", sans-serif
- 颜色：`#1a1a1a`
- **保留** hover 高亮效果（hover 时轴线加粗、标签变红并有金色光晕）

## 动画

- 保留现有的入场动画（`coinFlip` 硬币翻转）
- 保留 `animationProgress` 驱动的多边形展开动画（`easeOutBack`）

## 组件 Props 变更

```ts
const props = defineProps<{
  dimensions: string[]
  finalScores: number[]
  groupName?: string
}>()
```

- **移除**：`teacherScores`、`peerScores`
- **保留并改为必填**：`finalScores`（替代原有的可选 finalScores）

## 调用方影响

- `GroupResults.vue` 和 `GroupTaskResults.vue` 当前仍传入 `teacherScores` / `peerScores`，本阶段**不强制修改页面组件传参逻辑**，组件内部仅消费 `finalScores`。
- 若调用方未传 `finalScores`，雷达图仅绘制背景和网格，不显示数据多边形。

## 测试更新

- 更新 `JojoRadarChart.spec.ts`
  - 移除 `teacherScores` / `peerScores` 相关 props
  - 新增仅传入 `dimensions` + `finalScores` + `groupName` 的渲染测试用例

## 文件变更清单

| 文件 | 操作 |
|------|------|
| `frontend-v3/src/features/group-collaboration/components/JojoRadarChart.vue` | 重写绘制逻辑，拆分函数，更新 props |
| `frontend-v3/test/features/group-collaboration/JojoRadarChart.spec.ts` | 更新测试 props |

## 不纳入本次范围

- 修改 `GroupResults.vue` / `GroupTaskResults.vue` 的页面布局
- 后端 API 变更
- 新增配置开关或多主题支持
