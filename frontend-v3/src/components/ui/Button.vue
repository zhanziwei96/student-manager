<script setup lang="ts">
import { computed } from 'vue'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

/**
 * Button 组件
 * Ollama 白色主题设计
 */

const buttonVariants = cva(
  // 基础样式
  'inline-flex items-center justify-center gap-2 whitespace-nowrap ' +
  'font-medium ' +
  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#3b82f6]/50 ' +
  'disabled:pointer-events-none disabled:opacity-50 disabled:cursor-not-allowed',
  {
    variants: {
      variant: {
        // 默认按钮 - 灰色药丸
        default: 'bg-[#e5e5e5] text-[#262626] border border-[#e5e5e5] hover:bg-[#d4d4d4]',

        // 描边按钮 - 白色药丸
        outline: 'bg-white text-[#404040] border border-[#d4d4d4] hover:bg-[#fafafa]',

        // CTA 按钮 - 黑色药丸
        cta: 'bg-black text-white border border-black hover:bg-[#262626]',

        // 幽灵按钮 - 透明背景
        ghost: 'bg-transparent text-[#737373] hover:text-black hover:bg-[#fafafa]',

        // 危险按钮 - 错误色
        destructive: 'bg-[#ef4444] text-white border border-[#ef4444] hover:bg-[#dc2626]',

        // 链接按钮
        link: 'text-black underline-offset-4 hover:underline bg-transparent',
      },
      size: {
        // 小尺寸: h-8 (32px)
        sm: 'h-8 px-3 text-xs rounded-full',

        // 默认尺寸: h-9 (36px)
        default: 'h-9 px-4 py-2 text-sm rounded-full',

        // 大尺寸: h-10 (40px)
        lg: 'h-10 px-6 text-base rounded-full',

        // 图标按钮: 正方形
        icon: 'h-9 w-9 p-0 rounded-full',
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
