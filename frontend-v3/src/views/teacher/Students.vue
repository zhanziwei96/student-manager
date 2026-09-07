<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { useToast } from '@/composables'
import { StudentCard, ScoreDialog, StudentFilters, useStudentScore, usePaginatedStudents } from '@/features/students'
import { DataContainer, Card, Button, Dialog, Input, Label, Select } from '@/components/ui'
import type { Student } from '@/types'
import { studentsApi } from '@/api'
import type { StudentSubjectScore } from '@/api/students'
import { getErrorMessage } from '@/lib/error'
import { Users, GraduationCap, Search, ChevronLeft, ChevronRight, ChevronDown, ChevronUp } from 'lucide-vue-next'

/**
 * 教师学生管理页面 - FE-006 重构后
 *
 * 使用 Feature-based 架构：
 * - 使用 features/students 的组件和 composables
 * - 视图层只负责页面布局和状态组合
 * - 业务逻辑下沉到 Feature 层
 * - 学生列表服务端分页（usePaginatedStudents），搜索时前端过滤
 */

// === 数据获取（服务端分页） ===
const {
  page,
  searchQuery,
  className,
  isSearching,
  classOptions,
  filteredStudents,
  total: totalStudents,
  totalPages,
  isPending,
  error,
  refetch,
  setSearchQuery,
  setClassFilter,
} = usePaginatedStudents()


// 统计信息（总数来自服务端 total；已签到/平均分基于当前展示列表）
const stats = computed(() => {
  const total = isSearching.value ? filteredStudents.value.length : totalStudents.value
  const checkedIn = filteredStudents.value.filter(s => s.checkin_status === 'checked_in').length
  const avgScore = filteredStudents.value.length > 0
    ? Math.round(filteredStudents.value.reduce((sum, s) => sum + s.score, 0) / filteredStudents.value.length)
    : 0

  return [
    { title: '学生总数', value: total, icon: Users },
    { title: '已签到', value: checkedIn, icon: GraduationCap },
    { title: '平均分数', value: avgScore, icon: Search },
  ]
})

// === Feature composables ===
const { updateScore, isUpdating, updatingStudentId } = useStudentScore()

// === 分数对话框状态 ===
const selectedStudent = ref<Student | null>(null)
const showScoreDialog = ref(false)
const defaultScore = ref(0)
const defaultReason = ref('')

// === Toast 状态 (队列模式) ===
const { success: showSuccessToast, error: showErrorToast } = useToast()

const queryClient = useQueryClient()

// === 科目分数展开区 ===
const expandedStudentId = ref<string | null>(null)

// 切换展开/收起某学生的科目分数
const toggleSubjects = (studentId: string) => {
  expandedStudentId.value = expandedStudentId.value === studentId ? null : studentId
}

// 展开学生的科目分数（按学生缓存，收起时停用查询）
const { data: subjectScores, isPending: isSubjectsPending } = useQuery({
  queryKey: computed(() => ['student-subjects', expandedStudentId.value]),
  queryFn: () => studentsApi.getSubjects(expandedStudentId.value!),
  enabled: computed(() => expandedStudentId.value !== null),
})

// === 科目分数调整弹窗（下拉选科目 + 加减分） ===
const showSubjectScoreDialog = ref(false)
const scoreStudent = ref<Student | null>(null)
const scoreSubjectId = ref<string | number>('')
const subjectScoreChange = ref(0)
const subjectScoreReason = ref('')
const isUpdatingSubjectScore = ref(false)

// 弹窗科目下拉选项（来自该学生已展开的科目分数）
const scoreSubjectOptions = computed(() =>
  (subjectScores.value ?? []).map((s: StudentSubjectScore) => ({
    value: s.subject_id,
    label: `${s.subject_name}（当前 ${s.score} 分）`,
  }))
)

// 从展开区打开科目分数调整弹窗
const openSubjectScoreDialog = (student: Student) => {
  scoreStudent.value = student
  scoreSubjectId.value = subjectScores.value?.[0]?.subject_id ?? ''
  subjectScoreChange.value = 0
  subjectScoreReason.value = ''
  showSubjectScoreDialog.value = true
}

