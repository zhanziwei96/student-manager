<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { cn } from '@/lib/utils'
import { Search, ChevronDown, X } from 'lucide-vue-next'

interface Option {
  value: string
  label: string
}

interface Props {
  modelValue?: string
  class?: string
  placeholder?: string
  disabled?: boolean
  options: Option[]
  searchPlaceholder?: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const isOpen = ref(false)
const searchQuery = ref('')
const containerRef = ref<HTMLDivElement | null>(null)
const dropdownRef = ref<HTMLDivElement | null>(null)
const dropdownStyle = ref({ top: '0px', left: '0px', width: '0px' })

const selectedLabel = computed(() => {
  const option = props.options.find(opt => opt.value === props.modelValue)
  return option?.label || props.placeholder || '请选择'
})

const filteredOptions = computed(() => {
  if (!searchQuery.value) return props.options
  const query = searchQuery.value.toLowerCase()
  return props.options.filter(opt =>
    opt.label.toLowerCase().includes(query)
  )
})

const updatePosition = () => {
  if (!containerRef.value) return
  const rect = containerRef.value.getBoundingClientRect()
  dropdownStyle.value = {
    top: `${rect.bottom + 4}px`,
    left: `${rect.left}px`,
    width: `${rect.width}px`,
  }
}

const toggleOpen = () => {
  if (props.disabled) return
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    searchQuery.value = ''
    nextTick(updatePosition)
  }
}

const selectOption = (value: string) => {
  emit('update:modelValue', value)
  isOpen.value = false
  searchQuery.value = ''
}

const clearSelection = () => {
  emit('update:modelValue', '')
}

// 点击外部关闭
const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as Node
  const insideTrigger = containerRef.value?.contains(target)
  const insideDropdown = dropdownRef.value?.contains(target)
  if (!insideTrigger && !insideDropdown) {
    isOpen.value = false
  }
}

// ESC 关闭
const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Escape') isOpen.value = false
}

// 窗口 resize 时更新位置
const handleResize = () => {
  if (isOpen.value) updatePosition()
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  document.addEventListener('keydown', handleKeydown)
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('keydown', handleKeydown)
  window.removeEventListener('resize', handleResize)
})
</script>

<template>
  <div
    ref="containerRef"
    class="relative"
  >
    <!-- Trigger -->
    <button
      type="button"
      :class="cn(
        'flex h-10 w-full items-center justify-between rounded-full',
        'border border-[#e5e5e5] bg-white',
        'px-3 py-2',
        'text-sm text-black',
        'focus:outline-none focus:ring-2 focus:ring-[#3b82f6]/50 focus:border-black',
        'disabled:cursor-not-allowed disabled:opacity-50',
        isOpen && 'ring-2 ring-[#3b82f6]/50 border-black',
        props.class
      )"
      :disabled="disabled"
      @click="toggleOpen"
    >
      <span :class="!modelValue && 'text-[#a3a3a3]'">
        {{ selectedLabel }}
      </span>
      <div class="flex items-center gap-1">
        <button
          v-if="modelValue"
          type="button"
          class="rounded p-0.5 hover:bg-[#fafafa]"
          @click.stop="clearSelection"
        >
          <X class="h-3.5 w-3.5 text-[#a3a3a3]" />
        </button>
        <ChevronDown
          :class="cn(
            'h-4 w-4 text-[#a3a3a3]',
            isOpen && 'rotate-180'
          )"
        />
      </div>
    </button>
  </div>

  <!-- Dropdown rendered via Teleport to avoid z-index / overflow clipping -->
  <Teleport to="body">
    <div
      v-if="isOpen"
      ref="dropdownRef"
      :style="dropdownStyle"
      :class="cn(
        'fixed z-[9999] mt-1 min-w-[200px]',
        'rounded-xl border border-[#e5e5e5] bg-white',
        'overflow-hidden'
      )"
    >
      <!-- Search Input -->
      <div class="border-b border-[#e5e5e5] p-2">
        <div class="relative">
          <Search class="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-[#a3a3a3]" />
          <input
            v-model="searchQuery"
            type="text"
            :placeholder="searchPlaceholder || '搜索...'"
            class="w-full rounded-full bg-[#fafafa] border border-[#e5e5e5] py-1.5 pl-9 pr-3 text-sm text-black placeholder:text-[#a3a3a3] focus:outline-none focus:ring-1 focus:ring-[#3b82f6]/50"
            @click.stop
          >
        </div>
      </div>

      <!-- Options List -->
      <div class="max-h-60 overflow-y-auto py-1">
        <div
          v-for="option in filteredOptions"
          :key="option.value"
          :class="cn(
            'cursor-pointer px-3 py-2 text-sm',
            modelValue === option.value
              ? 'bg-[#e5e5e5] text-black'
              : 'text-[#737373] hover:bg-[#fafafa]'
          )"
          @click="selectOption(option.value)"
        >
          {{ option.label }}
        </div>
        <div
          v-if="filteredOptions.length === 0"
          class="px-3 py-4 text-center text-sm text-[#a3a3a3]"
        >
          未找到匹配选项
        </div>
      </div>
    </div>
  </Teleport>
</template>
