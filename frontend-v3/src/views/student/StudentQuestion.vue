<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useStudentQuestions } from '@/features/question/composables/useStudentQuestions'
import { useAnswers } from '@/features/question/composables/useAnswers'
import QuestionCard from '@/features/question/components/QuestionCard.vue'
import AnswerList from '@/features/question/components/AnswerList.vue'
import AnswerInput from '@/features/question/components/AnswerInput.vue'
import type { Question, Answer } from '@/types/question'

const authStore = useAuthStore()
const currentUserId = computed(() => String(authStore.user?.id || ''))

const selectedQuestion = ref<Question | null>(null)
const editingAnswer = ref<Answer | null>(null)

const { questions, isLoading } = useStudentQuestions()

const selectedId = computed(() => selectedQuestion.value?.id || 0)

const {
  answers,
  isLoading: answersLoading,
  createAnswer,
  updateAnswer,
  deleteAnswer,
} = useAnswers(selectedId)

function handleView(question: Question) {
  selectedQuestion.value = question
  editingAnswer.value = null
}

async function handleSubmit(content: string, isAnonymous: boolean) {
  if (!selectedQuestion.value) return
  if (editingAnswer.value) {
    await updateAnswer({
      id: editingAnswer.value.id,
      data: { content },
    })
    editingAnswer.value = null
  } else {
    await createAnswer({
      question_id: selectedQuestion.value.id,
      content,
      is_anonymous: isAnonymous,
    })
  }
}

function handleEdit(answer: Answer) {
  editingAnswer.value = answer
}

async function handleDelete(answerId: number) {
  if (confirm('确定删除这条回答吗？')) {
    await deleteAnswer(answerId)
  }
}

function cancelEdit() {
  editingAnswer.value = null
}
</script>

<template>
  <div class="p-6 max-w-4xl mx-auto">
    <h1 class="text-2xl font-bold mb-6">课堂问答</h1>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- 问题列表 -->
      <div>
        <div v-if="isLoading" class="text-center py-8 text-gray-400">加载中...</div>
        <div v-else class="space-y-3">
          <QuestionCard
            v-for="q in questions"
            :key="q.id"
            :question="q"
            :class="selectedQuestion?.id === q.id ? 'ring-2 ring-blue-300' : ''"
            @view="handleView(q)"
          />
        </div>
        <div v-if="!isLoading && (!questions || questions.length === 0)" class="text-center py-8 text-gray-400">
          暂无问题
        </div>
      </div>

      <!-- 回答区域 -->
      <div>
        <div v-if="!selectedQuestion" class="text-center py-16 text-gray-400">
          点击左侧问题查看详情
        </div>
        <div v-else>
          <QuestionCard :question="selectedQuestion" class="mb-4" />

          <!-- 回答输入 -->
          <div v-if="selectedQuestion.status === 'active'" class="mb-4">
            <div v-if="editingAnswer" class="mb-2">
              <p class="text-sm text-gray-500 mb-2">修改回答</p>
              <AnswerInput
                placeholder="修改你的回答..."
                submit-label="保存"
                @submit="handleSubmit"
              />
              <button class="text-xs text-gray-500 mt-1" @click="cancelEdit">取消修改</button>
            </div>
            <div v-else>
              <AnswerInput
                placeholder="写下你的回答..."
                submit-label="提交回答"
                show-anonymous
                @submit="handleSubmit"
              />
            </div>
          </div>
          <div v-else class="mb-4 p-3 bg-gray-50 rounded text-sm text-gray-500 text-center">
            该问题已结束，无法回答
          </div>

          <!-- 回答列表 -->
          <h3 class="text-sm font-semibold text-gray-600 mb-2">
            回答 ({{ answers?.length || 0 }})
          </h3>
          <div v-if="answersLoading" class="text-center py-8 text-gray-400">加载中...</div>
          <AnswerList
            v-else
            :answers="answers || []"
            :current-user-id="currentUserId"
            :is-teacher="false"
            @edit="handleEdit"
            @delete="handleDelete"
          />
        </div>
      </div>
    </div>
  </div>
</template>
