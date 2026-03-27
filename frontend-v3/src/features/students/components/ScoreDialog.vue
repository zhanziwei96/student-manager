<script setup lang="ts">
import { ref, watch } from 'vue'
import { Dialog, Button, Input, Label } from '@/components/ui'
import type { Student } from '@/types'

/**
 * 分数调整对话框组件
 * 
 * 用于自定义分数调整，支持输入分数变化和原因
 */

interface Props {
  open: boolean
  student: Student | null
  isLoading?: boolean
  defaultScore?: number
  defaultReason?: string
}

const props = withDefaults(defineProps<Props>(), {
  isLoading: false,
  defaultScore: 0,
  defaultReason: '',
})

const emit = defineEmits<{
  'update:open': [value: boolean]
  submit: [scoreChange: number, reason: string]
}>()

// 本地状态
const scoreChange = ref(0)
const reason = ref('')

// 当对话框打开或学生变化时，重置表单
watch(() => [props.open, props.student], () => {
  if (props.open && props.student) {
    scoreChange.value = props.defaultScore || 10
    reason.value = props.defaultReason || ''
  }
}, { immediate: true })

const handleSubmit = () => {
  emit('submit', scoreChange.value, reason.value)
}

const handleCancel = () => {
  emit('update:open', false)
}
</script>

<template>
  <Dialog 
    :open="open" 
    :title="student ? `调整 ${student.name} 的分数` : '调整分数'"
    @update:open="$emit('update:open', $event)"
  >
    <div class="space-y-4">
      <p
        v-if="student"
        class="text-white/60"
      >
        更新 <span class="font-medium text-white">{{ student.name }}</span> 的分数
      </p>
      <div class="space-y-2">
        <Label for="scoreChange">分数变化</Label>
        <Input
          id="scoreChange"
          v-model.number="scoreChange"
          type="number"
          placeholder="输入分数（正数或负数）"
        />
      </div>
      <div class="space-y-2">
        <Label for="reason">原因</Label>
        <Input
          id="reason"
          v-model="reason"
          placeholder="输入分数变化原因"
        />
      </div>
    </div>
    <template #footer>
      <Button
        variant="outline"
        @click="handleCancel"
      >
        取消
      </Button>
      <Button
        :loading="isLoading"
        @click="handleSubmit"
      >
        更新分数
      </Button>
    </template>
  </Dialog>
</template>