const handleUpdateSubjectScore = async () => {
  if (!scoreStudent.value || scoreSubjectId.value === '') return
  if (!subjectScoreReason.value.trim()) {
    showErrorToast('请输入分数变化原因')
    return
  }

  try {
    isUpdatingSubjectScore.value = true
    const studentId = scoreStudent.value.student_id
    await studentsApi.updateSubjectScore(studentId, Number(scoreSubjectId.value), subjectScoreChange.value, subjectScoreReason.value.trim())
    // 刷新该学生科目分数与学生列表总分
    await queryClient.invalidateQueries({ queryKey: ['student-subjects', studentId] })
    await queryClient.invalidateQueries({ queryKey: ['students'] })
    showSubjectScoreDialog.value = false
    showSuccessToast(`${scoreStudent.value.name} 的科目分数已更新`)
  } catch (err: unknown) {
    showErrorToast(getErrorMessage(err) || '更新科目分数失败')
  } finally {
    isUpdatingSubjectScore.value = false
  }
}

// === 快速分数选项 ===
const quickScoreOptions = [
  { label: '课堂提问', score: 2, icon: 'MessageCircle' },
  { label: '违反纪律', score: -2, icon: 'AlertTriangle' },
  { label: '旷课', score: -5, icon: 'UserX' },
]

// === 事件处理 ===
const openScoreDialog = (student: Student, score: number = 10, reason: string = '加分') => {
  selectedStudent.value = student
  defaultScore.value = score
  defaultReason.value = reason
  showScoreDialog.value = true
}

const handleQuickScore = async (student: Student, score: number, reason: string) => {
  try {
    await updateScore(student.student_id, score, reason)
    
    showSuccessToast(`${student.name} ${score > 0 ? '+' : ''}${score}分`)
  } catch (err: unknown) {
    showErrorToast(getErrorMessage(err) || '调整分数失败')
  }
}

