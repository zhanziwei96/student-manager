<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps<{
  dimensions: string[]
  teacherScores: number[]
  peerScores: number[]
}>()

const chartRef = ref<HTMLDivElement | null>(null)
let chartInstance: echarts.ECharts | null = null

function hasCanvasSupport(): boolean {
  try {
    const canvas = document.createElement('canvas')
    return !!canvas.getContext('2d')
  } catch {
    return false
  }
}

function initChart() {
  if (!chartRef.value || !hasCanvasSupport()) return
  chartInstance = echarts.init(chartRef.value, undefined, { renderer: 'canvas' })
  updateChart()
}

function updateChart() {
  if (!chartInstance) return

  const option: echarts.EChartsOption = {
    // 深色背景
    backgroundColor: 'transparent',

    // 雷达配置 —— 替身面板圆形风格
    radar: {
      indicator: props.dimensions.map((name) => ({ name, max: 100 })),
      shape: 'circle',
      splitNumber: 5,
      radius: '68%',
      center: ['50%', '48%'],

      // 轴名称：粗体锐利字体，金属白
      axisName: {
        color: '#e8e6e3',
        fontWeight: 900,
        fontSize: 14,
        fontFamily: '"Noto Sans SC", "Impact", "Arial Black", sans-serif',
        textShadowColor: 'rgba(163, 130, 255, 0.8)',
        textShadowBlur: 6,
      },

      // 同心圆分隔线：银灰金属感 + 辉光
      splitLine: {
        lineStyle: {
          color: '#8a8a8a',
          width: 1.5,
          opacity: 0.5,
          shadowColor: 'rgba(180, 160, 220, 0.4)',
          shadowBlur: 4,
        },
      },

      // 同心圆区域填充：金色渐变能量核心
      splitArea: {
        show: true,
        areaStyle: {
          color: [
            'rgba(255, 215, 0, 0.04)',
            'rgba(255, 200, 0, 0.07)',
            'rgba(255, 185, 0, 0.10)',
            'rgba(255, 170, 0, 0.14)',
            'rgba(255, 155, 0, 0.18)',
          ],
        },
      },

      // 径向轴线：金属银线
      axisLine: {
        lineStyle: {
          color: '#9a9a9a',
          width: 1.5,
          opacity: 0.6,
          shadowColor: 'rgba(163, 130, 255, 0.3)',
          shadowBlur: 3,
        },
      },
    },

    // 装饰性图形：外圈辉光环
    graphic: [
      // 外圈金属环
      {
        type: 'circle',
        shape: { cx: '50%', cy: '48%', r: '71%' },
        style: {
          stroke: 'rgba(200, 180, 230, 0.35)',
          lineWidth: 3,
          shadowColor: 'rgba(140, 100, 255, 0.6)',
          shadowBlur: 15,
          fill: 'none',
        },
        silent: true,
      },
      // 最外层辉光
      {
        type: 'circle',
        shape: { cx: '50%', cy: '48%', r: '74%' },
        style: {
          stroke: 'rgba(180, 150, 255, 0.15)',
          lineWidth: 1,
          shadowColor: 'rgba(140, 100, 255, 0.3)',
          shadowBlur: 20,
          fill: 'none',
        },
        silent: true,
      },
    ],

    series: [
      {
        type: 'radar',
        data: [
          {
            value: props.teacherScores,
            name: '教师评分',
            symbol: 'diamond',
            symbolSize: 10,
            lineStyle: {
              color: '#ff4757',
              width: 2.5,
              shadowColor: 'rgba(255, 71, 87, 0.6)',
              shadowBlur: 8,
            },
            itemStyle: {
              color: '#ff4757',
              borderColor: '#ff6b81',
              borderWidth: 1.5,
              shadowColor: 'rgba(255, 71, 87, 0.8)',
              shadowBlur: 6,
            },
            areaStyle: {
              color: new echarts.graphic.RadialGradient(0.5, 0.5, 1, [
                { offset: 0, color: 'rgba(255, 71, 87, 0.35)' },
                { offset: 1, color: 'rgba(255, 71, 87, 0.05)' },
              ]),
            },
          },
          {
            value: props.peerScores,
            name: '组外学生评分',
            symbol: 'diamond',
            symbolSize: 10,
            lineStyle: {
              color: '#ffd32a',
              width: 2.5,
              shadowColor: 'rgba(255, 211, 42, 0.6)',
              shadowBlur: 8,
            },
            itemStyle: {
              color: '#ffd32a',
              borderColor: '#fff200',
              borderWidth: 1.5,
              shadowColor: 'rgba(255, 211, 42, 0.8)',
              shadowBlur: 6,
            },
            areaStyle: {
              color: new echarts.graphic.RadialGradient(0.5, 0.5, 1, [
                { offset: 0, color: 'rgba(255, 211, 42, 0.25)' },
                { offset: 1, color: 'rgba(255, 211, 42, 0.03)' },
              ]),
            },
          },
        ],
      },
    ],

    // 图例：动漫风格
    legend: {
      data: ['教师评分', '组外学生评分'],
      bottom: 4,
      textStyle: {
        color: '#d4d0cb',
        fontWeight: 'bold',
        fontSize: 13,
        fontFamily: '"Noto Sans SC", "Arial Black", sans-serif',
        textShadowColor: 'rgba(163, 130, 255, 0.5)',
        textShadowBlur: 4,
      },
      itemGap: 24,
      itemWidth: 18,
      itemHeight: 10,
    },
  }

  chartInstance.setOption(option, true)
}

function handleResize() {
  chartInstance?.resize()
}

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
  chartInstance = null
})

watch(() => [props.dimensions, props.teacherScores, props.peerScores], updateChart, { deep: true })
</script>

<template>
  <div
    ref="chartRef"
    class="jojo-stand-panel w-full"
  />
</template>

<style scoped>
.jojo-stand-panel {
  background:
    radial-gradient(
      ellipse at 50% 48%,
      rgba(60, 30, 90, 0.25) 0%,
      rgba(25, 15, 50, 0.5) 45%,
      rgba(10, 5, 20, 0.85) 80%,
      rgba(5, 2, 10, 1) 100%
    );
  border-radius: 12px;
  border: 2px solid rgba(120, 90, 180, 0.3);
  box-shadow:
    0 0 20px rgba(100, 60, 200, 0.25),
    inset 0 0 30px rgba(80, 40, 160, 0.15);
  padding: 8px;
}
</style>
