<script setup lang="ts">
import { ref, watch } from 'vue'
import { useStudents, useStudentCreate, useToast } from '@/composables'
import { StudentFilters, useStudentFilters } from '@/features/students'
import { Card, Button, Badge, Dialog, Input, Label, DataContainer } from '@/components/ui'
import { Plus } from 'lucide-vue-next'
import { getErrorMessage } from '@/lib/error'

/**
 * 管理员学生管理页面 - FE-006 重构后
 *
 * 使用 Feature-based 架构，使用共享的 StudentFilters 组件
 */

// 统一的 Indigo 卡片样式
const getCardStyle = () => ({
  backgroundColor: 'var(--card-indigo-bg)',
  borderColor: 'var(--card-indigo-border)',
  '--tw-shadow-color': 'var(--card-indigo-shadow)',
})

const getCardIconStyle = () => ({
  backgroundColor: 'var(--card-indigo-icon-bg)',
  color: 'var(--card-indigo-icon-text)',
})

const getCardGlowStyle = () => ({
  backgroundColor: 'var(--card-indigo-glow)',
})

// === 数据获取 ===
const { data: students, isPending, error, refetch } = useStudents()
const { mutateAsync: createStudent, isPending: isCreating } = useStudentCreate()

// === Feature composables ===
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

// === Toast 状态 (队列模式) ===
const { success: showSuccessToast, error: showErrorToast } = useToast()

// === 添加学生对话框 ===
const showAddDialog = ref(false)
const newStudent = ref({
  student_id: '',
  name: '',
  class_name: '',
})
const addFormErrors = ref({
  student_id: '',
  name: '',
  class_name: '',
})

// 打开添加学生弹窗
const openAddDialog = () => {
  newStudent.value = {
    student_id: '',
    name: '',
    class_name: '',
  }
  addFormErrors.value = {
    student_id: '',
    name: '',
    class_name: '',
  }
  showAddDialog.value = true
}

// 验证添加学生表单
const validateAddForm = () => {
  addFormErrors.value = {
    student_id: '',
    name: '',
    class_name: '',
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

  if (!newStudent.value.class_name.trim()) {
    addFormErrors.value.class_name = '请输入班级'
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
      class_name: newStudent.value.class_name.trim(),
    })

    showSuccessToast(`学生 ${newStudent.value.name} 添加成功`)
    showAddDialog.value = false
  } catch (err: unknown) {
    showErrorToast(getErrorMessage(err) || '添加学生失败')
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
      <Button @click="openAddDialog">
        <Plus class="mr-2 h-4 w-4" />
        添加学生
      </Button>
    </div>

    <!-- Filters -->
    <StudentFilters
      v-model:search-query="filters.searchQuery"
      v-model:selected-class="filters.className"
      :class-options="classOptions"
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
          :key="student.id"
          class="relative overflow-hidden p-4"
          :style="getCardStyle()"
        >
          <!-- 背景光晕效果 -->
          <div
            class="absolute -right-4 -bottom-4 h-20 w-20 rounded-full blur-2xl opacity-30"
            :style="getCardGlowStyle()"
          />

          <div class="relative z-10 flex items-start justify-between">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <div
                  class="flex h-8 w-8 items-center justify-center rounded-lg"
                  :style="getCardIconStyle()"
                >
                  <span
                    class="text-sm font-medium"
                    :style="{ color: 'var(--card-indigo-icon-text)' }"
                  >
                    {{ student.name.charAt(0) }}
                  </span>
                </div>
                <span class="font-medium text-black truncate">{{ student.name }}</span>
                <Badge
                  :variant="student.is_account_enabled ? 'success' : 'secondary'"
                  class="text-xs flex-shrink-0"
                >
                  {{ student.is_account_enabled ? '启用' : '禁用' }}
                </Badge>
              </div>
              <p class="text-sm text-[var(--color-text-tertiary)] mt-1">{{ student.student_id }}</p>
              <p class="text-sm text-[var(--color-text-muted)] mt-0.5 truncate">{{ student.class_name }}</p>
            </div>
            <div class="text-right flex-shrink-0 ml-4">
              <span class="text-xl font-medium text-[var(--color-primary)]">{{ student.score }}</span>
              <p class="text-xs text-[var(--color-text-muted)]">分</p>
            </div>
          </div>
        </Card>
      </div>

      <!-- Desktop: Table -->
      <Card class="hidden lg:block overflow-hidden border-[var(--color-border)]">
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="border-b border-[var(--color-divider)] bg-[var(--color-background-card)]">
                <th class="px-4 py-3 text-left text-sm font-medium text-[var(--color-text-muted)]">
                  学号
                </th>
                <th class="px-4 py-3 text-left text-sm font-medium text-[var(--color-text-muted)]">
                  姓名
                </th>
                <th class="px-4 py-3 text-left text-sm font-medium text-[var(--color-text-muted)]">
                  班级
                </th>
                <th class="px-4 py-3 text-left text-sm font-medium text-[var(--color-text-muted)]">
                  分数
                </th>
                <th class="px-4 py-3 text-left text-sm font-medium text-[var(--color-text-muted)]">
                  状态
                </th>
                <th class="px-4 py-3 text-left text-sm font-medium text-[var(--color-text-muted)]">
                  操作
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="student in filteredStudents"
                :key="student.id"
                class="border-b border-[var(--color-divider)] transition-colors hover:bg-[var(--color-background-hover)]"
              >
                <td class="px-4 py-3 text-sm text-[var(--color-text-tertiary)]">
                  {{ student.student_id }}
                </td>
                <td class="px-4 py-3 text-sm font-medium text-black">
                  {{ student.name }}
                </td>
                <td class="px-4 py-3 text-sm text-[var(--color-text-tertiary)]">
                  {{ student.class_name }}
                </td>
                <td class="px-4 py-3 text-sm font-medium text-[var(--color-primary)]">
                  {{ student.score }}
                </td>
                <td class="px-4 py-3">
                  <Badge :variant="student.is_account_enabled ? 'success' : 'secondary'">
                    {{ student.is_account_enabled ? '启用' : '禁用' }}
                  </Badge>
                </td>
                <td class="px-4 py-3">
                  <span class="text-[var(--color-text-muted)] text-sm">-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>
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
            :class="addFormErrors.student_id ? 'border-[var(--color-error)]' : ''"
          />
          <p
            v-if="addFormErrors.student_id"
            class="text-sm text-[var(--color-error)]"
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
            :class="addFormErrors.name ? 'border-[var(--color-error)]' : ''"
          />
          <p
            v-if="addFormErrors.name"
            class="text-sm text-[var(--color-error)]"
          >
            {{ addFormErrors.name }}
          </p>
        </div>
        <div class="space-y-2">
          <Label for="className">班级</Label>
          <Input
            id="className"
            v-model="newStudent.class_name"
            placeholder="输入班级名称"
            :class="addFormErrors.class_name ? 'border-[var(--color-error)]' : ''"
          />
          <p
            v-if="addFormErrors.class_name"
            class="text-sm text-[var(--color-error)]"
          >
            {{ addFormErrors.class_name }}
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
  </div>
</template>
