<script setup lang="ts">
import { Loader2, AlertCircle } from 'lucide-vue-next'
import Card from './Card.vue'

/**
 * DataContainer 组件
 * 通用的数据加载容器，统一处理 loading、error 和空数据状态
 */

interface Props {
  // 加载状态
  loading?: boolean
  // 错误对象
  error?: Error | null
  // 是否有数据
  hasData?: boolean
  // 空数据提示文本
  emptyText?: string
  // 加载占位高度
  loadingHeight?: string
}

withDefaults(defineProps<Props>(), {
  loading: false,
  error: null,
  hasData: true,
  emptyText: '暂无数据',
  loadingHeight: '16rem',
})

const emit = defineEmits<{
  (e: 'retry'): void
}>()
</script>

<template>
  <!-- 加载状态 -->
  <div
    v-if="loading"
    class="flex items-center justify-center"
    :style="{ height: loadingHeight }"
  >
    <Loader2 class="h-8 w-8 animate-spin text-primary" />
  </div>

  <!-- 错误状态 -->
  <Card
    v-else-if="error"
    class="border-red-500/20 bg-red-500/10 p-4"
  >
    <div class="flex items-center gap-3 text-red-400">
      <AlertCircle class="h-5 w-5" />
      <div class="flex-1">
        <p class="font-medium">加载失败</p>
        <p class="text-sm opacity-80">{{ error.message }}</p>
      </div>
      <button
        class="rounded-md px-3 py-1 text-sm hover:bg-red-500/20"
        @click="emit('retry')"
      >
        重试
      </button>
    </div>
  </Card>

  <!-- 空数据状态 -->
  <Card
    v-else-if="!hasData"
    class="border-white/10 bg-white/[0.02] p-8 text-center"
  >
    <p class="text-white/60">{{ emptyText }}</p>
  </Card>

  <!-- 正常内容 -->
  <slot v-else />
</template>
