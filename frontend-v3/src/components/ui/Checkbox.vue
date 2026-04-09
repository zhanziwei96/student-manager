<script setup lang="ts">
import { computed } from 'vue'
import { cn } from '@/lib/utils'
import { Check } from 'lucide-vue-next'

/**
 * Checkbox 组件
 * Ollama 白色主题设计
 */

interface Props {
  checked?: boolean
  disabled?: boolean
  id?: string
  class?: string | string[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update:checked', value: boolean): void
}>()

const handleChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  emit('update:checked', target.checked)
}

const wrapperClasses = computed(() =>
  cn(
    'relative flex items-center justify-center',
    'h-5 w-5 rounded border',
    props.checked
      ? 'bg-black border-black'
      : 'bg-white border-[#e5e5e5] hover:border-[#d4d4d4]',
    props.disabled && 'opacity-50 cursor-not-allowed',
    props.class
  )
)
</script>

<template>
  <label
    class="relative flex cursor-pointer items-center gap-2"
    :class="{ 'cursor-not-allowed': disabled }"
  >
    <input
      :id="id"
      type="checkbox"
      class="peer sr-only"
      :checked="checked"
      :disabled="disabled"
      @change="handleChange"
    >
    <div :class="wrapperClasses">
      <Check
        v-if="checked"
        class="h-3.5 w-3.5 text-white"
        stroke-width="3"
      />
    </div>
  </label>
</template>
