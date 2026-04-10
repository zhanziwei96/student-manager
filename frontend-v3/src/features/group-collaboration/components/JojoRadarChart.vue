<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
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
  chartInstance = echarts.init(chartRef.value)
  updateChart()
}

function updateChart() {
  if (!chartInstance) return
  const option: echarts.EChartsOption = {
    radar: {
      indicator: props.dimensions.map((name) => ({ name, max: 100 })),
      shape: 'polygon',
      splitNumber: 4,
      axisName: { color: '#262626', fontWeight: 'bold' },
      splitLine: { lineStyle: { color: '#262626', width: 2, opacity: 0.3 } },
      splitArea: { show: false },
      axisLine: { lineStyle: { color: '#262626', width: 2, opacity: 0.3 } },
    },
    series: [
      {
        type: 'radar',
        data: [
          {
            value: props.teacherScores,
            name: '教师评分',
            symbol: 'diamond',
            symbolSize: 8,
            lineStyle: { color: '#6366f1', width: 3 },
            itemStyle: { color: '#6366f1' },
            areaStyle: { color: 'rgba(99, 102, 241, 0.25)' },
          },
          {
            value: props.peerScores,
            name: '组外学生评分',
            symbol: 'diamond',
            symbolSize: 8,
            lineStyle: { color: '#10b981', width: 3 },
            itemStyle: { color: '#10b981' },
            areaStyle: { color: 'rgba(16, 185, 129, 0.25)' },
          },
        ],
      },
    ],
    legend: { data: ['教师评分', '组外学生评分'], bottom: 0, textStyle: { color: '#262626' } },
  }
  chartInstance.setOption(option)
}

onMounted(initChart)
watch(() => [props.dimensions, props.teacherScores, props.peerScores], updateChart, { deep: true })
</script>

<template>
  <div ref="chartRef" class="h-80 w-full" />
</template>
