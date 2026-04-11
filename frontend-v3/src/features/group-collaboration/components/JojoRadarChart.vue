<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'

const props = defineProps<{
  dimensions: string[]
  finalScores: number[]
  groupName?: string
}>()

const canvasRef = ref<HTMLCanvasElement | null>(null)
const containerRef = ref<HTMLDivElement | null>(null)

const canvasSize = ref({ width: 800, height: 800 })
const hoveredIndex = ref<number | null>(null)
const animationProgress = ref(0)
const coinDone = ref(false)

let rafId: number | null = null
let resizeObserver: ResizeObserver | null = null

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

function easeOutBack(t: number): number {
  const c1 = 1.70158
  const c3 = c1 + 1
  return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2)
}

function setupCanvas() {
  const canvas = canvasRef.value
  const container = containerRef.value
  if (!canvas || !container) return

  const rect = container.getBoundingClientRect()
  // 正方形：取宽高最小值
  const size = Math.floor(Math.min(rect.width, rect.height))
  const ratio = window.devicePixelRatio || 1

  canvasSize.value = { width: size, height: size }

  canvas.width = size * ratio
  canvas.height = size * ratio
  canvas.style.width = `${size}px`
  canvas.style.height = `${size}px`

  const ctx = canvas.getContext('2d')
  if (!ctx) return
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0)
}

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
  } else {
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.font = '14px "Noto Sans SC", "Microsoft YaHei", sans-serif'
    ctx.fillStyle = '#666'
    ctx.fillText('至少需要 3 个维度', cx, cy)
  }
}

function animate() {
  if (animationProgress.value >= 1) {
    animationProgress.value = 1
    draw()
    return
  }
  animationProgress.value += 0.024
  if (animationProgress.value > 1) animationProgress.value = 1
  draw()
  rafId = requestAnimationFrame(animate)
}

function startAnimation() {
  animationProgress.value = 0
  if (rafId) cancelAnimationFrame(rafId)
  rafId = requestAnimationFrame(animate)
}

function onCoinDone() {
  coinDone.value = true
  startAnimation()
}

function onMouseMove(e: MouseEvent) {
  const canvas = canvasRef.value
  if (!canvas) return
  const rect = canvas.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top
  const { width, height } = canvasSize.value
  const cx = width / 2
  const cy = height / 2
  const labelRadius = Math.min(width, height) * 0.30 + 28

  const dims = props.dimensions || []
  let found: number | null = null
  for (let i = 0; i < dims.length; i++) {
    const a = -Math.PI / 2 + (Math.PI * 2 * i) / dims.length
    const lx = cx + Math.cos(a) * labelRadius
    const ly = cy + Math.sin(a) * labelRadius
    const dx = x - lx
    const dy = y - ly
    if (dx * dx + dy * dy < 900) {
      found = i
      break
    }
  }
  if (found !== hoveredIndex.value) {
    hoveredIndex.value = found
    draw()
  }
}

function onMouseLeave() {
  if (hoveredIndex.value !== null) {
    hoveredIndex.value = null
    draw()
  }
}

onMounted(() => {
  setupCanvas()

  const canvas = canvasRef.value
  canvas?.addEventListener('mousemove', onMouseMove)
  canvas?.addEventListener('mouseleave', onMouseLeave)

  if (typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(() => {
      setupCanvas()
      draw()
    })
    if (containerRef.value) resizeObserver.observe(containerRef.value)
  }
})

onUnmounted(() => {
  if (rafId) cancelAnimationFrame(rafId)
  resizeObserver?.disconnect()
  const canvas = canvasRef.value
  canvas?.removeEventListener('mousemove', onMouseMove)
  canvas?.removeEventListener('mouseleave', onMouseLeave)
})

watch(
  () => [props.dimensions, props.finalScores, props.groupName],
  () => {
    // 重置硬币动画
    coinDone.value = false
    startAnimation()
  },
  { deep: true },
)
</script>

<template>
  <div class="jojo-radar-wrapper flex items-center justify-center">
    <div
      ref="containerRef"
      class="jojo-radar-chart relative overflow-hidden"
      :class="{ 'coin-enter': !coinDone }"
      :style="{ width: '100%', aspectRatio: '1 / 1' }"
      @animationend="onCoinDone"
    >
      <canvas ref="canvasRef" class="block w-full h-full" />
    </div>
  </div>
</template>

<style scoped>
.jojo-radar-chart {
  border-radius: 50%;
  box-shadow: inset 0 0 24px rgba(0, 0, 0, 0.08), 0 4px 14px rgba(0, 0, 0, 0.12);
}

.jojo-radar-chart.coin-enter {
  animation: coinFlip 1s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}

@keyframes coinFlip {
  0% {
    transform: perspective(800px) rotateY(0deg);
    opacity: 0.3;
  }
  30% {
    transform: perspective(800px) rotateY(540deg);
    opacity: 0.7;
  }
  60% {
    transform: perspective(800px) rotateY(900deg);
    opacity: 0.9;
  }
  80% {
    transform: perspective(800px) rotateY(1040deg);
    opacity: 1;
  }
  100% {
    transform: perspective(800px) rotateY(1080deg);
    opacity: 1;
  }
}
</style>
