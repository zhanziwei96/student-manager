<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ChevronDown, X, Search, Check } from 'lucide-vue-next'
import { cn } from '@/lib/utils'

export interface MobilePickerOption {
  value: string | number
  label: string
  subtitle?: string
  disabled?: boolean
}

interface Props {
  modelValue?: string | number
  options: MobilePickerOption[]
  title?: string
  placeholder?: string
  disabled?: boolean
  searchable?: boolean
  searchPlaceholder?: string
  clearable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '请选择',
  searchPlaceholder: '搜索...'
})

const emit = defineEmits<{
  'update:modelValue': [value: string | number | undefined]
  change: [value: string | number | undefined, option: MobilePickerOption | undefined]
}>()

// 状态
const isOpen = ref(false)
const searchQuery = ref('')
const isMobile = ref(false)
const desktopPanelRef = ref<HTMLDivElement | null>(null)

// 移动端检测
const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
}

const handleClickOutside = (event: MouseEvent) => {
  if (!isMobile.value && isOpen.value) {
    const target = event.target as HTMLElement
    if (!target.closest('.mobile-picker-container')) {
      close()
    }
  }
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
  document.removeEventListener('click', handleClickOutside)
})

// 计算属性
const selectedOption = computed(() => {
  if (props.modelValue === undefined) return undefined
  return props.options.find(opt => opt.value === props.modelValue)
})

// 过滤选项
const filteredOptions = computed(() => {
  if (!searchQuery.value) return props.options
  const query = searchQuery.value.toLowerCase()
  return props.options.filter(opt =>
    opt.label.toLowerCase().includes(query) ||
    opt.subtitle?.toLowerCase().includes(query)
  )
})

// 方法
const open = () => {
  if (props.disabled) return
  isOpen.value = true
  searchQuery.value = ''
}

const close = () => {
  isOpen.value = false
  searchQuery.value = ''
}

const select = (option: MobilePickerOption) => {
  if (option.disabled) return
  emit('update:modelValue', option.value)
  emit('change', option.value, option)
  close()
}

const clear = () => {
  emit('update:modelValue', undefined)
  emit('change', undefined, undefined)
}

const isSelected = (option: MobilePickerOption) => {
  return props.modelValue === option.value
}
</script>

