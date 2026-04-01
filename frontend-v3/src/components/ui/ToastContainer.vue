<script setup lang="ts">
import { toasts } from '@/composables/useToast'
import Toast from './Toast.vue'

/**
 * Toast 容器组件
 * 支持多条 Toast 消息同时显示（队列模式）
 */

const handleClose = (id: string) => {
  const index = toasts.value.findIndex(t => t.id === id)
  if (index > -1) {
    toasts.value.splice(index, 1)
  }
}
</script>

<template>
  <Teleport to="body">
    <div
      class="fixed top-1/2 left-1/2 z-[100] flex flex-col gap-2 pointer-events-none -translate-x-1/2 -translate-y-1/2"
    >
      <Toast
        v-for="toast in toasts"
        :key="toast.id"
        :message="toast.message"
        :variant="toast.variant"
        :duration="toast.duration"
        :show="true"
        @close="handleClose(toast.id)"
      />
    </div>
  </Teleport>
</template>
