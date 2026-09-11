<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { useStudentCreate, useToast } from '@/composables'
import { StudentFilters, usePaginatedStudents } from '@/features/students'
import StudentImportDialog from '@/components/admin/StudentImportDialog.vue'
import { Card, Button, Badge, Dialog, Input, Label, Checkbox, Select, DataContainer } from '@/components/ui'
import { Plus, Archive, ChevronLeft, ChevronRight, Loader2, Upload } from 'lucide-vue-next'
import { studentsApi } from '@/api'
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
  classId,
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

// 批量导入
const showImportDialog = ref(false)
const handleImported = async () => {
  await queryClient.invalidateQueries({ queryKey: ['students'] })
  await queryClient.invalidateQueries({ queryKey: ['classes'] })  // 导入可能自动建班
  await queryClient.invalidateQueries({ queryKey: ['stats'] })
}

// === Toast 状态 (队列模式) ===
const { success: showSuccessToast, error: showErrorToast } = useToast()

// === 按班级禁用（学期归档，支持多选班级） ===
const queryClient = useQueryClient()
const showDisableDialog = ref(false)
const disableClassIds = ref<number[]>([])
const isDisabling = ref(false)

// 可选班级（排除“全部班级”占位项）
const disableClassOptions = computed(() =>
  classOptions.value.filter((o) => o.value !== '')
)

const openDisableDialog = () => {
  disableClassIds.value = []
  showDisableDialog.value = true
}

// 勾选/取消勾选班级
const toggleDisableClass = (classId: number, checked: boolean) => {
  if (checked) {
    disableClassIds.value = [...disableClassIds.value, classId]
  } else {
    disableClassIds.value = disableClassIds.value.filter((c) => c !== classId)
  }
}

const handleDisableByClass = async () => {
  if (disableClassIds.value.length === 0) return

  try {
    isDisabling.value = true
    const result = await studentsApi.disableByClass(disableClassIds.value)
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

  try {
    await createStudent({
      student_id: newStudent.value.student_id.trim(),
      name: newStudent.value.name.trim(),
      class_id: Number(newStudent.value.class_id),
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
          data-testid="import-students-btn"
          @click="showImportDialog = true"
        >
          <Upload class="mr-2 h-4 w-4" />
          批量导入
        </Button>
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

    <StudentImportDialog
      v-model:open="showImportDialog"
      @imported="handleImported"
    />

    <!-- Filters -->
    <StudentFilters
      v-model:search-query="searchQuery"
      v-model:selected-class="classId"
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
                :checked="disableClassIds.includes(Number(cls.value))"
                @update:checked="(checked) => toggleDisableClass(Number(cls.value), checked)"
              />
              <span class="text-sm">{{ cls.label }}</span>
            </div>
          </div>
        </div>
        <p
          v-if="disableClassIds.length > 0"
          class="text-sm text-[#ef4444]"
        >
          将禁用 {{ disableClassIds.length }} 个班级的所有学生账号，确定吗？
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
          :disabled="disableClassIds.length === 0"
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
