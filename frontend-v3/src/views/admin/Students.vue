<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { useStudentCreate, useToast } from '@/composables'
import { StudentFilters, usePaginatedStudents } from '@/features/students'
import { Card, Button, Badge, Dialog, Input, Label, Checkbox, Select, DataContainer } from '@/components/ui'
import { Plus, Archive, ChevronLeft, ChevronRight, ChevronDown, ChevronUp, Loader2 } from 'lucide-vue-next'
import { studentsApi } from '@/api'
import type { StudentSubjectScore } from '@/api/students'
import { classesApi } from '@/api/classes'
import { cohortsApi } from '@/api/cohorts'
import type { Student, StudentStatus } from '@/types'
import type { ClassOption } from '@/features/students/types'
import { getErrorMessage } from '@/lib/error'

// 学籍状态展示映射（与后端 Student.status 一致）
const STUDENT_STATUS_LABEL: Record<StudentStatus, string> = {
  active: '在读',
  suspended: '休学',
  withdrawn: '退学',
  graduated: '毕业',
}
const STUDENT_STATUS_BADGE: Record<StudentStatus, 'success' | 'warning' | 'error' | 'secondary'> = {
  active: 'success',
  suspended: 'warning',
  withdrawn: 'error',
  graduated: 'secondary',
}
const STUDENT_STATUS_OPTIONS: { value: StudentStatus; label: string }[] = [
  { value: 'active', label: '在读' },
  { value: 'suspended', label: '休学' },
  { value: 'withdrawn', label: '退学' },
  { value: 'graduated', label: '毕业' },
]

/**
 * 管理员学生管理页面 - FE-006 重构后
 *
 * 使用 Feature-based 架构，使用共享的 StudentFilters 组件
 * 学生列表服务端分页（usePaginatedStudents），搜索时前端过滤
 */


// === 届 → 班级联动筛选 ===
const cohortFilter = ref('')
const { data: cohortsData } = useQuery({
  queryKey: ['cohorts'],
  queryFn: () => cohortsApi.list(),
})
const cohorts = computed(() => cohortsData.value ?? [])
const cohortOptions = computed<ClassOption[]>(() => [
  { value: '', label: '全部届', count: 0 },
  ...cohorts.value.map((c) => ({ value: c.year, label: c.label, count: 0 })),
])

// === 数据获取（服务端分页，班级选项按届过滤） ===
const {
  page,
  searchQuery,
  className,
  isSearching,
  classOptions,
  filteredStudents,
  total,
  totalPages,
  isPending,
  error,
  refetch,
  setSearchQuery,
  setClassFilter,
} = usePaginatedStudents(50, cohortFilter)
const { mutateAsync: createStudent, isPending: isCreating } = useStudentCreate()

// === Toast 状态 (队列模式) ===
const { success: showSuccessToast, error: showErrorToast } = useToast()

// === 按班级禁用（学期归档，支持多选班级） ===
const queryClient = useQueryClient()
const showDisableDialog = ref(false)
const disableClassNames = ref<string[]>([])
const isDisabling = ref(false)

// 可选班级（排除“全部班级”占位项）
const disableClassOptions = computed(() =>
  classOptions.value.filter((o) => o.value !== '')
)

const openDisableDialog = () => {
  disableClassNames.value = []
  showDisableDialog.value = true
}

// 勾选/取消勾选班级
const toggleDisableClass = (className: string, checked: boolean) => {
  if (checked) {
    disableClassNames.value = [...disableClassNames.value, className]
  } else {
    disableClassNames.value = disableClassNames.value.filter((c) => c !== className)
  }
}

