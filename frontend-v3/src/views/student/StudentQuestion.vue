<script setup lang="ts">
import { ref, computed } from 'vue'
import { useStudentQuestions } from '@/features/question/composables/useStudentQuestions'
import { useAnswers } from '@/features/question/composables/useAnswers'
import { useToast } from '@/composables/useToast'
import AnswerList from '@/features/question/components/AnswerList.vue'
import AnswerInput from '@/features/question/components/AnswerInput.vue'
import type { Question, Answer } from '@/types/question'
import { MessageCircle, Loader2, ChevronRight, Hand } from 'lucide-vue-next'

const { success: showSuccess, error: showError } = useToast()

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

const activeCount = computed(() => questions.value?.filter(q => q.status === 'active').length || 0)

function handleView(question: Question) {
  selectedQuestion.value = question
  editingAnswer.value = null
}

async function handleSubmit(content: string, isAnonymous: boolean) {
  if (!selectedQuestion.value) return
  try {
    if (editingAnswer.value) {
      await updateAnswer({ id: editingAnswer.value.id, data: { content } })
      editingAnswer.value = null
      showSuccess('回答已修改')
    } else {
      await createAnswer({
        question_id: selectedQuestion.value.id,
        content,
        is_anonymous: isAnonymous,
      })
      showSuccess(isAnonymous ? '匿名回答成功' : '回答成功')
    }
  } catch (err: any) {
    showError(err.message || '操作失败')
  }
}

function handleEdit(answer: Answer) {
  editingAnswer.value = answer
}

async function handleDelete(answerId: number) {
  if (!confirm('确定删除这条回答吗？')) return
  try {
    await deleteAnswer(answerId)
    showSuccess('回答已删除')
  } catch (err: any) {
    showError(err.message || '删除失败')
  }
}

function cancelEdit() {
  editingAnswer.value = null
}

