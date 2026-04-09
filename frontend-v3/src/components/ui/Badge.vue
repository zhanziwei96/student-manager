<script setup lang="ts">
import { computed } from 'vue'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

/**
 * Badge 组件
 * Ollama 白色主题设计
 */

const badgeVariants = cva(
  'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium whitespace-nowrap',
  {
    variants: {
      variant: {
        // 默认标签 - 灰色
        default: 'bg-[#e5e5e5] text-[#262626]',

        // 成功状态
        success: 'bg-success/15 text-success',

        // 警告状态
        warning: 'bg-warning/15 text-warning',

        // 错误状态
        error: 'bg-error/15 text-error',

        // 信息状态
        info: 'bg-info/15 text-info',

        // 描边样式
        outline: 'border border-[#e5e5e5] text-[#737373] bg-transparent',

        // 次级标签
        secondary: 'bg-[#fafafa] text-[#737373]',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)

type BadgeVariants = VariantProps<typeof badgeVariants>

interface Props {
  variant?: BadgeVariants['variant']
  class?: string
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
})

const classes = computed(() => cn(badgeVariants({ variant: props.variant }), props.class))
</script>

<template>
  <span :class="classes">
    <slot />
  </span>
</template>
