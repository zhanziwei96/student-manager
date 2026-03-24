<script setup lang="ts">
import { computed } from 'vue'
import { cn } from '@/lib/utils'
import { ChevronDown } from 'lucide-vue-next'

/**
 * Select 组件
 * 基于 ClassHub 设计体系 v1.0.0
 */

interface Option {
  value: string
  label: string
  disabled?: boolean
}

interface Props {
  modelValue?: string
  class?: string
  id?: string
  placeholder?: string
  disabled?: boolean
  options: Option[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const classes = computed(() =>
  cn(
    // 布局
    'flex h-9 w-full items-center justify-between rounded-md',
    'px-3 py-2 pr-10', // 右侧留出图标空间
    // 边框和背景
    'border border-border bg-transparent',
    // 文字
    'text-sm text-text-primary',
    // 占位符
    'placeholder:text-text-placeholder',
    // 状态
    'transition-all duration-150 ease-out',
    'hover:border-border-hover',
    'focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary',
    'disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-white/[0.02]',
    // 自定义下拉箭头
    'appearance-none cursor-pointer',
    props.class
  )
)

const onChange = (event: Event) => {
  const target = event.target as HTMLSelectElement
  emit('update:modelValue', target.value)
}
</script>

<template>
  <div class="relative">
    <select
      :id="id"
      :class="classes"
      :value="modelValue"
      :disabled="disabled"
      @change="onChange"
    >
      <option v-if="placeholder" value="" disabled>{{ placeholder }}</option>
      <option 
        v-for="option in options" 
        :key="option.value" 
        :value="option.value"
        :disabled="option.disabled"
        class="bg-background-elevated text-text-primary"
      >
        {{ option.label }}
      </option>
    </select>
    <ChevronDown class="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
  </div>
</template>
