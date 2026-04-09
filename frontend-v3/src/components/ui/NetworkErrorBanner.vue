<script setup lang="ts">
import { AlertTriangle, RefreshCw, X } from 'lucide-vue-next'
import Button from './Button.vue'

interface Props {
  message?: string
}

withDefaults(defineProps<Props>(), {
  message: '网络连接失败，数据同步异常',
})

const emit = defineEmits<{
  retry: []
  dismiss: []
}>()
</script>

<template>
  <div
    class="fixed top-0 left-0 right-0 z-50 bg-[#ef4444] text-white px-4 py-3"
    role="alert"
  >
    <div class="flex items-center justify-between max-w-7xl mx-auto">
      <div class="flex items-center gap-2">
        <AlertTriangle class="h-5 w-5 flex-shrink-0" />
        <span class="text-sm font-medium">{{ message }}</span>
      </div>

      <div class="flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          class="text-white hover:bg-white/20"
          @click="emit('retry')"
        >
          <RefreshCw class="h-4 w-4 mr-1" />
          重试
        </Button>
        <Button
          variant="ghost"
          size="sm"
          class="text-white hover:bg-white/20 p-1"
          @click="emit('dismiss')"
        >
          <X class="h-4 w-4" />
        </Button>
      </div>
    </div>
  </div>
</template>
