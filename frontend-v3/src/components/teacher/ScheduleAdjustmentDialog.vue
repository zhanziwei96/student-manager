<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { Dialog, Button, Input } from '@/components/ui'
import { useCreateScheduleAdjustment } from '@/composables'
import type { CreateScheduleAdjustmentRequest } from '@/types'

interface ScheduleInfo {
  id: number
  course_name: string
  class_name: string
  classroom?: string
  start_time?: string
  end_time?: string
}

interface Props {
  open: boolean
  schedule: ScheduleInfo | null
  weekNumber: number
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
  (e: 'success'): void
}>()

type AdjustmentType = 'cancel' | 'modify' | 'makeup'

const adjustmentType = ref<AdjustmentType>('cancel')
const reason = ref('')
const newDate = ref('')
const newStartTime = ref('')
const newEndTime = ref('')
const newClassroom = ref('')

const { mutateAsync: createAdjustment, isPending } = useCreateScheduleAdjustment()

// 当弹窗打开时重置表单
watch(() => props.open, (isOpen) => {
  if (isOpen) {
    adjustmentType.value = 'cancel'
    reason.value = ''
    newDate.value = ''
    newStartTime.value = ''
    newEndTime.value = ''
    newClassroom.value = ''
  }
})

const typeOptions: { value: AdjustmentType; label: string; color: string }[] = [
  { value: 'cancel', label: '停课', color: 'text-red-400 bg-red-500/10 border-red-500/30' },
  { value: 'modify', label: '调课', color: 'text-blue-400 bg-blue-500/10 border-blue-500/30' },
  { value: 'makeup', label: '补课', color: 'text-purple-400 bg-purple-500/10 border-purple-500/30' },
]

const showExtraFields = computed(() => adjustmentType.value === 'modify' || adjustmentType.value === 'makeup')

const handleClose = () => {
  emit('update:open', false)
}

const handleSubmit = async () => {
  if (!props.schedule) return

  if (showExtraFields.value && !newDate.value) {
    alert('请选择新日期')
    return
  }

  const payload: CreateScheduleAdjustmentRequest = {
    schedule_id: props.schedule.id,
    week_number: props.weekNumber,
    type: adjustmentType.value,
    reason: reason.value || undefined,
  }

  if (showExtraFields.value) {
    payload.new_date = newDate.value || undefined
    payload.new_start_time = newStartTime.value || undefined
    payload.new_end_time = newEndTime.value || undefined
    payload.new_classroom = newClassroom.value || undefined
  }

  try {
    await createAdjustment(payload)
    emit('success')
    handleClose()
  } catch {
    // 错误由 mutation 的 error 状态处理，可在外层展示
  }
}
</script>

<template>
  <Dialog
    :open="open"
    title="课程调整"
    @update:open="emit('update:open', $event)"
  >
    <div class="space-y-4">
      <!-- 课程上下文信息 -->
      <p class="text-xs text-white/50">
        课程：{{ schedule?.course_name }} | 班级：{{ schedule?.class_name }} | 第{{ weekNumber }}周
      </p>

      <!-- 调整类型切换 -->
      <div class="flex items-center gap-2">
        <Button
          v-for="opt in typeOptions"
          :key="opt.value"
          type="button"
          size="sm"
          :variant="adjustmentType === opt.value ? 'default' : 'outline'"
          :class="
            'flex-1 ' +
            (adjustmentType === opt.value
              ? opt.color.split(' ').slice(1).join(' ') + ' ' + opt.color.split(' ')[0].replace('text-', 'bg-').replace('-400', '-500').replace('/10', '')
              : '')
          "
          @click="adjustmentType = opt.value"
        >
          {{ opt.label }}
        </Button>
      </div>

      <!-- 公共字段：原因 -->
      <div>
        <label class="mb-1.5 block text-sm text-white/70">调整原因</label>
        <Input
          v-model="reason"
          placeholder="请输入调整原因"
        />
      </div>

      <!-- 额外字段：only for modify / makeup -->
      <div
        v-if="showExtraFields"
        class="space-y-3"
      >
        <div>
          <label class="mb-1.5 block text-sm text-white/70">新日期</label>
          <input
            v-model="newDate"
            type="date"
            class="w-full border border-white/10 bg-white/5 rounded-lg px-3 py-2 text-white text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
          >
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="mb-1.5 block text-sm text-white/70">新开始时间</label>
            <input
              v-model="newStartTime"
              type="time"
              class="w-full border border-white/10 bg-white/5 rounded-lg px-3 py-2 text-white text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
            >
          </div>
          <div>
            <label class="mb-1.5 block text-sm text-white/70">新结束时间</label>
            <input
              v-model="newEndTime"
              type="time"
              class="w-full border border-white/10 bg-white/5 rounded-lg px-3 py-2 text-white text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
            >
          </div>
        </div>

        <div>
          <label class="mb-1.5 block text-sm text-white/70">新教室</label>
          <Input
            v-model="newClassroom"
            placeholder="请输入新教室"
          />
        </div>
      </div>
    </div>

    <template #footer>
      <Button
        variant="outline"
        @click="handleClose"
      >
        取消
      </Button>
      <Button
        :loading="isPending"
        @click="handleSubmit"
      >
        提交
      </Button>
    </template>
  </Dialog>
</template>
