<script setup lang="ts">
import { computed } from 'vue'
import { cn } from '@/lib/utils'

/**
 * Card 组件
 * 基于 ClassHub 设计体系 v1.0.0
 */

interface Props {
  class?: string
  variant?: 'default' | 'elevated' | 'glass' | 'active'
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
})

const variantClasses = {
  // 默认卡片: 轻微透明背景
  default: 'bg-white/[0.02] border-border hover:border-border-hover',
  
  // 提升卡片: 更深的背景色
  elevated: 'bg-background-elevated border-border',
  
  // 玻璃卡片: 毛玻璃效果
  glass: 'bg-white/5 backdrop-blur-lg border-white/15',
  
  // 激活卡片: 主色边框和背景
  active: 'bg-primary/10 border-primary',
}

const classes = computed(() =>
  cn(
    'rounded-xl border p-4 md:p-6 text-white',
    'transition-all duration-200 ease-out',
    variantClasses[props.variant],
    props.class
  )
)
</script>

<template>
  <div :class="classes">
    <slot />
  </div>
</template>
