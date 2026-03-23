<script setup lang="ts">
import { computed } from 'vue'
import { cn } from '@/lib/utils'

/**
 * Label 组件
 * 基于 ClassHub 设计体系 v1.0.0
 */

interface Props {
  class?: string
  for?: string
}

const props = defineProps<Props>()

const classes = computed(() =>
  cn(
    // 基础样式
    'text-sm font-medium text-text-secondary',
    // 间距
    'mb-2 block',
    // 禁用状态
    'peer-disabled:cursor-not-allowed peer-disabled:opacity-50',
    props.class
  )
)
</script>

<template>
  <label :class="classes" :for="$props.for">
    <slot />
  </label>
</template>