function timeAgo(iso: string): string {
  const now = Date.now()
  const then = new Date(iso).getTime()
  const diff = Math.floor((now - then) / 1000)
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)} 分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)} 小时前`
  return `${Math.floor(diff / 86400)} 天前`
}
</script>

<template>
  <div>
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-2xl font-medium text-black">
        课堂问答
      </h1>
      <p class="text-[#737373]">
        {{ activeCount > 0 ? `${activeCount} 个问题等你来答` : '暂时没有新问题' }}
      </p>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="flex h-64 items-center justify-center">
      <Loader2 class="h-8 w-8 animate-spin text-[#a3a3a3]" />
    </div>

    <!-- Empty State -->
    <div
      v-else-if="!questions || questions.length === 0"
      class="flex flex-col items-center justify-center py-20"
    >
      <div class="h-16 w-16 rounded-full bg-[#fafafa] flex items-center justify-center mb-4">
        <MessageCircle class="h-8 w-8 text-[#a3a3a3]" />
      </div>
      <p class="text-[#737373] mb-1">老师还没有发布问题</p>
      <p class="text-sm text-[#a3a3a3]">稍等一下，有问题就能回答啦</p>
    </div>

    <!-- Main Content -->
    <div v-else class="flex flex-col lg:flex-row gap-6">
      <!-- Left: Question List -->
      <div class="w-full lg:w-[340px] lg:flex-shrink-0 space-y-2">
        <div
          v-for="q in questions"
          :key="q.id"
          :class="[
            'group relative bg-white rounded-xl border p-4 cursor-pointer transition-all',
            selectedQuestion?.id === q.id
              ? 'border-black shadow-sm'
              : 'border-[#e5e5e5] hover:border-[#d4d4d4]',
            q.status === 'closed' ? 'opacity-60' : '',
          ]"
          @click="handleView(q)"
        >
          <div class="flex items-start gap-3">
            <div
              :class="[
                'flex h-9 w-9 items-center justify-center rounded-full flex-shrink-0',
                q.status === 'active' ? 'bg-green-50 text-green-600' : 'bg-[#f5f5f5] text-[#a3a3a3]',
              ]"
            >
              <Hand v-if="q.status === 'active'" class="h-4 w-4" />
              <MessageCircle v-else class="h-4 w-4" />
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-black truncate">{{ q.content }}</p>
              <div class="flex items-center gap-2 mt-1.5 text-xs text-[#a3a3a3]">
                <span>{{ q.teacher_name }}</span>
                <span class="text-[#e5e5e5]">|</span>
                <span>{{ q.answer_count }} 条回答</span>
                <span class="text-[#e5e5e5]">|</span>
                <span>{{ timeAgo(q.created_at) }}</span>
              </div>
            </div>
            <ChevronRight
              :class="[
                'h-4 w-4 flex-shrink-0 mt-2 transition-colors',
                selectedQuestion?.id === q.id ? 'text-black' : 'text-[#d4d4d4] group-hover:text-[#737373]',
              ]"
            />
          </div>
        </div>
      </div>

      <!-- Right: Answer Area -->
      <div class="flex-1 min-w-0">
        <!-- No Question Selected -->
        <div
          v-if="!selectedQuestion"
          class="flex flex-col items-center justify-center py-20"
        >
          <div class="h-12 w-12 rounded-full bg-[#fafafa] flex items-center justify-center mb-3">
            <MessageCircle class="h-6 w-6 text-[#a3a3a3]" />
          </div>
          <p class="text-[#737373] text-sm">点击左边的问题开始回答</p>
        </div>

        <!-- Question Detail + Answers -->
        <div v-else>
          <!-- Question Banner -->
          <div class="bg-white rounded-xl border border-[#e5e5e5] p-5 mb-5">
            <div class="flex items-center gap-2 mb-2">
              <span
                :class="[
                  'px-2 py-0.5 text-xs rounded-full font-medium',
                  selectedQuestion.status === 'active'
                    ? 'bg-green-50 text-green-700'
                    : 'bg-[#f5f5f5] text-[#737373]',
                ]"
              >
                {{ selectedQuestion.status === 'active' ? '进行中' : '已结束' }}
              </span>
              <span v-if="!selectedQuestion.class_name" class="text-xs text-blue-500">所有班级</span>
              <span v-else class="text-xs text-[#a3a3a3]">{{ selectedQuestion.class_name }}</span>
            </div>
            <p class="text-black font-medium">{{ selectedQuestion.content }}</p>
            <p class="text-xs text-[#a3a3a3] mt-2">
              {{ selectedQuestion.teacher_name }} · {{ timeAgo(selectedQuestion.created_at) }}
            </p>
          </div>

          <!-- Answer Input -->
          <div v-if="selectedQuestion.status === 'active'" class="mb-5">
            <div v-if="editingAnswer" class="mb-2">
              <div class="flex items-center justify-between mb-2">
                <p class="text-sm text-[#737373]">修改回答</p>
                <button class="text-xs text-[#a3a3a3] hover:text-black" @click="cancelEdit">取消</button>
              </div>
              <AnswerInput
                placeholder="修改你的回答..."
                submit-label="保存"
                @submit="handleSubmit"
              />
            </div>
            <div v-else>
              <AnswerInput
                placeholder="说说你的想法..."
                submit-label="发送"
                show-anonymous
                @submit="handleSubmit"
              />
            </div>
          </div>
          <div v-else class="mb-5 p-4 bg-[#fafafa] rounded-xl text-center">
            <p class="text-sm text-[#737373]">这个问题已经结束啦</p>
          </div>

          <!-- Answers -->
          <div>
            <div class="flex items-center gap-2 mb-3">
              <h3 class="text-sm font-medium text-black">回答</h3>
              <span class="text-xs text-[#a3a3a3] bg-[#fafafa] px-2 py-0.5 rounded-full">
                {{ answers?.length || 0 }}
              </span>
            </div>

            <div v-if="answersLoading" class="flex justify-center py-8">
              <Loader2 class="h-6 w-6 animate-spin text-[#a3a3a3]" />
            </div>

            <AnswerList
              v-else
              :answers="answers || []"
              :is-teacher="false"
              @edit="handleEdit"
              @delete="handleDelete"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
