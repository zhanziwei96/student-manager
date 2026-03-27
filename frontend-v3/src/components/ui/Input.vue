<script setup lang="ts">
import { computed } from 'vue'
import { cn } from '@/lib/utils'

/**
 * Input 组件
 * 基于 ClassHub 设计体系 v1.0.0
 */

interface Props {
  modelValue?: string | number
  class?: string | string[]
  id?: string
  placeholder?: string
  type?: string
  disabled?: boolean
  required?: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update:modelValue', value: string | number): void
}>()

const classes = computed(() =>
  cn(
    // 布局
    'flex h-9 w-full rounded-md px-3 py-2',
    // 边框
    'border border-border bg-transparent',
    // 文字
    'text-sm text-text-primary',
    // 占位符
    'placeholder:text-text-placeholder',
    // 文件输入
    'file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-text-primary',
    // 状态
    'transition-all duration-150 ease-out',
    'hover:border-border-hover',
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:border-primary',
    'disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-white/[0.02]',
    props.class
  )
)

const onInput = (event: Event) => {
  const target = event.target as HTMLInputElement
  const value = props.type === 'number' ? Number(target.value) : target.value
  emit('update:modelValue', value)
}
</script>

<template>
  <input
    :id="id"
    :class="classes"
    :value="modelValue"
    :placeholder="placeholder"
    :type="type || 'text'"
    :disabled="disabled"
    :required="required"
    @input="onInput"
  >
</template>
