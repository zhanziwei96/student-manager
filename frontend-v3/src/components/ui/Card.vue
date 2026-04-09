<script setup lang="ts">
import { computed } from 'vue'
import { cn } from '@/lib/utils'

/**
 * Card 组件
 * Ollama 白色主题设计
 */

interface Props {
  class?: string
  variant?: 'default' | 'snow' | 'active'
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
})

const variantClasses = {
  // 默认卡片: 白色背景
  default: 'bg-white border-[#e5e5e5]',

  // 雪白卡片: 微灰背景
  snow: 'bg-[#fafafa] border-[#e5e5e5]',

  // 激活卡片: 灰色边框和背景
  active: 'bg-[#fafafa] border-[#d4d4d4]',
}

const classes = computed(() =>
  cn(
    'rounded-xl border p-4 md:p-6 text-black',
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
