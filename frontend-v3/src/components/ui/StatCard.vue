<script setup lang="ts">
import { Card } from './index'
import type { Component } from 'vue'
import { computed } from 'vue'

/**
 * 统计卡片组件
 *
 * 通用的统计数据展示卡片，用于 Dashboard 页面
 * Ollama 白色主题设计
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

// 图标背景色和文字色映射
const iconColorClasses = computed(() => {
  const colors: Record<CardColor, { bg: string; text: string }> = {
    indigo: { bg: 'bg-[#e5e5e5]', text: 'text-[#404040]' },
    neutral: { bg: 'bg-[#e5e5e5]', text: 'text-[#404040]' },
    success: { bg: 'bg-green-100', text: 'text-green-600' },
    warning: { bg: 'bg-amber-100', text: 'text-amber-600' },
    error: { bg: 'bg-red-100', text: 'text-red-600' },
  }
  return colors[props.color]
})

// 趋势标签色映射
const trendColorClasses = computed(() => {
  const colors: Record<CardColor, string> = {
    indigo: 'bg-[#e5e5e5] text-[#404040]',
    neutral: 'bg-[#e5e5e5] text-[#404040]',
    success: 'bg-green-100 text-green-600',
    warning: 'bg-amber-100 text-amber-600',
    error: 'bg-red-100 text-red-600',
  }
  return colors[props.color]
})
</script>

<template>
  <Card
    class="relative overflow-hidden p-6"
    :class="link ? 'cursor-pointer' : ''"
    @click="link ? emit('click') : null"
  >
    <div class="relative z-10">
      <div class="flex items-start justify-between">
        <div>
          <p class="mt-3 text-xs font-medium text-[#737373]">
            {{ title }}
          </p>
          <p class="mt-1 text-3xl font-medium text-black">
            {{ value }}
          </p>
        </div>
        <div
          class="flex h-10 w-10 items-center justify-center rounded-xl"
          :class="[iconColorClasses.bg, iconColorClasses.text]"
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
        <span
          class="text-xs px-2 py-0.5 rounded-full"
          :class="trendColorClasses"
        >
          {{ trend }}
        </span>
        <span class="text-xs text-[#a3a3a3]">较上月</span>
      </div>
      <div
        v-else-if="link"
        class="mt-4"
      >
        <span class="text-sm text-black hover:text-[#737373]">
          查看详情 →
        </span>
      </div>
    </div>
  </Card>
</template>
