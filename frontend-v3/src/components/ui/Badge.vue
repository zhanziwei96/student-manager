<script setup lang="ts">
import { computed } from 'vue'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

/**
 * Badge 组件
 * 基于 ClassHub 设计体系 v1.0.0
 */

const badgeVariants = cva(
  'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors whitespace-nowrap',
  {
    variants: {
      variant: {
        // 默认标签
        default: 'bg-white/10 text-text-secondary',
        
        // 主色标签
        primary: 'bg-primary/20 text-primary',
        
        // 成功状态
        success: 'bg-success/20 text-success',
        
        // 警告状态
        warning: 'bg-warning/20 text-warning',
        
        // 错误状态
        error: 'bg-error/20 text-error',
        
        // 信息状态
        info: 'bg-info/20 text-info',
        
        // 描边样式
        outline: 'border border-border text-text-secondary bg-transparent',
        
        // 次级标签
        secondary: 'bg-white/5 text-text-muted',
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
