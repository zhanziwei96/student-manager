<script setup lang="ts">
import { computed } from 'vue'
import { cn } from '@/lib/utils'
import { ChevronDown } from 'lucide-vue-next'

/**
 * Select 组件
 * Ollama 白色主题设计
 */

interface Option {
  value: string | number
  label: string
  disabled?: boolean
}

interface Props {
  modelValue?: string | number
  class?: string
  id?: string
  placeholder?: string
  disabled?: boolean
  options?: Option[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update:modelValue', value: string | number): void
}>()

const classes = computed(() =>
  cn(
    // 布局
    'flex h-9 w-full items-center justify-between rounded-full',
    'px-3 py-2 pr-10', // 右侧留出图标空间
    // 边框和背景
    'border border-[#e5e5e5] bg-white',
    // 文字
    'text-sm text-black',
    // 占位符
    'placeholder:text-[#a3a3a3]',
    // 状态
    'focus:outline-none focus:ring-2 focus:ring-[#3b82f6]/50 focus:border-black',
    'disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-[#fafafa]',
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
      <option
        v-if="placeholder"
        value=""
        disabled
      >
        {{ placeholder }}
      </option>
      <option
        v-for="option in options || []"
        :key="option.value"
        :value="option.value"
        :disabled="option.disabled"
        class="bg-white text-black"
      >
        {{ option.label }}
      </option>
      <slot />
    </select>
    <ChevronDown class="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#a3a3a3]" />
  </div>
</template>