const handleDisableByClass = async () => {
  if (disableClassNames.value.length === 0) return

  try {
    isDisabling.value = true
    const result = await studentsApi.disableByClass(disableClassNames.value)
    // 刷新学生列表与班级列表（禁用后班级从列表消失）
    await queryClient.invalidateQueries({ queryKey: ['students'] })
    await queryClient.invalidateQueries({ queryKey: ['classes'] })
    showDisableDialog.value = false
    showSuccessToast(`已禁用 ${result.disabled_count} 名学生`)
  } catch (err: unknown) {
    showErrorToast(getErrorMessage(err) || '按班级禁用失败')
  } finally {
    isDisabling.value = false
  }
}

// === 科目分数展开行 ===
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
const scoreChange = ref(0)
const scoreReason = ref('')
const isUpdatingSubjectScore = ref(false)

// 弹窗科目下拉选项（来自该学生已展开的科目分数）
const scoreSubjectOptions = computed(() =>
  (subjectScores.value ?? []).map((s: StudentSubjectScore) => ({
    value: s.subject_id,
    label: `${s.subject_name}（当前 ${s.score} 分）`,
  }))
)

// 从展开行打开科目分数调整弹窗
const openSubjectScoreDialog = (student: Student) => {
  scoreStudent.value = student
  scoreSubjectId.value = subjectScores.value?.[0]?.subject_id ?? ''
  scoreChange.value = 0
  scoreReason.value = ''
  showSubjectScoreDialog.value = true
}