<template>
  <div class="relative mobile-picker-container">
    <!-- 触发器 -->
    <button
      type="button"
      :class="cn(
        'flex h-11 w-full items-center justify-between rounded-full',
        'border border-[#e5e5e5] bg-white',
        'px-3 py-2',
        'text-base text-black',
        'focus:outline-none focus:ring-2 focus:ring-[#3b82f6]/50 focus:border-black',
        'disabled:cursor-not-allowed disabled:opacity-50',
        isOpen && 'ring-2 ring-[#3b82f6]/50 border-black'
      )"
      :disabled="disabled"
      @click="open"
    >
      <span :class="!selectedOption && 'text-[#a3a3a3]'">
        <template v-if="selectedOption">
          {{ selectedOption.label }}
          <span v-if="selectedOption.subtitle" class="text-[#737373] ml-1">
            ({{ selectedOption.subtitle }})
          </span>
        </template>
        <template v-else>
          {{ placeholder }}
        </template>
      </span>
      <div class="flex items-center gap-1">
        <button
          v-if="clearable && modelValue !== undefined"
          type="button"
          class="rounded p-0.5 hover:bg-[#fafafa]"
          @click.stop="clear"
        >
          <X class="h-4 w-4 text-[#a3a3a3]" />
        </button>
        <ChevronDown
          :class="cn(
            'h-4 w-4 text-[#a3a3a3]',
            isOpen && 'rotate-180'
          )"
        />
      </div>
    </button>

    <!-- 移动端底部弹窗 -->
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="isOpen && isMobile"
          class="fixed inset-0 z-50 bg-black/30"
          @click="close"
        />
      </Transition>

      <Transition name="slide-up">
        <div
          v-if="isOpen && isMobile"
          class="fixed bottom-0 left-0 right-0 z-50 bg-white rounded-t-xl max-h-[70vh] flex flex-col"
        >
          <!-- 指示条 -->
          <div class="flex justify-center pt-3 pb-2" @click="close">
            <div class="w-10 h-1 rounded-full bg-[#d4d4d4]" />
          </div>

          <!-- 标题栏 -->
          <div class="flex items-center justify-between px-4 py-3 border-b border-[#e5e5e5]">
            <h3 class="text-lg font-medium text-black">
              {{ title || placeholder }}
            </h3>
            <button
              type="button"
              class="text-black text-base font-medium"
              @click="close"
            >
              完成
            </button>
          </div>

          <!-- 搜索框 -->
          <div v-if="searchable" class="p-3 border-b border-[#e5e5e5]">
            <div class="relative">
              <Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#a3a3a3]" />
              <input
                v-model="searchQuery"
                type="text"
                :placeholder="searchPlaceholder"
                class="w-full h-10 pl-10 pr-4 rounded-full bg-[#fafafa] border border-[#e5e5e5] text-black text-sm placeholder:text-[#a3a3a3] focus:outline-none focus:border-black"
              >
            </div>
          </div>

          <!-- 选项列表 -->
          <div class="flex-1 overflow-y-auto">
            <div
              v-for="option in filteredOptions"
              :key="option.value"
              :class="cn(
                'flex items-center justify-between px-4 py-4 border-b border-[#e5e5e5] cursor-pointer active:bg-[#fafafa]',
                isSelected(option) && 'bg-[#e5e5e5]'
              )"
              @click="select(option)"
            >
              <div>
                <div :class="cn('text-base', isSelected(option) ? 'text-black font-medium' : 'text-[#737373]')">
                  {{ option.label }}
                </div>
                <div v-if="option.subtitle" class="text-sm text-[#a3a3a3] mt-0.5">
                  {{ option.subtitle }}
                </div>
              </div>
              <Check
                v-if="isSelected(option)"
                class="h-5 w-5 text-black"
              />
            </div>
            <div v-if="filteredOptions.length === 0" class="py-8 text-center text-[#a3a3a3]">
              未找到匹配选项
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- 桌面端下拉面板 -->
    <div
      v-if="isOpen && !isMobile"
      ref="desktopPanelRef"
      class="absolute z-50 top-full left-0 right-0 mt-1 bg-white border border-[#e5e5e5] rounded-xl overflow-hidden"
    >
      <!-- 搜索框 -->
      <div v-if="searchable" class="p-2 border-b border-[#e5e5e5]">
        <div class="relative">
          <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-[#a3a3a3]" />
          <input
            v-model="searchQuery"
            type="text"
            :placeholder="searchPlaceholder"
            class="w-full h-9 pl-9 pr-3 rounded-full bg-[#fafafa] border border-[#e5e5e5] text-black text-sm placeholder:text-[#a3a3a3] focus:outline-none focus:border-black"
            @keydown.esc="close"
          >
        </div>
      </div>

      <!-- 选项列表 -->
      <div class="max-h-[300px] overflow-y-auto">
        <div
          v-for="(option, index) in filteredOptions"
          :key="option.value"
          :class="cn(
            'flex items-center justify-between px-3 py-2.5 cursor-pointer hover:bg-[#fafafa]',
            index !== filteredOptions.length - 1 && 'border-b border-[#e5e5e5]',
            isSelected(option) && 'bg-[#e5e5e5]'
          )"
          @click="select(option)"
        >
          <div>
            <div :class="cn('text-sm', isSelected(option) ? 'text-black font-medium' : 'text-[#737373]')">
              {{ option.label }}
            </div>
            <div v-if="option.subtitle" class="text-xs text-[#a3a3a3] mt-0.5">
              {{ option.subtitle }}
            </div>
          </div>
          <Check
            v-if="isSelected(option)"
            class="h-4 w-4 text-black"
          />
        </div>
        <div v-if="filteredOptions.length === 0" class="py-6 text-center text-sm text-[#a3a3a3]">
          未找到匹配选项
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 150ms ease-out;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 200ms ease-out, opacity 200ms ease-out;
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(100%);
  opacity: 0;
}
</style>
