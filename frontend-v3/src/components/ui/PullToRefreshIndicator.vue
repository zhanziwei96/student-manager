<script setup lang="ts">
import { ArrowDown, Loader2 } from 'lucide-vue-next'

/**
 * 下拉刷新指示器（usePullToRefresh 的配套 UI）
 *
 * 11 个列表页共用同一份标记；样式调整只改这里。
 * 阈值文案与 composable 默认 threshold=80 对齐。
 */
interface Props {
  pulling: boolean
  pullDistance: number
  refreshing: boolean
  /** 触发刷新的阈值（需与 usePullToRefresh 的 threshold 一致，默认 80） */
  threshold?: number
}

const props = withDefaults(defineProps<Props>(), { threshold: 80 })
</script>

<template>
  <div
    v-if="pulling || refreshing"
    class="flex items-center justify-center gap-1.5 overflow-hidden text-xs text-[#525252] transition-[height] duration-150"
    :style="{ height: props.pullDistance + 'px' }"
  >
    <Loader2 v-if="refreshing" class="h-4 w-4 animate-spin" />
    <ArrowDown v-else class="h-4 w-4" />
    <span>{{ refreshing ? '刷新中…' : pullDistance >= threshold ? '释放刷新' : '下拉刷新' }}</span>
  </div>
</template>
