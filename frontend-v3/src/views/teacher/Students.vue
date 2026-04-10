<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useStudents, useToast } from '@/composables'
import { StudentCard, ScoreDialog, StudentFilters, useStudentScore, useStudentFilters } from '@/features/students'
import { DataContainer, Card } from '@/components/ui'
import type { Student } from '@/types'
import { getErrorMessage } from '@/lib/error'
import { Users, GraduationCap, Search } from 'lucide-vue-next'

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


// 统计信息
const stats = computed(() => {
  const total = filteredStudents.value.length
  const checkedIn = filteredStudents.value.filter(s => s.checkin_status === 'checked_in').length
  const avgScore = total > 0
    ? Math.round(filteredStudents.value.reduce((sum, s) => sum + s.score, 0) / total)
    : 0

  return [
    { title: '学生总数', value: total, icon: Users },
    { title: '已签到', value: checkedIn, icon: GraduationCap },
    { title: '平均分数', value: avgScore, icon: Search },
  ]
})

// === Feature composables ===
const { updateScore, isUpdating, updatingStudentId } = useStudentScore()
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

// === Toast 状态 (队列模式) ===
const { success: showSuccessToast, error: showErrorToast } = useToast()

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
    <div class="mb-5">
      <h1 class="text-2xl font-medium text-black">
        我的学生
      </h1>
      <p class="text-[#737373]">
        查看和管理学生分数
      </p>
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
  </div>
</template>
