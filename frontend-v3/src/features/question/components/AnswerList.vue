<script setup lang="ts">
import type { Answer } from '@/types/question'
import { Pencil, Trash2, Star, CornerDownRight } from 'lucide-vue-next'

interface Props {
  answers: Answer[]
  isTeacher: boolean
}

defineProps<Props>()

const emit = defineEmits<{
  reply: [answerId: number]
  star: [answerId: number, starred: boolean]
  edit: [answer: Answer]
  delete: [answerId: number]
}>()

function timeAgo(iso: string): string {
  const now = Date.now()
  const then = new Date(iso).getTime()
  const diff = Math.floor((now - then) / 1000)
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)} 分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)} 小时前`
  return `${Math.floor(diff / 86400)} 天前`
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
        'rounded-xl border p-4 transition-all',
        isReply(answer)
          ? 'ml-6 bg-[#fafafa] border-[#e5e5e5]'
          : 'bg-white border-[#e5e5e5]',
        answer.is_starred ? 'border-amber-200 bg-amber-50/40' : '',
      ]"
    >
      <!-- Reply indicator -->
      <div v-if="isReply(answer)" class="flex items-center gap-1 mb-2 text-[#a3a3a3]">
        <CornerDownRight class="h-3 w-3" />
        <span class="text-xs">追问回复</span>
      </div>

      <!-- Header: Name + Badge + Time -->
      <div class="flex items-center justify-between mb-2">
        <div class="flex items-center gap-2">
          <div
            :class="[
              'h-7 w-7 rounded-full flex items-center justify-center text-xs font-medium flex-shrink-0',
              answer.is_anonymous
                ? 'bg-purple-50 text-purple-500'
                : 'bg-[#f5f5f5] text-[#737373]',
            ]"
          >
            {{ answer.is_anonymous ? '?' : (answer.student_name || '?')[0] }}
          </div>
          <span
            v-if="answer.is_anonymous"
            class="text-sm font-medium text-purple-500"
          >
            匿名同学
          </span>
          <span v-else class="text-sm font-medium text-black">
            {{ answer.student_name || '未知' }}
          </span>
          <span
            v-if="answer.is_starred"
            class="flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] rounded bg-amber-50 text-amber-600 font-medium"
          >
            <Star class="h-3 w-3 fill-amber-400 text-amber-400" />
            优秀
          </span>
        </div>
        <span class="text-xs text-[#a3a3a3]">{{ timeAgo(answer.created_at) }}</span>
      </div>

      <!-- Content -->
      <p class="text-sm text-[#262626] pl-9 mb-2 leading-relaxed">{{ answer.content }}</p>

      <!-- Actions -->
      <div class="flex gap-1 pl-9">
        <button
          v-if="isTeacher && !isReply(answer)"
          class="flex items-center gap-1 px-2 py-1 text-xs text-[#737373] rounded-lg hover:bg-[#fafafa] hover:text-black transition-colors"
          @click="emit('reply', answer.id)"
        >
          <CornerDownRight class="h-3 w-3" />
          追问
        </button>
        <button
          v-if="isTeacher && !isReply(answer)"
          class="flex items-center gap-1 px-2 py-1 text-xs rounded-lg transition-colors"
          :class="answer.is_starred ? 'text-amber-500 hover:bg-amber-50' : 'text-[#737373] hover:bg-[#fafafa] hover:text-black'"
          @click="emit('star', answer.id, !answer.is_starred)"
        >
          <Star :class="['h-3 w-3', answer.is_starred ? 'fill-amber-400' : '']" />
          {{ answer.is_starred ? '取消优秀' : '标记优秀' }}
        </button>
        <button
          v-if="!isTeacher && answer.is_own"
          class="flex items-center gap-1 px-2 py-1 text-xs text-[#737373] rounded-lg hover:bg-[#fafafa] hover:text-black transition-colors"
          @click="emit('edit', answer)"
        >
          <Pencil class="h-3 w-3" />
          修改
        </button>
        <button
          v-if="!isTeacher && answer.is_own"
          class="flex items-center gap-1 px-2 py-1 text-xs text-red-400 rounded-lg hover:bg-red-50 hover:text-red-500 transition-colors"
          @click="emit('delete', answer.id)"
        >
          <Trash2 class="h-3 w-3" />
          删除
        </button>
      </div>
    </div>

    <!-- Empty -->
    <div v-if="answers.length === 0" class="flex flex-col items-center py-12">
      <p class="text-sm text-[#a3a3a3]">还没有人回答，快来抢沙发</p>
    </div>
  </div>
</template>
