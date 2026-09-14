<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { useScrollLock } from '@vueuse/core'
import { useRoute } from 'vue-router'
import { cn } from '@/lib/utils'

/**
 * BottomSheet 底部半模态组件（iOS 风格）
 * Ollama 白色主题 + 毛玻璃材质（微信 WebView 降级实色）
 *
 * - Teleport 到 body，避免 z-index 层级问题
 * - 遮罩点击关闭 / 路由切换关闭
 * - 顶部拖拽手柄下滑关闭（原生 TouchEvent，无手势库依赖）
 * - 打开时锁定背景滚动
 *
 * 供 BottomNav「更多」与移动端弹窗 Sheet 化复用
 */

interface Props {
  open: boolean
  title?: string
  class?: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:open': [value: boolean]
}>()

// 检查是否在客户端环境（SSR 安全）
const isClient = typeof window !== 'undefined'

// 锁定 body 滚动（与 Dialog.vue 一致，useScrollLock 支持计数器）
const isLocked = useScrollLock(isClient ? document.body : null)

const close = () => {
  emit('update:open', false)
}

// ========== 拖拽下滑关闭 ==========
const sheetRef = ref<HTMLElement | null>(null)
// 当前拖拽位移（px，>= 0）
const dragY = ref(0)
// 是否正在拖拽（拖拽中禁用 transform 过渡）
const isDragging = ref(false)
// 是否正在回弹（回弹期间保留 transform 过渡）
const springing = ref(false)

let startY = 0
let startTime = 0

const resetDrag = () => {
  dragY.value = 0
  isDragging.value = false
  springing.value = false
}

watch(
  () => props.open,
  (isOpen) => {
    isLocked.value = isOpen
    if (!isOpen) resetDrag()
  },
  { immediate: true }
)

// 组件卸载时恢复滚动，避免泄漏
onUnmounted(() => {
  isLocked.value = false
})

// 路由切换时关闭（同 MobileDrawer）
const route = useRoute()
watch(() => route.path, close)

const onTouchStart = (e: TouchEvent) => {
  isDragging.value = true
  springing.value = false
  startY = e.touches[0].clientY
  startTime = Date.now()
}

const onTouchMove = (e: TouchEvent) => {
  if (!isDragging.value) return
  // 只响应向下拖拽
  dragY.value = Math.max(0, e.touches[0].clientY - startY)
}

const onTouchEnd = () => {
  if (!isDragging.value) return
  isDragging.value = false

  const delta = dragY.value
  const velocity = delta / Math.max(Date.now() - startTime, 1)
  // jsdom 等无布局环境 offsetHeight 为 0，回退阈值 80px
  const height = sheetRef.value?.offsetHeight ?? 0
  const threshold = Math.max(height / 3, 80)

  // 拖过 1/3 高度，或快速下滑（最小位移 50px 防止误触）
  if (delta > threshold || (delta > 50 && velocity > 0.4)) {
    resetDrag()
    close()
    return
  }

  // 未过阈值：回弹（先挂过渡，下一帧再归零，保证动画生效）
  springing.value = true
  requestAnimationFrame(() => {
    dragY.value = 0
    window.setTimeout(() => {
      springing.value = false
    }, 300)
  })
}

// 拖拽位移用内联 transform 跟随手指；无拖拽时不设内联样式，
// 避免覆盖进出场 Transition 的 translate-y 类
const sheetStyle = computed(() => {
  if (dragY.value === 0 && !springing.value) return undefined
  return {
    transform: `translateY(${dragY.value}px)`,
    transition: isDragging.value ? 'none' : 'transform 0.25s ease-out'
  }
})

const sheetClasses = computed(() =>
  cn(
    'fixed inset-x-0 bottom-0 z-50 flex max-h-[85vh] flex-col',
    // --radius-sheet
    'rounded-t-[1.25rem] bottom-sheet-glass',
    props.class
  )
)
</script>

<template>
  <Teleport
    v-if="isClient"
    to="body"
  >
    <!-- 遮罩层：点击关闭 -->
    <Transition
      enter-active-class="transition-opacity duration-300"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition-opacity duration-200"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="open"
        class="fixed inset-0 z-50 bg-black/30"
        @click="close"
      />
    </Transition>

    <!-- Sheet 面板：底部弹出 -->
    <Transition
      enter-active-class="transition-transform duration-300 ease-out"
      enter-from-class="translate-y-full"
      enter-to-class="translate-y-0"
      leave-active-class="transition-transform duration-200 ease-in"
      leave-from-class="translate-y-0"
      leave-to-class="translate-y-full"
    >
      <section
        v-if="open"
        ref="sheetRef"
        role="dialog"
        aria-modal="true"
        :class="sheetClasses"
        :style="sheetStyle"
      >
        <!-- 拖拽手柄区域 -->
        <div
          class="touch-none select-none pt-2.5 pb-2 cursor-grab active:cursor-grabbing"
          @touchstart="onTouchStart"
          @touchmove="onTouchMove"
          @touchend="onTouchEnd"
          @touchcancel="onTouchEnd"
        >
          <div class="mx-auto h-1.5 w-10 rounded-full bg-[#d4d4d4]" />
        </div>

        <!-- 标题 -->
        <h3
          v-if="title"
          class="px-4 pb-2 text-center text-base font-medium text-black"
        >
          {{ title }}
        </h3>

        <!-- 内容（内部滚动） -->
        <div class="flex-1 min-h-0 overflow-y-auto px-4">
          <slot />
        </div>
      </section>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* 微信 WebView 兼容：不支持 backdrop-filter 时保持纯白底 */
.bottom-sheet-glass {
  background: #ffffff;
  /* 刘海屏底部安全区（--safe-bottom） */
  padding-bottom: calc(env(safe-area-inset-bottom, 0px) + 1rem);
}

@supports (backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px)) {
  .bottom-sheet-glass {
    /* tokens.css 的 @theme inline 不导出运行时变量，此处写字面值：
       --color-surface-glass / --material-blur */
    background: rgba(255, 255, 255, 0.85);
    backdrop-filter: saturate(180%) blur(20px);
    -webkit-backdrop-filter: saturate(180%) blur(20px);
  }
}
</style>
