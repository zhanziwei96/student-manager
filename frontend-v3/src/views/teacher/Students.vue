<script setup lang="ts">
import { ref, watch } from 'vue'
import { useStudents, useToast } from '@/composables'
import { StudentCard, ScoreDialog, StudentFilters, useStudentScore, useStudentFilters } from '@/features/students'
import { DataContainer } from '@/components/ui'
import { Toast } from '@/components/ui'
import type { Student } from '@/types'
import { getErrorMessage } from '@/lib/error'

/**
 * 教师学生管理页面 - FE-006 重构后
 * 
 * 使用 Feature-based 架构：
 * - 使用 features/students 的组件和 composables
 * - 视图层只负责页面布局和状态组合
 * - 业务逻辑下沉到 Feature 层
 */

// === 数据获取 ===
const { data: students, isPending, error, refetch } = useStudents()

// === Feature composables ===
const { updateScore, isUpdating, error: scoreError, updatingStudentId } = useStudentScore()
const { 
  filters, 
  classOptions, 
  filteredStudents, 
  setSearchQuery, 
  setClassFilter,
  selectFirstClass,
} = useStudentFilters(students)

// 默认选中第一个班级
watch(() => students.value, (newData) => {
  if (newData && newData.length > 0) {
    selectFirstClass()
  }
}, { immediate: true })

// === 分数对话框状态 ===
const selectedStudent = ref<Student | null>(null)
const showScoreDialog = ref(false)
const defaultScore = ref(0)
const defaultReason = ref('')

// === Toast 状态 (REVIEW-P1: 使用全局 useToast composable) ===
const { show, message: toastMessage, variant: toastVariant, success: showSuccessToast, error: showErrorToast } = useToast()

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
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-white">我的学生</h1>
      <p class="text-white/60">查看和管理学生分数</p>
    </div>

    <!-- Filters -->
    <StudentFilters
      v-model:search-query="filters.searchQuery"
      v-model:selected-class="filters.className"
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
        <StudentCard
          v-for="student in filteredStudents"
          :key="student.student_id"
          :student="student"
          :quick-score-options="quickScoreOptions"
          :is-updating="isUpdating"
          :updating-student-id="updatingStudentId || undefined"
          @quick-score="handleQuickScore"
          @open-score-dialog="openScoreDialog"
        />
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

    <!-- Toast -->
    <Toast v-model:show="show" :message="toastMessage" :variant="toastVariant" />
  </div>
</template>