const handleUpdateScore = async (scoreChange: number, reason: string) => {
  if (!selectedStudent.value) return

  try {
    await updateScore(selectedStudent.value.student_id, scoreChange, reason)

    showSuccessToast(`${selectedStudent.value.name} 的分数已更新`)
    showScoreDialog.value = false
  } catch (err: unknown) {
    showErrorToast(getErrorMessage(err) || '更新分数失败')
  }
}
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-5">
      <div>
        <h1 class="text-2xl font-medium text-black">
          我的学生
        </h1>
        <p class="text-[#737373]">
          查看和管理学生分数
        </p>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-3 gap-3 sm:gap-4 mb-5">
      <Card
        v-for="stat in stats"
        :key="stat.title"
        class="group relative overflow-hidden p-3 sm:p-4"
        :class="'bg-white border-[#e5e5e5]'"
      >
        <div class="relative z-10">
          <div class="flex items-center justify-between">
            <div
              class="flex h-8 w-8 sm:h-10 sm:w-10 items-center justify-center rounded-xl transition-transform"
              :class="'bg-primary/10 text-primary'"
            >
              <component
                :is="stat.icon"
                class="h-4 w-4 sm:h-5 sm:w-5"
              />
            </div>
            <p class="text-xl sm:text-2xl font-medium text-black">
              {{ stat.value }}
            </p>
          </div>
          <p class="mt-2 text-xs font-medium text-[#737373]">
            {{ stat.title }}
          </p>
        </div>
        <!-- 背景装饰 -->
      </Card>
    </div>

    <!-- Filters -->
    <StudentFilters class="mb-5"
      v-model:search-query="searchQuery"
      v-model:selected-class="className"
      :class-options="classOptions"
      @update:search-query="setSearchQuery"
      @update:selected-class="setClassFilter"
    />

    <!-- Data Container -->
    <DataContainer
      :loading="isPending"
      :error="error"
      :has-data="filteredStudents.length > 0"
      empty-text="未找到匹配的学生"
      @retry="refetch"
    >
      <!-- Students list -->
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        <div
          v-for="student in filteredStudents"
          :key="student.student_id"
          class="space-y-2"
        >
          <StudentCard
            :student="student"
            :quick-score-options="quickScoreOptions"
            :is-updating="isUpdating"
            :updating-student-id="updatingStudentId || undefined"
            @quick-score="handleQuickScore"
            @open-score-dialog="openScoreDialog"
          />
          <Button
            variant="outline"
            size="sm"
            class="w-full"
            data-testid="expand-subjects-btn"
            @click="toggleSubjects(student.student_id)"
          >
            科目分数
            <ChevronUp
              v-if="expandedStudentId === student.student_id"
              class="ml-1 h-4 w-4"
            />
            <ChevronDown
              v-else
              class="ml-1 h-4 w-4"
            />
          </Button>
          <!-- 展开区：科目分数列表 -->
          <div
            v-if="expandedStudentId === student.student_id"
            class="rounded-lg border border-[#e5e5e5] bg-[#fafafa] p-3"
            data-testid="subject-scores-panel"
          >
            <p
              v-if="isSubjectsPending"
              class="text-sm text-[#737373]"
            >
              加载中...
            </p>
            <p
              v-else-if="!subjectScores || subjectScores.length === 0"
              class="text-sm text-[#737373]"
            >
              暂无科目分数记录
            </p>
            <div v-else class="space-y-2">
              <div
                v-for="s in subjectScores"
                :key="s.subject_id"
                class="flex items-center justify-between text-sm"
                data-testid="subject-score-item"
              >
                <span class="font-medium text-black">{{ s.subject_name }}</span>
                <span class="text-black">{{ s.score }} 分</span>
                <span class="text-xs text-[#a3a3a3]">{{ s.teacher_name }}</span>
              </div>
              <Button
                variant="outline"
                size="sm"
                class="w-full"
                data-testid="open-subject-score-dialog-btn"
                @click="openSubjectScoreDialog(student)"
              >
                调整科目分数
              </Button>
            </div>
          </div>
        </div>
      </div>

      <!-- 分页（搜索模式下显示匹配数量） -->
      <div
        v-if="isSearching"
        class="mt-4 text-center text-sm text-[#737373]"
      >
        找到 {{ filteredStudents.length }} 名匹配的学生
      </div>
      <div
        v-else-if="totalPages > 1"
        class="flex items-center justify-center gap-2 mt-4"
        data-testid="students-pagination"
      >
        <Button
          variant="outline"
          size="sm"
          :disabled="page <= 1"
          data-testid="students-prev-page"
          @click="page--"
        >
          <ChevronLeft class="h-4 w-4" />
        </Button>
        <span class="text-sm text-[#737373]">
          {{ page }} / {{ totalPages }}（共 {{ totalStudents }} 人）
        </span>
        <Button
          variant="outline"
          size="sm"
          :disabled="page >= totalPages"
          data-testid="students-next-page"
          @click="page++"
        >
          <ChevronRight class="h-4 w-4" />
        </Button>
      </div>
    </DataContainer>

    <!-- Score Dialog -->
    <ScoreDialog
      v-model:open="showScoreDialog"
      :student="selectedStudent"
      :is-loading="isUpdating"
      :default-score="defaultScore"
      :default-reason="defaultReason"
      @submit="handleUpdateScore"
    />

    <!-- 科目分数调整对话框（下拉选科目 + 加减分） -->
    <Dialog
      v-model:open="showSubjectScoreDialog"
      :title="scoreStudent ? `调整 ${scoreStudent.name} 的科目分数` : '调整科目分数'"
    >
      <div class="space-y-4">
        <div class="space-y-2">
          <Label for="subjectScoreSelect">科目</Label>
          <Select
            id="subjectScoreSelect"
            v-model="scoreSubjectId"
            :options="scoreSubjectOptions"
            placeholder="选择科目"
            data-testid="subject-score-select"
          />
        </div>
        <div class="space-y-2">
          <Label for="subjectScoreChange">分数变化</Label>
          <Input
            id="subjectScoreChange"
            v-model.number="subjectScoreChange"
            type="number"
            placeholder="输入分数（正数或负数）"
          />
        </div>
        <div class="space-y-2">
          <Label for="subjectScoreReason">原因</Label>
          <Input
            id="subjectScoreReason"
            v-model="subjectScoreReason"
            placeholder="输入分数变化原因"
          />
        </div>
      </div>
      <template #footer>
        <Button
          variant="outline"
          @click="showSubjectScoreDialog = false"
        >
          取消
        </Button>
        <Button
          :loading="isUpdatingSubjectScore"
          :disabled="scoreSubjectId === ''"
          data-testid="confirm-subject-score-btn"
          @click="handleUpdateSubjectScore"
        >
          更新分数
        </Button>
      </template>
    </Dialog>
  </div>
</template>
