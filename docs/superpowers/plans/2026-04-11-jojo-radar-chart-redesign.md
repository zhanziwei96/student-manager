# JoJo Radar Chart Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite `JojoRadarChart.vue` to match the JoJo reference image style while maintaining dynamic dimensions and only displaying `finalScores`.

**Architecture:** Replace the existing flat paper/metal style with the reference image's layered metal ring, radial yellow gradient, wireframe grid with tick marks, and red data polygon. Keep the coin-flip entry animation and hover interactions.

**Tech Stack:** Vue 3.5 + TypeScript, Canvas 2D API, Vitest

---

## File Structure

| File | Responsibility |
|------|----------------|
| `frontend-v3/src/features/group-collaboration/components/JojoRadarChart.vue` | Single-file Vue component: canvas setup, prop definitions, JoJo-style draw functions, animation, hover interactions |
| `frontend-v3/test/features/group-collaboration/JojoRadarChart.spec.ts` | Component mount tests verifying props and DOM structure |

---

## Task 1: Update Tests to Match New Props

**Files:**
- Modify: `frontend-v3/test/features/group-collaboration/JojoRadarChart.spec.ts`

- [ ] **Step 1: Replace test content to use new props**

Replace the existing test file with the following. This removes `teacherScores` and `peerScores` and validates the new required `finalScores` prop.

```typescript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import JojoRadarChart from '@/features/group-collaboration/components/JojoRadarChart.vue'

describe('JojoRadarChart', () => {
  it('renders canvas container with dimensions and finalScores', () => {
    const wrapper = mount(JojoRadarChart, {
      props: {
        dimensions: ['创意', '执行力'],
        finalScores: [80, 90],
        groupName: '测试组',
      },
    })
    expect(wrapper.find('canvas').exists()).toBe(true)
    expect(wrapper.find('.jojo-radar-chart').exists()).toBe(true)
  })

  it('renders with six dimensions', () => {
    const wrapper = mount(JojoRadarChart, {
      props: {
        dimensions: ['破坏力', '速度', '射程距离', '持续力', '精密动作性', '成长性'],
        finalScores: [80, 100, 40, 80, 100, 60],
        groupName: '替身小组',
      },
    })
    expect(wrapper.find('canvas').exists()).toBe(true)
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd /home/yufeng/student-manager/frontend-v3 && pnpm test:run test/features/group-collaboration/JojoRadarChart.spec.ts
```

Expected: Tests fail because `JojoRadarChart.vue` still defines `teacherScores`/`peerScores` as required and does not accept the new prop signature.

---

## Task 2: Rewrite JojoRadarChart.vue Draw Logic

**Files:**
- Modify: `frontend-v3/src/features/group-collaboration/components/JojoRadarChart.vue`

- [ ] **Step 1: Update props to remove teacherScores/peerScores and make finalScores required**

In the `<script setup lang="ts">` block, replace the `props` definition with:

```typescript
const props = defineProps<{
  dimensions: string[]
  finalScores: number[]
  groupName?: string
}>()
```

- [ ] **Step 2: Replace color constants**

Replace the `COLORS` object with:

```typescript
const COLORS = {
  paper: '#e8e4d9',
  ringFill1: 'rgba(255, 248, 150, 0.65)',
  ringFill2: 'rgba(255, 255, 220, 0.45)',
  ringStroke: '#5a5a5a',
  axisText: '#2a2a2a',
  dataFill: 'rgba(220, 50, 60, 0.6)',
  dataStroke: '#1a1a1a',
  dotFill: '#ffffff',
  dotStroke: '#1a1a1a',
  highlight: '#c9a227',
}
```

- [ ] **Step 3: Remove unused functions**

Delete the following functions entirely from the component:
- `drawPaperNoise`
- `drawCircularBorder`
- `drawDots`

Also delete the reference `const hasTeacher = tScores.some(...)` and `const hasPeer = pScores.some(...)` lines inside `draw()`.

- [ ] **Step 4: Add new drawing functions**

Insert the following functions after `setupCanvas` (or in any logical order before `draw`):

**`drawOuterRing`**
```typescript
function drawOuterRing(
  ctx: CanvasRenderingContext2D,
  cx: number,
  cy: number,
  radius: number,
) {
  ctx.beginPath()
  ctx.arc(cx, cy, radius + 40, 0, Math.PI * 2)

  const gradient = ctx.createLinearGradient(cx - radius - 40, cy - radius - 40, cx + radius + 40, cy + radius + 40)
  gradient.addColorStop(0, '#aaa')
  gradient.addColorStop(0.5, '#e0e0e0')
  gradient.addColorStop(1, '#888')

  ctx.fillStyle = gradient
  ctx.fill()

  ctx.strokeStyle = '#333'
  ctx.lineWidth = 2
  ctx.stroke()
}
```

