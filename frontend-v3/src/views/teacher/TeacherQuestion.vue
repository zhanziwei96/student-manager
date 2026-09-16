<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQueryClient } from '@tanstack/vue-query'
import { useTeacherQuestions } from '@/features/question/composables/useTeacherQuestions'
import { useAnswers } from '@/features/question/composables/useAnswers'
import QuestionCard from '@/features/question/components/QuestionCard.vue'
import AnswerList from '@/features/question/components/AnswerList.vue'
import AnswerInput from '@/features/question/components/AnswerInput.vue'
import { Checkbox, PullToRefreshIndicator } from '@/components/ui'
import { useClasses } from '@/composables'
import { usePullToRefresh } from '@/composables/usePullToRefresh'
import {  } from 'lucide-vue-next'
import type { Question } from '@/types/question'
import type { AdminClass } from '@/types'

const statusFilter = ref('')
const selectedQuestion = ref<Question | null>(null)
const showCreateForm = ref(false)
const newQuestionContent = ref('')
const newQuestionClassIds = ref<number[]>([])  // 空数组 = 所有班级可见
const newQuestionRealtime = ref(false)

// 目标班级选项（空选 = 所有班级）
const { data: classes } = useClasses()

/** 班级选项按「届 · 专业」分组，组内保持后端的届/班级名顺序 */
const classGroups = computed(() => {
  const groups = new Map<string, { label: string; items: AdminClass[] }>()
  for (const cls of classes.value ?? []) {
    const label = `${cls.cohort_year}届 · ${cls.major}`
    const group = groups.get(label) ?? { label, items: [] }
    group.items.push(cls)
    groups.set(label, group)
  }
  return [...groups.values()].sort((a, b) => b.label.localeCompare(a.label, 'zh-Hans-CN'))
})

const toggleClassId = (ids: number[], classId: number, checked: boolean) => {
  if (checked) {
    if (!ids.includes(classId)) ids.push(classId)
    return
  }
  const index = ids.indexOf(classId)
  if (index >= 0) ids.splice(index, 1)
}

const toggleAllClassIds = (ids: number[]) => {
  const all = classes.value ?? []
  if (ids.length === all.length) ids.length = 0
  else ids.splice(0, ids.length, ...all.map((c) => c.id))
}

const { questions, isLoading, createQuestion, closeQuestion } = useTeacherQuestions({
  status: statusFilter,
})

// 下拉刷新（移动端手势）：await 问题列表与当前回答列表后 refreshing 复位
const queryClient = useQueryClient()
const pageRef = ref<HTMLElement | null>(null)
const { pulling, pullDistance, refreshing } = usePullToRefresh(pageRef, async () => {
  await Promise.all([
    queryClient.refetchQueries({ queryKey: ['teacher-questions'] }),
    queryClient.refetchQueries({ queryKey: ['answers'] }),
  ])
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
    class_ids: [...newQuestionClassIds.value],
    is_realtime: newQuestionRealtime.value,
  })
  showCreateForm.value = false
  newQuestionContent.value = ''
  newQuestionClassIds.value = []
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
  <div ref="pageRef" class="overscroll-y-contain p-6 max-w-6xl mx-auto">
    <PullToRefreshIndicator :pulling="pulling" :pull-distance="pullDistance" :refreshing="refreshing" />
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">课堂问答</h1>
      <button
        class="px-4 py-2 min-h-[44px] bg-blue-600 text-white rounded-lg hover:bg-blue-700"
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
      <div class="mt-3">
        <div class="flex items-center justify-between">
          <label class="text-sm text-gray-500">目标班级</label>
          <button
            type="button"
            data-testid="create-select-all-classes"
            class="px-3 py-1 min-h-[44px] text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
            @click="toggleAllClassIds(newQuestionClassIds)"
          >
            {{ newQuestionClassIds.length === (classes?.length ?? 0) && (classes?.length ?? 0) > 0 ? '清空' : '全选' }}
          </button>
        </div>
        <div
          data-testid="question-class-panel"
          class="mt-1 max-h-56 space-y-3 overflow-y-auto rounded-xl border border-gray-200 p-3"
        >
          <div
            v-for="group in classGroups"
            :key="group.label"
          >
            <p class="mb-1 text-xs font-medium text-gray-400">
              {{ group.label }}
            </p>
            <div class="space-y-1.5">
              <div
                v-for="cls in group.items"
                :key="cls.id"
                class="flex items-center gap-2"
              >
                <Checkbox
                  :checked="newQuestionClassIds.includes(cls.id)"
                  @update:checked="(checked) => toggleClassId(newQuestionClassIds, cls.id, checked)"
                />
                <span class="text-sm">{{ cls.name }}</span>
              </div>
            </div>
          </div>
          <p
            v-if="classGroups.length === 0"
            class="text-xs text-gray-400"
          >
            暂无班级
          </p>
        </div>
        <p
          class="mt-1 text-xs"
          :class="newQuestionClassIds.length === 0 ? 'text-gray-500' : 'text-gray-400'"
        >
          {{ newQuestionClassIds.length === 0
            ? '未选择班级 = 所有班级可见'
            : `已选 ${newQuestionClassIds.length} 个班级` }}
        </p>
      </div>
      <div class="flex gap-4 mt-3 items-center">
        <label class="flex items-center gap-2 cursor-pointer">
          <input v-model="newQuestionRealtime" type="checkbox" class="w-4 h-4" />
          <span class="text-sm">实时提问</span>
        </label>
        <button
          class="px-4 py-2 min-h-[44px] bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
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
            :class="['px-3 py-1 min-h-[44px] text-sm rounded', !statusFilter ? 'bg-blue-100 text-blue-700' : 'bg-gray-100']"
            @click="statusFilter = ''"
          >
            全部
          </button>
          <button
            :class="['px-3 py-1 min-h-[44px] text-sm rounded', statusFilter === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100']"
            @click="statusFilter = 'active'"
          >
            进行中
          </button>
          <button
            :class="['px-3 py-1 min-h-[44px] text-sm rounded', statusFilter === 'closed' ? 'bg-gray-200 text-gray-700' : 'bg-gray-100']"
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
            <button class="text-xs text-gray-500 mt-1 inline-flex min-h-[44px] min-w-[44px] items-center px-2 -mx-2" @click="replyTarget = null">取消</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
