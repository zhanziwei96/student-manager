<script setup lang="ts">
import type { Question } from '@/types/question'

interface Props {
  question: Question
  showActions?: boolean
}

withDefaults(defineProps<Props>(), {
  showActions: false,
})

const emit = defineEmits<{
  view: [questionId: number]
  close: [questionId: number]
}>()

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('zh-CN')
}
</script>

<template>
  <div class="bg-white rounded-lg border border-gray-200 p-4 shadow-sm hover:shadow-md transition-shadow">
    <div class="flex justify-between items-start mb-2">
      <div class="flex items-center gap-2">
        <span
          :class="[
            'px-2 py-0.5 text-xs rounded-full',
            question.status === 'active'
              ? 'bg-green-100 text-green-700'
              : 'bg-gray-100 text-gray-600',
          ]"
        >
          {{ question.status === 'active' ? '进行中' : '已结束' }}
        </span>
        <span v-if="question.is_realtime" class="px-2 py-0.5 text-xs rounded-full bg-orange-100 text-orange-700">
          实时
        </span>
        <span v-if="question.class_name" class="text-xs text-gray-500">
          {{ question.class_name }}
        </span>
        <span v-else class="text-xs text-blue-500">所有班级</span>
      </div>
      <span class="text-xs text-gray-400">{{ formatDate(question.created_at) }}</span>
    </div>

    <p class="text-gray-800 mb-3">{{ question.content }}</p>

    <div class="flex justify-between items-center">
      <div class="flex items-center gap-4 text-sm text-gray-500">
        <span>提问: {{ question.teacher_name || '未知' }}</span>
        <span>{{ question.answer_count }} 条回答</span>
      </div>

      <div v-if="showActions" class="flex gap-2">
        <button
          class="px-3 py-1 text-sm bg-blue-50 text-blue-600 rounded hover:bg-blue-100"
          @click="emit('view', question.id)"
        >
          查看回答
        </button>
        <button
          v-if="question.status === 'active'"
          class="px-3 py-1 text-sm bg-gray-50 text-gray-600 rounded hover:bg-gray-100"
          @click="emit('close', question.id)"
        >
          结束
        </button>
      </div>
    </div>
  </div>
</template>
