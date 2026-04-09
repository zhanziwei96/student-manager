<script setup lang="ts">
import { computed } from 'vue'
import { cn } from '@/lib/utils'

/**
 * Input 组件
 * Ollama 白色主题设计
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
    'flex h-9 w-full rounded-full px-3 py-2',
    // 边框和背景
    'border border-[#e5e5e5] bg-white',
    // 文字
    'text-sm text-black',
    // 占位符
    'placeholder:text-[#a3a3a3]',
    // 文件输入
    'file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-black',
    // 状态
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#3b82f6]/50 focus-visible:border-black',
    'disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-[#fafafa]',
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
