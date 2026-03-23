<script setup lang="ts">
import { computed } from 'vue'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

/**
 * Button 组件
 * 基于 ClassHub 设计体系 v1.0.0
 */

const buttonVariants = cva(
  // 基础样式
  'inline-flex items-center justify-center gap-2 whitespace-nowrap ' +
  'font-medium transition-all duration-150 ease-out ' +
  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:ring-offset-2 focus-visible:ring-offset-background ' +
  'disabled:pointer-events-none disabled:opacity-50 disabled:cursor-not-allowed ' +
  'active:scale-[0.98]',
  {
    variants: {
      variant: {
        // 主按钮 - 使用主色
        default: 'bg-primary text-white hover:bg-primary-hover shadow-md hover:shadow-glow-primary',
        
        // 次级按钮 - 描边样式
        outline: 'border border-border bg-transparent text-text-secondary hover:bg-white/10 hover:text-text-primary hover:border-border-hover',
        
        // 幽灵按钮 - 透明背景
        ghost: 'bg-transparent text-text-secondary hover:bg-white/10 hover:text-text-primary',
        
        // 危险按钮 - 错误色
        destructive: 'bg-error text-white hover:bg-error/90 shadow-md',
        
        // 次级按钮 - 半透明背景
        secondary: 'bg-white/10 text-white hover:bg-white/20',
        
        // 链接按钮
        link: 'text-primary underline-offset-4 hover:underline bg-transparent',
      },
      size: {
        // 小尺寸: h-8 (32px)
        sm: 'h-8 px-3 text-xs rounded-md',
        
        // 默认尺寸: h-9 (36px)
        default: 'h-9 px-4 py-2 text-sm rounded-md',
        
        // 大尺寸: h-10 (40px)
        lg: 'h-10 px-6 text-base rounded-lg',
        
        // 图标按钮: 正方形
        icon: 'h-9 w-9 p-0 rounded-md',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
)

type ButtonVariants = VariantProps<typeof buttonVariants>

interface Props {
  variant?: ButtonVariants['variant']
  size?: ButtonVariants['size']
  class?: string
  disabled?: boolean
  type?: 'button' | 'submit' | 'reset'
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
  size: 'default',
  type: 'button',
  loading: false,
})

const classes = computed(() => cn(buttonVariants({ variant: props.variant, size: props.size }), props.class))
</script>

<template>
  <button 
    :class="classes" 
    :disabled="disabled || loading" 
    :type="type"
  >
    <slot />
  </button>
</template>
