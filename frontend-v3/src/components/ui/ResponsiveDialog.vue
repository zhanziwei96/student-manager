<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import Dialog from './Dialog.vue'
import BottomSheet from './BottomSheet.vue'

/**
 * ResponsiveDialog 响应式弹窗
 * 桌面端（≥768px）渲染居中 Dialog，移动端（<768px）渲染 BottomSheet
 *
 * API 与 Dialog 一致：v-model:open + title + description + 默认插槽 + footer 插槽，
 * 调用方只需把 <Dialog> 换成 <ResponsiveDialog>。
 * 移动端检测与 MobilePicker 一致（window.innerWidth < 768 + resize 监听）。
 */

interface Props {
  open: boolean
  title?: string
  description?: string
}

defineProps<Props>()

const emit = defineEmits<{
  'update:open': [value: boolean]
}>()

// class / data-* 等透传属性手动绑定到内部组件，禁用到根节点的自动透传
defineOptions({ inheritAttrs: false })

// 移动端检测（与 MobilePicker 相同模式；初始化时同步判断避免首帧闪错组件）
const isMobile = ref(typeof window !== 'undefined' && window.innerWidth < 768)
const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})

const onUpdateOpen = (value: boolean) => {
  emit('update:open', value)
}
</script>

<template>
  <!-- 桌面端：居中 Dialog（视觉与原有 Dialog 完全一致） -->
  <Dialog
    v-if="!isMobile"
    v-bind="$attrs"
    :open="open"
    :title="title"
    :description="description"
    @update:open="onUpdateOpen"
  >
    <template
      v-if="$slots.title"
      #title
    >
      <slot name="title" />
    </template>
    <template
      v-if="$slots.description"
      #description
    >
      <slot name="description" />
    </template>
    <slot />
    <template
      v-if="$slots.footer"
      #footer
    >
      <slot name="footer" />
    </template>
  </Dialog>

  <!-- 移动端：底部 BottomSheet -->
  <BottomSheet
    v-else
    v-bind="$attrs"
    :open="open"
    :title="$slots.title ? undefined : title"
    @update:open="onUpdateOpen"
  >
    <!-- 标题插槽（BottomSheet 仅支持 title 字符串，插槽标题在此渲染） -->
    <h3
      v-if="$slots.title"
      class="pb-2 text-center text-base font-medium text-black"
    >
      <slot name="title" />
    </h3>
    <p
      v-if="description || $slots.description"
      class="mb-3 text-sm text-[#737373] break-words"
    >
      <slot name="description">
        {{ description }}
      </slot>
    </p>
    <slot />
    <!-- 底部操作区：纵向堆叠、按钮撑满（iOS Action Sheet 惯例） -->
    <div
      v-if="$slots.footer"
      class="mt-4 flex flex-col gap-2 [&_button]:w-full"
    >
      <slot name="footer" />
    </div>
  </BottomSheet>
</template>
