<script setup lang="ts">
import { ref, computed } from 'vue'
import { ChevronDown, X } from 'lucide-vue-next'
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

// 计算属性
const selectedOption = computed(() => {
  if (props.modelValue === undefined) return undefined
  return props.options.find(opt => opt.value === props.modelValue)
})

// TODO: 将在底部弹窗实现中使用
// const filteredOptions = computed(() => {
//   if (!searchQuery.value) return props.options
//   const query = searchQuery.value.toLowerCase()
//   return props.options.filter(opt =>
//     opt.label.toLowerCase().includes(query) ||
//     opt.subtitle?.toLowerCase().includes(query)
//   )
// })

// 方法
const open = () => {
  if (props.disabled) return
  isOpen.value = true
  searchQuery.value = ''
}

// TODO: 将在底部弹窗实现中使用
// const close = () => {
//   isOpen.value = false
//   searchQuery.value = ''
// }

// TODO: 将在底部弹窗实现中使用
// const select = (option: MobilePickerOption) => {
//   if (option.disabled) return
//   emit('update:modelValue', option.value)
//   emit('change', option.value, option)
//   close()
// }

const clear = () => {
  emit('update:modelValue', undefined)
  emit('change', undefined, undefined)
}

// TODO: 将在底部弹窗实现中使用
// const isSelected = (option: MobilePickerOption) => {
//   return props.modelValue === option.value
// }
</script>

<template>
  <div class="relative">
    <!-- 触发器 -->
    <button
      type="button"
      :class="cn(
        'flex h-11 w-full items-center justify-between rounded-lg',
        'border border-white/10 bg-white/5',
        'px-3 py-2',
        'text-base text-white',
        'transition-all duration-150',
        'hover:border-white/20 hover:bg-white/[0.07]',
        'focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50',
        'disabled:cursor-not-allowed disabled:opacity-50',
        isOpen && 'border-primary/50 ring-2 ring-primary/50'
      )"
      :disabled="disabled"
      @click="open"
    >
      <span :class="!selectedOption && 'text-white/50'">
        <template v-if="selectedOption">
          {{ selectedOption.label }}
          <span v-if="selectedOption.subtitle" class="text-white/60 ml-1">
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
          class="rounded p-0.5 hover:bg-white/10"
          @click.stop="clear"
        >
          <X class="h-4 w-4 text-white/50" />
        </button>
        <ChevronDown
          :class="cn(
            'h-4 w-4 text-white/50 transition-transform duration-200',
            isOpen && 'rotate-180'
          )"
        />
      </div>
    </button>

    <!-- TODO: 底部弹窗 -->
  </div>
</template>
