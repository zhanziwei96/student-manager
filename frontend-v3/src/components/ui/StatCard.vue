<script setup lang="ts">
import { Card, Badge } from './index'
import type { Component, CSSProperties } from 'vue'
import { computed } from 'vue'

/**
 * 统计卡片组件
 *
 * 通用的统计数据展示卡片，用于 Dashboard 页面
 * 支持 CSS 变量主题色
 */

type CardColor = 'indigo' | 'neutral' | 'success' | 'warning' | 'error'

interface Props {
  title: string
  value: string | number
  icon: Component
  trend?: string
  color?: CardColor
  link?: string
}

const props = withDefaults(defineProps<Props>(), {
  trend: '',
  color: 'indigo',
  link: '',
})

const emit = defineEmits<{
  click: []
}>()

// 获取卡片样式 - 使用 CSS 变量
const cardStyle = computed<CSSProperties>(() => {
  const varPrefix = `--card-${props.color}`
  return {
    backgroundColor: `var(${varPrefix}-bg)`,
    borderColor: `var(${varPrefix}-border)`,
    '--tw-shadow-color': `var(${varPrefix}-shadow)`,
  } as CSSProperties
})

const iconStyle = computed<CSSProperties>(() => {
  const varPrefix = `--card-${props.color}`
  return {
    backgroundColor: `var(${varPrefix}-icon-bg)`,
    color: `var(${varPrefix}-icon-text)`,
  }
})

const glowStyle = computed<CSSProperties>(() => {
  const varPrefix = `--card-${props.color}`
  return {
    backgroundColor: `var(${varPrefix}-glow)`,
  }
})

const textMutedColor = computed(() => {
  const colors: Record<CardColor, string> = {
    indigo: 'text-indigo-200/80',
    neutral: 'text-white/60',
    success: 'text-green-200/80',
    warning: 'text-amber-200/80',
    error: 'text-red-200/80',
  }
  return colors[props.color]
})

const trendBadgeStyle = computed<CSSProperties>(() => {
  const varPrefix = `--card-${props.color}`
  return {
    backgroundColor: `var(${varPrefix}-icon-bg)`,
    color: `var(${varPrefix}-icon-text)`,
  }
})
</script>

<template>
  <Card
    class="group relative overflow-hidden p-6 shadow-lg transition-all duration-300 hover:scale-[1.02]"
    :class="link ? 'cursor-pointer' : ''"
    :style="cardStyle"
    @click="link ? emit('click') : null"
  >
    <div class="relative z-10">
      <div class="flex items-start justify-between">
        <div>
          <p class="mt-3 text-xs font-medium" :class="textMutedColor">
            {{ title }}
          </p>
          <p class="mt-1 text-3xl font-bold text-white">
            {{ value }}
          </p>
        </div>
        <div
          class="flex h-10 w-10 items-center justify-center rounded-xl shadow-inner transition-transform group-hover:scale-110"
          :style="iconStyle"
        >
          <component
            :is="icon"
            class="h-5 w-5"
          />
        </div>
      </div>
      <div
        v-if="trend"
        class="mt-4 flex items-center gap-2"
      >
        <Badge
          class="text-xs px-2 py-0.5 border-0"
          :style="trendBadgeStyle"
        >
          {{ trend }}
        </Badge>
        <span class="text-xs text-white/40">较上月</span>
      </div>
      <div
        v-else-if="link"
        class="mt-4"
      >
        <span class="text-sm text-primary hover:text-primary/80">
          查看详情 →
        </span>
      </div>
    </div>
    <!-- 背景装饰 -->
    <div
      class="absolute -right-4 -bottom-4 h-16 w-16 rounded-full blur-2xl transition-colors opacity-30"
      :style="glowStyle"
    />
  </Card>
</template>
