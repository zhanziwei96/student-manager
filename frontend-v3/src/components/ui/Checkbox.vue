<script setup lang="ts">
import { computed } from 'vue'
import { cn } from '@/lib/utils'
import { Check } from 'lucide-vue-next'

/**
 * Checkbox 组件
 * 基于 ClassHub 设计体系 v1.0.0
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
    'h-5 w-5 rounded border transition-all duration-150',
    props.checked
      ? 'bg-primary border-primary'
      : 'bg-transparent border-border hover:border-border-hover',
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