**`drawInnerBackground`**
```typescript
function drawInnerBackground(
  ctx: CanvasRenderingContext2D,
  cx: number,
  cy: number,
  radius: number,
) {
  ctx.beginPath()
  ctx.arc(cx, cy, radius, 0, Math.PI * 2)

  const gradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius)
  gradient.addColorStop(0, '#ffffe0')
  gradient.addColorStop(0.7, '#fffacd')
  gradient.addColorStop(1, '#ffe4b5')

  ctx.fillStyle = gradient
  ctx.fill()

  ctx.strokeStyle = '#666'
  ctx.lineWidth = 1
  ctx.stroke()
}
```

**`drawGrid`** (rewrite the existing one completely)
```typescript
function drawGrid(
  ctx: CanvasRenderingContext2D,
  cx: number,
  cy: number,
  radius: number,
  count: number,
) {
  const angles = Array.from({ length: count }, (_, i) => -Math.PI / 2 + (Math.PI * 2 * i) / count)
  const levels = 5

  // concentric circles (wireframe only)
  ctx.strokeStyle = 'rgba(0, 0, 0, 0.2)'
  ctx.lineWidth = 1
  for (let l = 1; l <= levels; l++) {
    const r = (radius / levels) * l
    ctx.beginPath()
    ctx.arc(cx, cy, r, 0, Math.PI * 2)
    ctx.stroke()
  }

  // axis lines + tick marks
  ctx.strokeStyle = 'rgba(0, 0, 0, 0.4)'
  for (let i = 0; i < count; i++) {
    const a = angles[i]
    const isHover = hoveredIndex.value === i

    ctx.beginPath()
    ctx.moveTo(cx, cy)
    ctx.lineTo(cx + Math.cos(a) * radius, cy + Math.sin(a) * radius)
    ctx.lineWidth = isHover ? 3 : 1.2
    ctx.strokeStyle = isHover ? COLORS.highlight : 'rgba(0, 0, 0, 0.4)'
    ctx.stroke()

    for (let lv = 1; lv <= levels; lv++) {
      const tr = (radius / levels) * lv
      const tx = cx + Math.cos(a) * tr
      const ty = cy + Math.sin(a) * tr
      const tickAngle = a + Math.PI / 2

      ctx.beginPath()
      ctx.moveTo(tx + 3 * Math.cos(tickAngle), ty + 3 * Math.sin(tickAngle))
      ctx.lineTo(tx - 3 * Math.cos(tickAngle), ty - 3 * Math.sin(tickAngle))
      ctx.lineWidth = 1
      ctx.strokeStyle = 'rgba(0, 0, 0, 0.4)'
      ctx.stroke()
    }
  }

  // numeric labels on the vertical axis (left side)
  const labels = ['20', '40', '60', '80', '100']
  ctx.textAlign = 'right'
  ctx.textBaseline = 'middle'
  ctx.font = 'bold 11px Arial'
  ctx.fillStyle = '#333'
  for (let lv = 1; lv <= levels; lv++) {
    const r = (radius / levels) * lv
    const lx = cx - 5
    const ly = cy - r
    ctx.fillText(labels[lv - 1], lx, ly)
  }
}
```

**`drawDataPolygon`** (rewrite)
```typescript
function drawDataPolygon(
  ctx: CanvasRenderingContext2D,
  cx: number,
  cy: number,
  radius: number,
  scores: number[],
  progress: number,
) {
  const count = scores.length
  if (count === 0) return
  const angles = Array.from({ length: count }, (_, i) => -Math.PI / 2 + (Math.PI * 2 * i) / count)
  const scale = easeOutBack(progress)

  ctx.beginPath()
  for (let i = 0; i < count; i++) {
    const a = angles[i]
    const val = Math.min(100, Math.max(0, scores[i] ?? 0)) / 100
    const r = radius * val * scale
    const x = cx + Math.cos(a) * r
    const y = cy + Math.sin(a) * r
    if (i === 0) ctx.moveTo(x, y)
    else ctx.lineTo(x, y)
  }
  ctx.closePath()
  ctx.fillStyle = COLORS.dataFill
  ctx.fill()
  ctx.lineWidth = 2
  ctx.strokeStyle = COLORS.dataStroke
  ctx.stroke()
}
```

