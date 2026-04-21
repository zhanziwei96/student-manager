<script setup lang="ts">
import type { Answer } from '@/types/question'

interface Props {
  answers: Answer[]
  currentUserId: string
  isTeacher: boolean
}

defineProps<Props>()

const emit = defineEmits<{
  reply: [answerId: number]
  star: [answerId: number, starred: boolean]
  edit: [answer: Answer]
  delete: [answerId: number]
}>()

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('zh-CN')
}

function isReply(answer: Answer): boolean {
  return !!answer.parent_id
}
</script>

<template>
  <div class="space-y-3">
    <div
      v-for="answer in answers"
      :key="answer.id"
      :class="[
        'p-4 rounded-lg border',
        isReply(answer)
          ? 'ml-8 bg-gray-50 border-gray-200'
          : 'bg-white border-gray-200',
        answer.is_starred ? 'border-yellow-300 bg-yellow-50/30' : '',
      ]"
    >
      <div class="flex justify-between items-start mb-2">
        <div class="flex items-center gap-2">
          <span class="font-medium text-sm">
            {{ answer.student_name || '匿名' }}
          </span>
          <span v-if="answer.is_anonymous" class="text-xs text-gray-400">(匿名)</span>
          <span
            v-if="answer.is_starred"
            class="px-1.5 py-0.5 text-xs rounded bg-yellow-100 text-yellow-700"
          >
            ⭐ 优秀
          </span>
        </div>
        <span class="text-xs text-gray-400">{{ formatDate(answer.created_at) }}</span>
      </div>

      <p class="text-gray-800 text-sm mb-3">{{ answer.content }}</p>

      <div class="flex gap-2">
        <button
          v-if="isTeacher && !isReply(answer)"
          class="text-xs text-blue-600 hover:text-blue-800"
          @click="emit('reply', answer.id)"
        >
          追问
        </button>
        <button
          v-if="isTeacher && !isReply(answer)"
          :class="[
            'text-xs',
            answer.is_starred ? 'text-yellow-600 hover:text-yellow-800' : 'text-gray-500 hover:text-gray-700',
          ]"
          @click="emit('star', answer.id, !answer.is_starred)"
        >
          {{ answer.is_starred ? '取消优秀' : '标记优秀' }}
        </button>
        <button
          v-if="!isTeacher && answer.student_id === currentUserId"
          class="text-xs text-gray-500 hover:text-gray-700"
          @click="emit('edit', answer)"
        >
          修改
        </button>
        <button
          v-if="!isTeacher && answer.student_id === currentUserId"
          class="text-xs text-red-500 hover:text-red-700"
          @click="emit('delete', answer.id)"
        >
          删除
        </button>
      </div>
    </div>

    <div v-if="answers.length === 0" class="text-center text-gray-400 py-8">
      暂无回答
    </div>
  </div>
</template>
