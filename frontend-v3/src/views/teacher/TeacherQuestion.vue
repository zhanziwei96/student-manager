<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useTeacherQuestions } from '@/features/question/composables/useTeacherQuestions'
import { useAnswers } from '@/features/question/composables/useAnswers'
import QuestionCard from '@/features/question/components/QuestionCard.vue'
import AnswerList from '@/features/question/components/AnswerList.vue'
import AnswerInput from '@/features/question/components/AnswerInput.vue'
import type { Question } from '@/types/question'

const authStore = useAuthStore()
const currentUserId = computed(() => String(authStore.user?.id || ''))

const statusFilter = ref('')
const selectedQuestion = ref<Question | null>(null)
const showCreateForm = ref(false)
const newQuestionContent = ref('')
const newQuestionClass = ref('')
const newQuestionRealtime = ref(false)

const { questions, isLoading, createQuestion, closeQuestion } = useTeacherQuestions({
  status: statusFilter,
})

const selectedId = computed(() => selectedQuestion.value?.id || 0)

const {
  answers,
  isLoading: answersLoading,
  replyAnswer,
  starAnswer,
} = useAnswers(selectedId)

const replyTarget = ref<number | null>(null)

async function handleCreate() {
  if (!newQuestionContent.value.trim()) return
  await createQuestion({
    content: newQuestionContent.value.trim(),
    class_name: newQuestionClass.value || undefined,
    is_realtime: newQuestionRealtime.value,
  })
  showCreateForm.value = false
  newQuestionContent.value = ''
  newQuestionClass.value = ''
  newQuestionRealtime.value = false
}

async function handleClose(questionId: number) {
  await closeQuestion(questionId)
}

function handleView(question: Question) {
  selectedQuestion.value = question
  replyTarget.value = null
}

async function handleReply(answerId: number, content: string) {
  await replyAnswer({ answerId, data: { answer_id: answerId, content } })
  replyTarget.value = null
}

async function handleStar(answerId: number, starred: boolean) {
  await starAnswer({ answerId, starred })
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('zh-CN')
}
</script>

<template>
  <div class="p-6 max-w-6xl mx-auto">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">课堂问答</h1>
      <button
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        @click="showCreateForm = !showCreateForm"
      >
        {{ showCreateForm ? '取消' : '发布问题' }}
      </button>
    </div>

    <!-- 发布问题表单 -->
    <div v-if="showCreateForm" class="bg-white rounded-lg border border-gray-200 p-4 mb-6">
      <textarea
        v-model="newQuestionContent"
        placeholder="请输入问题内容..."
        rows="3"
        class="w-full px-3 py-2 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <div class="flex gap-4 mt-3 items-center">
        <input
          v-model="newQuestionClass"
          placeholder="目标班级（留空表示所有班级）"
          class="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
        />
        <label class="flex items-center gap-2 cursor-pointer">
          <input v-model="newQuestionRealtime" type="checkbox" class="w-4 h-4" />
          <span class="text-sm">实时提问</span>
        </label>
        <button
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          :disabled="!newQuestionContent.trim()"
          @click="handleCreate"
        >
          发布
        </button>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- 问题列表 -->
      <div>
        <div class="flex gap-2 mb-4">
          <button
            :class="['px-3 py-1 text-sm rounded', !statusFilter ? 'bg-blue-100 text-blue-700' : 'bg-gray-100']"
            @click="statusFilter = ''"
          >
            全部
          </button>
          <button
            :class="['px-3 py-1 text-sm rounded', statusFilter === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100']"
            @click="statusFilter = 'active'"
          >
            进行中
          </button>
          <button
            :class="['px-3 py-1 text-sm rounded', statusFilter === 'closed' ? 'bg-gray-200 text-gray-700' : 'bg-gray-100']"
            @click="statusFilter = 'closed'"
          >
            已结束
          </button>
        </div>

        <div v-if="isLoading" class="text-center py-8 text-gray-400">加载中...</div>
        <div v-else class="space-y-3">
          <QuestionCard
            v-for="q in questions"
            :key="q.id"
            :question="q"
            show-actions
            :class="selectedQuestion?.id === q.id ? 'ring-2 ring-blue-300' : ''"
            @view="handleView(q)"
            @close="handleClose"
          />
        </div>
      </div>

      <!-- 回答详情 -->
      <div>
        <div v-if="!selectedQuestion" class="text-center py-16 text-gray-400">
          点击左侧问题查看回答
        </div>
        <div v-else>
          <div class="mb-4">
            <h2 class="text-lg font-semibold mb-1">{{ selectedQuestion.content }}</h2>
            <p class="text-sm text-gray-500">
              {{ selectedQuestion.class_name || '所有班级' }} · {{ formatDate(selectedQuestion.created_at) }}
            </p>
          </div>

          <div v-if="answersLoading" class="text-center py-8 text-gray-400">加载回答中...</div>
          <AnswerList
            v-else
            :answers="answers || []"
            :current-user-id="currentUserId"
            :is-teacher="true"
            @reply="replyTarget = $event"
            @star="handleStar"
          />

          <!-- 追问输入框 -->
          <div v-if="replyTarget" class="mt-4">
            <AnswerInput
              placeholder="请输入追问内容..."
              submit-label="发送追问"
              @submit="(content) => handleReply(replyTarget!, content)"
            />
            <button class="text-xs text-gray-500 mt-1" @click="replyTarget = null">取消</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
