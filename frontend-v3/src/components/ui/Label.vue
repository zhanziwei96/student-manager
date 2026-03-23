<script setup lang="ts">
import { computed } from 'vue'
import { cn } from '@/lib/utils'

interface Props {
  class?: string
  forId?: string
}

const props = defineProps<Props>()

const classes = computed(() =>
  cn(
    'text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 text-white/80',
    props.class
  )
)
</script>

<template>
  <label :class="classes" :for="forId">
    <slot />
  </label>
</template>