**`drawLabels`** (keep and adjust label radius)
```typescript
function drawLabels(
  ctx: CanvasRenderingContext2D,
  cx: number,
  cy: number,
  radius: number,
  dimensions: string[],
) {
  const count = dimensions.length
  const angles = Array.from({ length: count }, (_, i) => -Math.PI / 2 + (Math.PI * 2 * i) / count)
  const labelRadius = radius + 28

  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'

  for (let i = 0; i < count; i++) {
    const a = angles[i]
    const x = cx + Math.cos(a) * labelRadius
    const y = cy + Math.sin(a) * labelRadius
    const isHover = hoveredIndex.value === i

    ctx.font = 'bold 13px "Noto Sans SC", "Microsoft YaHei", sans-serif'
    ctx.fillStyle = isHover ? '#8B0000' : '#1a1a1a'
    if (isHover) {
      ctx.save()
      ctx.shadowColor = 'rgba(201, 162, 39, 0.9)'
      ctx.shadowBlur = 8
      ctx.fillText(dimensions[i], x, y)
      ctx.restore()
    } else {
      ctx.save()
      ctx.shadowColor = 'rgba(255,255,255,0.8)'
      ctx.shadowBlur = 4
      ctx.fillText(dimensions[i], x, y)
      ctx.restore()
    }
  }
}
```

- [ ] **Step 5: Rewrite the main `draw()` function**

Replace the entire `draw()` function body with:

```typescript
function draw() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const { width, height } = canvasSize.value
  const cx = width / 2
  const cy = height / 2
  const radius = Math.min(width, height) * 0.30

  ctx.clearRect(0, 0, width, height)

  const dims = props.dimensions || []
  const scores = props.finalScores || []

  if (dims.length > 2) {
    drawOuterRing(ctx, cx, cy, radius)
    drawInnerBackground(ctx, cx, cy, radius)
    drawGrid(ctx, cx, cy, radius, dims.length)
    drawDataPolygon(ctx, cx, cy, radius, scores, animationProgress.value)
    drawLabels(ctx, cx, cy, radius, dims)
  }
}
```

---

## Task 3: Run Tests and Verify

**Files:**
- Test: `frontend-v3/test/features/group-collaboration/JojoRadarChart.spec.ts`

- [ ] **Step 1: Run component tests**

Run:
```bash
cd /home/yufeng/student-manager/frontend-v3 && pnpm test:run test/features/group-collaboration/JojoRadarChart.spec.ts
```

Expected: All tests pass.

- [ ] **Step 2: Run full frontend test suite**

Run:
```bash
cd /home/yufeng/student-manager/frontend-v3 && pnpm test:run
```

Expected: No regressions in unrelated tests. If there are failures from previous state, note them but do not fix unrelated issues unless they were caused by this change.

---

## Task 4: Commit Changes

- [ ] **Step 1: Stage and commit**

Run:
```bash
cd /home/yufeng/student-manager
git add frontend-v3/src/features/group-collaboration/components/JojoRadarChart.vue
git add frontend-v3/test/features/group-collaboration/JojoRadarChart.spec.ts
git commit -m "feat: redesign JoJo radar chart to match reference style

- Replace flat paper style with metal ring + yellow radial gradient
- Switch to wireframe concentric grid with tick marks
- Display only finalScores as single red polygon
- Remove teacherScores/peerScores props and draw layers
- Update tests for new prop signature"
```

---

## Self-Review Checklist

**1. Spec coverage:**
- Metal outer ring → `drawOuterRing` in Task 2 Step 4
- Yellow radial background → `drawInnerBackground` in Task 2 Step 4
- Wireframe grid with tick marks and numeric labels → `drawGrid` in Task 2 Step 4
- Single red polygon for finalScores → `drawDataPolygon` in Task 2 Step 4
- Dynamic dimension labels → `drawLabels` in Task 2 Step 4
- Remove teacher/peer layers → props updated in Task 2 Step 1, `draw()` simplified in Task 2 Step 5
- Retain animations and hover → `animate()`, `startAnimation()`, hover handlers remain untouched
- Tests updated → Task 1

**2. Placeholder scan:**
- No TODOs, TBDs, or vague instruction steps present.
- All code blocks contain the actual implementation code.

**3. Type consistency:**
- Props updated consistently: `finalScores: number[]` is used in both component and tests.
- `drawDataPolygon` signature changed to remove unused fillStyle/strokeStyle/lineWidth parameters.
