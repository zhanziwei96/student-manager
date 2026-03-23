<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { cn } from '@/lib/utils'
import { X, CheckCircle, AlertCircle, Info } from 'lucide-vue-next'

type ToastVariant = 'default' | 'success' | 'error' | 'warning'

interface Props {
  show?: boolean
  message: string
  variant?: ToastVariant
  duration?: number
}

const props = withDefaults(defineProps<Props>(), {
  show: false,
  variant: 'default',
  duration: 3000,
})

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
}>()

const isVisible = ref(false)

const variantClasses: Record<ToastVariant, string> = {
  default: 'bg-[#13131f] border-white/10 text-white',
  success: 'bg-green-500/10 border-green-500/50 text-green-400',
  error: 'bg-red-500/10 border-red-500/50 text-red-400',
  warning: 'bg-yellow-500/10 border-yellow-500/50 text-yellow-400',
}

const classes = computed(() =>
  cn(
    'pointer-events-auto flex w-full max-w-sm items-center gap-3 rounded-lg border p-4 shadow-lg',
    variantClasses[props.variant],
    !isVisible.value && 'opacity-0 translate-y-2'
  )
)

const icon = computed(() => {
  switch (props.variant) {
    case 'success':
      return CheckCircle
    case 'error':
      return AlertCircle
    default:
      return Info
  }
})

onMounted(() => {
  if (props.show) {
    showToast()
  }
})

const showToast = () => {
  isVisible.value = true
  setTimeout(() => {
    isVisible.value = false
    setTimeout(() => emit('update:show', false), 200)
  }, props.duration)
}

const close = () => {
  isVisible.value = false
  setTimeout(() => emit('update:show', false), 200)
}

// Expose show method
defineExpose({ show: showToast })
</script>

<template>
  <Teleport to="body">
    <div v-if="show" class="fixed bottom-4 right-4 z-[100] flex flex-col gap-2">
      <div :class="classes" class="transition-all duration-200">
        <component :is="icon" class="h-5 w-5 shrink-0" />
        <span class="flex-1 text-sm font-medium">{{ message }}</span>
        <button @click="close" class="shrink-0 opacity-70 hover:opacity-100">
          <X class="h-4 w-4" />
        </button>
      </div>
    </div>
  </Teleport>
</template>
