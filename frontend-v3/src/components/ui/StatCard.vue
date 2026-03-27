<script setup lang="ts">
import { Card, Badge } from './index'
import type { Component } from 'vue'

/**
 * 统计卡片组件
 * 
 * 通用的统计数据展示卡片，用于 Dashboard 页面
 */

interface Props {
  title: string
  value: string | number
  icon: Component
  trend?: string
  color?: string
  link?: string
}

withDefaults(defineProps<Props>(), {
  trend: '',
  color: 'text-blue-400',
  link: '',
})

const emit = defineEmits<{
  click: []
}>()
</script>

<template>
  <Card
    class="group border-white/10 bg-white/[0.02] p-6 transition-colors hover:border-white/20"
    :class="link ? 'cursor-pointer' : ''"
    @click="link ? emit('click') : null"
  >
    <div class="flex items-center justify-between">
      <div>
        <p class="text-sm text-white/60">
          {{ title }}
        </p>
        <p class="mt-1 text-3xl font-bold text-white">
          {{ value }}
        </p>
      </div>
      <div :class="['rounded-lg bg-white/5 p-3 transition-colors group-hover:bg-white/10', color]">
        <component
          :is="icon"
          class="h-6 w-6"
        />
      </div>
    </div>
    <div
      v-if="trend"
      class="mt-4 flex items-center gap-2"
    >
      <Badge
        variant="secondary"
        class="text-xs"
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
  </Card>
</template>