const handleUpdateSubjectScore = async () => {
  if (!scoreStudent.value || scoreSubjectId.value === '') return
  if (!scoreReason.value.trim()) {
    showErrorToast('请输入分数变化原因')
    return
  }

  try {
    isUpdatingSubjectScore.value = true
    const studentId = scoreStudent.value.student_id
    await studentsApi.updateSubjectScore(studentId, Number(scoreSubjectId.value), scoreChange.value, scoreReason.value.trim())
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

// === 添加学生对话框（届 → 班级联动选择） ===
const showAddDialog = ref(false)
const newStudent = ref({
  student_id: '',
  name: '',
  class_id: '',
})
const addFormErrors = ref({
  student_id: '',
  name: '',
  class_id: '',
})
const addCohortYear = ref('')

const { data: addClassesData } = useQuery({
  queryKey: ['classes', addCohortYear],
  queryFn: () => classesApi.list(addCohortYear.value || undefined),
})
const addClassOptions = computed(() =>
  (addClassesData.value ?? []).map((c) => ({ value: c.id, label: c.display_name })),
)

// 打开添加学生弹窗
const openAddDialog = () => {
  newStudent.value = {
    student_id: '',
    name: '',
    class_id: '',
  }
  addFormErrors.value = {
    student_id: '',
    name: '',
    class_id: '',
  }
  addCohortYear.value = ''
  showAddDialog.value = true
}

// 验证添加学生表单
const validateAddForm = () => {
  addFormErrors.value = {
    student_id: '',
    name: '',
    class_id: '',
  }
  let isValid = true

  if (!newStudent.value.student_id.trim()) {
    addFormErrors.value.student_id = '请输入学号'
    isValid = false
  }

  if (!newStudent.value.name.trim()) {
    addFormErrors.value.name = '请输入姓名'
    isValid = false
  }

  if (!newStudent.value.class_id) {
    addFormErrors.value.class_id = '请选择班级'
    isValid = false
  }

  return isValid
}

// 处理添加学生
const handleAddStudent = async () => {
  if (!validateAddForm()) return

  const cls = (addClassesData.value ?? []).find((c) => c.id === Number(newStudent.value.class_id))

  try {
    await createStudent({
      student_id: newStudent.value.student_id.trim(),
      name: newStudent.value.name.trim(),
      class_name: cls?.name ?? '',
    })

    showSuccessToast(`学生 ${newStudent.value.name} 添加成功`)
    showAddDialog.value = false
  } catch (err: unknown) {
    showErrorToast(getErrorMessage(err) || '添加学生失败')
  }
}

// === 学籍状态切换 ===
const showStatusDialog = ref(false)
const statusStudent = ref<Student | null>(null)
const statusForm = ref<StudentStatus>('active')
const isUpdatingStatus = ref(false)

const openStatusDialog = (student: Student) => {
  statusStudent.value = student
  statusForm.value = (student.status ?? 'active') as StudentStatus
  showStatusDialog.value = true
}

const handleUpdateStatus = async () => {
  if (!statusStudent.value) return

  try {
    isUpdatingStatus.value = true
    await studentsApi.updateStatus(statusStudent.value.student_id, statusForm.value)
    await queryClient.invalidateQueries({ queryKey: ['students'] })
    showStatusDialog.value = false
    showSuccessToast(`${statusStudent.value.name} 的学籍状态已更新`)
  } catch (err: unknown) {
    showErrorToast(getErrorMessage(err) || '更新学籍状态失败')
  } finally {
    isUpdatingStatus.value = false
  }
}

// === 转班（届 → 班级联动选择目标班） ===
const showTransferDialog = ref(false)
const transferStudent = ref<Student | null>(null)
const transferCohortYear = ref('')
const transferClassId = ref<number | ''>('')
const transferError = ref('')
const isTransferring = ref(false)

const { data: transferClassesData } = useQuery({
  queryKey: ['classes', transferCohortYear],
  queryFn: () => classesApi.list(transferCohortYear.value || undefined),
  enabled: () => showTransferDialog.value,
})
const transferClassOptions = computed(() =>
  (transferClassesData.value ?? []).map((c) => ({ value: c.id, label: c.display_name })),
)

const openTransferDialog = (student: Student) => {
  transferStudent.value = student
  transferCohortYear.value = ''
  transferClassId.value = ''
  transferError.value = ''
  showTransferDialog.value = true
}

const handleTransfer = async () => {
  if (!transferStudent.value) return
  if (transferClassId.value === '') {
    transferError.value = '请选择目标班级'
    return
  }

  try {
    isTransferring.value = true
    await studentsApi.transferClass(transferStudent.value.student_id, Number(transferClassId.value))
    await queryClient.invalidateQueries({ queryKey: ['students'] })
    await queryClient.invalidateQueries({ queryKey: ['classes'] })
    showTransferDialog.value = false
    showSuccessToast(`${transferStudent.value.name} 已转班`)
  } catch (err: unknown) {
    showErrorToast(getErrorMessage(err) || '转班失败')
  } finally {
    isTransferring.value = false
  }
}
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-5">
      <div>
        <h1 class="text-2xl font-medium text-black">
          学生管理
        </h1>
        <p class="text-[#737373]">
          管理学生档案和分数
        </p>
      </div>
      <div class="flex gap-2">
        <Button
          variant="outline"
          data-testid="disable-by-class-btn"
          @click="openDisableDialog"
        >
          <Archive class="mr-2 h-4 w-4" />
          批量禁用毕业生账号
        </Button>
        <Button @click="openAddDialog">
          <Plus class="mr-2 h-4 w-4" />
          添加学生
        </Button>
      </div>
    </div>

    <!-- Filters -->
    <StudentFilters
      v-model:search-query="searchQuery"
      v-model:selected-class="className"
      v-model:selected-cohort="cohortFilter"
      :class-options="classOptions"
      :cohort-options="cohortOptions"
      class="mb-5"
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
      <!-- Mobile: Card List -->
      <div class="lg:hidden space-y-3">
        <Card
          v-for="student in filteredStudents"
          :key="student.student_id"
          class="relative overflow-hidden p-4"
          :class="'bg-white border-[#e5e5e5]'"
        >
          <!-- 背景光晕效果 -->

          <div class="relative z-10 flex items-start justify-between">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <div
                  class="flex h-8 w-8 items-center justify-center rounded-lg"
                  :class="'bg-primary/10 text-primary'"
                >
                  <span
                    class="text-sm font-medium"
                    :style="{ color: 'black' }"
                  >
                    {{ student.name.charAt(0) }}
                  </span>
                </div>
                <span class="font-medium text-black truncate">{{ student.name }}</span>
                <Badge
                  :variant="STUDENT_STATUS_BADGE[(student.status ?? 'active') as StudentStatus]"
                  class="text-xs flex-shrink-0"
                >
                  {{ STUDENT_STATUS_LABEL[(student.status ?? 'active') as StudentStatus] }}
                </Badge>
              </div>
              <p class="text-sm text-[#a3a3a3] mt-1">{{ student.student_id }}</p>
              <p class="text-sm text-[#737373] mt-0.5 truncate">{{ student.class_name }}</p>
            </div>
            <div class="text-right flex-shrink-0 ml-4">
              <span class="text-xl font-medium text-[black]">{{ student.score }}</span>
              <p class="text-xs text-[#737373]">分</p>
            </div>
          </div>
          <div class="relative z-10 mt-3">
            <div class="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                class="flex-1 hover:bg-[#fafafa]"
                @click="openTransferDialog(student)"
              >
                转班
              </Button>
              <Button
                variant="outline"
                size="sm"
                class="flex-1 hover:bg-[#fafafa]"
                @click="openStatusDialog(student)"
              >
                学籍
              </Button>
            </div>
            <Button
              variant="ghost"
              size="sm"
              class="w-full"
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
            <div
              v-if="expandedStudentId === student.student_id"
              class="mt-2 rounded-lg bg-[#fafafa] p-3"
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
                >
                  <span class="font-medium text-black">{{ s.subject_name }}</span>
                  <span class="text-black">{{ s.score }} 分</span>
                  <span class="text-xs text-[#a3a3a3]">{{ s.teacher_name }}</span>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  class="w-full"
                  @click="openSubjectScoreDialog(student)"
                >
                  调整科目分数
                </Button>
              </div>
            </div>
          </div>
        </Card>
      </div>

      <!-- Desktop: Table -->
      <Card class="hidden lg:block overflow-hidden border-[#e5e5e5]">
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="border-b border-[#e5e5e5] bg-[white]">
                <th class="px-4 py-3 text-left text-sm font-medium text-[#737373]">
                  学号
                </th>
                <th class="px-4 py-3 text-left text-sm font-medium text-[#737373]">
                  姓名
                </th>
                <th class="px-4 py-3 text-left text-sm font-medium text-[#737373]">
                  班级
                </th>
                <th class="px-4 py-3 text-left text-sm font-medium text-[#737373]">
                  分数
                </th>
                <th class="px-4 py-3 text-left text-sm font-medium text-[#737373]">
                  学籍
                </th>
                <th class="px-4 py-3 text-left text-sm font-medium text-[#737373]">
                  状态
                </th>
                <th class="px-4 py-3 text-left text-sm font-medium text-[#737373]">
                  操作
                </th>
              </tr>
            </thead>
            <tbody>
              <template
                v-for="student in filteredStudents"
                :key="student.student_id"
              >
                <tr class="border-b border-[#e5e5e5] transition-colors hover:bg-[#f5f5f5]">
                  <td class="px-4 py-3 text-sm text-[#a3a3a3]">
                    {{ student.student_id }}
                  </td>
                  <td class="px-4 py-3 text-sm font-medium text-black">
                    {{ student.name }}
                  </td>
                  <td class="px-4 py-3 text-sm text-[#a3a3a3]">
                    {{ student.class_name }}
                  </td>
                  <td class="px-4 py-3 text-sm font-medium text-[black]">
                    {{ student.score }}
                  </td>
                  <td class="px-4 py-3">
                    <Badge :variant="STUDENT_STATUS_BADGE[(student.status ?? 'active') as StudentStatus]">
                      {{ STUDENT_STATUS_LABEL[(student.status ?? 'active') as StudentStatus] }}
                    </Badge>
                  </td>
                  <td class="px-4 py-3">
                    <Badge :variant="student.is_account_enabled ? 'success' : 'secondary'">
                      {{ student.is_account_enabled ? '启用' : '禁用' }}
                    </Badge>
                  </td>
                  <td class="px-4 py-3">
                    <div class="flex gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        @click="openTransferDialog(student)"
                      >
                        转班
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        @click="openStatusDialog(student)"
                      >
                        学籍
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
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
                    </div>
                  </td>
                </tr>
                <!-- 展开行：科目分数列表 -->
                <tr
                  v-if="expandedStudentId === student.student_id"
                  class="border-b border-[#e5e5e5] bg-[#fafafa]"
                  data-testid="subject-scores-row"
                >
                  <td
                    colspan="7"
                    class="px-4 py-3"
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
                    <div v-else>
                      <div class="flex flex-wrap gap-2">
                        <div
                          v-for="s in subjectScores"
                          :key="s.subject_id"
                          class="flex items-center gap-2 rounded-lg border border-[#e5e5e5] bg-white px-3 py-2"
                          data-testid="subject-score-item"
                        >
                          <span class="text-sm font-medium text-black">{{ s.subject_name }}</span>
                          <span class="text-sm font-medium text-[black]">{{ s.score }} 分</span>
                          <span class="text-xs text-[#a3a3a3]">{{ s.teacher_name }}</span>
                        </div>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        class="mt-3"
                        data-testid="open-subject-score-dialog-btn"
                        @click="openSubjectScoreDialog(student)"
                      >
                        调整科目分数
                      </Button>
                    </div>
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>
      </Card>

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
          {{ page }} / {{ totalPages }}（共 {{ total }} 人）
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

    <!-- Add Student Dialog -->
    <Dialog
      v-model:open="showAddDialog"
      title="添加学生"
    >
      <div class="space-y-4">
        <div class="space-y-2">
          <Label for="studentId">学号</Label>
          <Input
            id="studentId"
            v-model="newStudent.student_id"
            placeholder="输入学号"
            :class="addFormErrors.student_id ? 'border-[#ef4444]' : ''"
          />
          <p
            v-if="addFormErrors.student_id"
            class="text-sm text-[#ef4444]"
          >
            {{ addFormErrors.student_id }}
          </p>
        </div>
        <div class="space-y-2">
          <Label for="studentName">姓名</Label>
          <Input
            id="studentName"
            v-model="newStudent.name"
            placeholder="输入姓名"
            :class="addFormErrors.name ? 'border-[#ef4444]' : ''"
          />
          <p
            v-if="addFormErrors.name"
            class="text-sm text-[#ef4444]"
          >
            {{ addFormErrors.name }}
          </p>
        </div>
        <div class="space-y-2">
          <Label for="addCohort">所属届</Label>
          <Select
            id="addCohort"
            v-model="addCohortYear"
            :options="cohortOptions.filter((o) => o.value !== '')"
            placeholder="选择届"
          />
        </div>
        <div class="space-y-2">
          <Label for="addClass">班级</Label>
          <Select
            id="addClass"
            v-model="newStudent.class_id"
            :options="addClassOptions"
            placeholder="选择班级"
            :class="addFormErrors.class_id ? 'border-[#ef4444]' : ''"
          />
          <p
            v-if="addFormErrors.class_id"
            class="text-sm text-[#ef4444]"
          >
            {{ addFormErrors.class_id }}
          </p>
        </div>
      </div>
      <template #footer>
        <Button
          variant="outline"
          @click="showAddDialog = false"
        >
          取消
        </Button>
        <Button
          :loading="isCreating"
          @click="handleAddStudent"
        >
          添加
        </Button>
      </template>
    </Dialog>
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
            v-model.number="scoreChange"
            type="number"
            placeholder="输入分数（正数或负数）"
          />
        </div>
        <div class="space-y-2">
          <Label for="subjectScoreReason">原因</Label>
          <Input
            id="subjectScoreReason"
            v-model="scoreReason"
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

    <!-- 批量禁用毕业生账号对话框（支持多选班级） -->
    <Dialog
      v-model:open="showDisableDialog"
      title="批量禁用毕业生账号"
      description="禁用后学生无法登录（适用于毕业/离校学生）"
    >
      <div class="space-y-4">
        <div class="space-y-2">
          <Label>选择班级（可多选）</Label>
          <div class="max-h-60 space-y-2 overflow-y-auto rounded-md border border-[#e5e5e5] p-3">
            <div
              v-for="cls in disableClassOptions"
              :key="cls.value"
              class="flex items-center gap-2"
            >
              <Checkbox
                :checked="disableClassNames.includes(String(cls.value))"
                @update:checked="(checked) => toggleDisableClass(String(cls.value), checked)"
              />
              <span class="text-sm">{{ cls.label }}</span>
            </div>
          </div>
        </div>
        <p
          v-if="disableClassNames.length > 0"
          class="text-sm text-[#ef4444]"
        >
          将禁用 {{ disableClassNames.length }} 个班级的所有学生账号，确定吗？
        </p>
      </div>
      <template #footer>
        <Button
          variant="outline"
          @click="showDisableDialog = false"
        >
          取消
        </Button>
        <Button
          variant="destructive"
          :disabled="disableClassNames.length === 0"
          :loading="isDisabling"
          data-testid="confirm-disable-btn"
          @click="handleDisableByClass"
        >
          确认禁用
        </Button>
      </template>
    </Dialog>

    <!-- 学籍状态切换对话框 -->
    <Dialog
      v-model:open="showStatusDialog"
      :title="statusStudent ? `调整 ${statusStudent.name} 的学籍状态` : '调整学籍状态'"
      description="休学/退学/毕业的学生将保留历史数据"
    >
      <div class="space-y-4">
        <div class="space-y-2">
          <Label for="studentStatus">学籍状态</Label>
          <Select
            id="studentStatus"
            v-model="statusForm"
            :options="STUDENT_STATUS_OPTIONS"
            data-testid="student-status-select"
          />
        </div>
      </div>
      <template #footer>
        <Button
          variant="outline"
          @click="showStatusDialog = false"
        >
          取消
        </Button>
        <Button
          :disabled="isUpdatingStatus"
          data-testid="confirm-status-btn"
          @click="handleUpdateStatus"
        >
          <Loader2
            v-if="isUpdatingStatus"
            class="mr-2 h-4 w-4 animate-spin"
          />
          保存
        </Button>
      </template>
    </Dialog>

    <!-- 转班对话框（届 → 班级联动） -->
    <Dialog
      v-model:open="showTransferDialog"
      :title="transferStudent ? `${transferStudent.name} 转班` : '转班'"
      :description="transferStudent ? `当前班级：${transferStudent.class_name}` : ''"
    >
      <div class="space-y-4">
        <div class="space-y-2">
          <Label for="transferCohort">目标届</Label>
          <Select
            id="transferCohort"
            v-model="transferCohortYear"
            :options="cohortOptions.filter((o) => o.value !== '')"
            placeholder="选择届"
          />
        </div>
        <div class="space-y-2">
          <Label for="transferClass">目标班级</Label>
          <Select
            id="transferClass"
            v-model="transferClassId"
            :options="transferClassOptions"
            placeholder="选择班级"
            data-testid="transfer-class-select"
          />
        </div>
        <p
          v-if="transferError"
          class="text-sm text-[#ef4444]"
        >
          {{ transferError }}
        </p>
      </div>
      <template #footer>
        <Button
          variant="outline"
          @click="showTransferDialog = false"
        >
          取消
        </Button>
        <Button
          :disabled="isTransferring"
          data-testid="confirm-transfer-btn"
          @click="handleTransfer"
        >
          <Loader2
            v-if="isTransferring"
            class="mr-2 h-4 w-4 animate-spin"
          />
          确认转班
        </Button>
      </template>
    </Dialog>
  </div>
</template>
