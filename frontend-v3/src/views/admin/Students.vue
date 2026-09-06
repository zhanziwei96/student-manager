<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useQueryClient } from '@tanstack/vue-query'
import { useStudents, useStudentCreate, useToast } from '@/composables'
import { StudentFilters, useStudentFilters } from '@/features/students'
import { Card, Button, Badge, Dialog, Input, Label, Checkbox, DataContainer } from '@/components/ui'
import { Plus, Archive } from 'lucide-vue-next'
import { studentsApi } from '@/api'
import { getErrorMessage } from '@/lib/error'

/**
 * 管理员学生管理页面 - FE-006 重构后
 *
 * 使用 Feature-based 架构，使用共享的 StudentFilters 组件
 */


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
      <div class="flex gap-2">
        <Button
          variant="outline"
          data-testid="disable-by-class-btn"
          @click="openDisableDialog"
        >
          <Archive class="mr-2 h-4 w-4" />
          按班级禁用
        </Button>
        <Button @click="openAddDialog">
          <Plus class="mr-2 h-4 w-4" />
          添加学生
        </Button>
      </div>
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
                  :variant="student.is_account_enabled ? 'success' : 'secondary'"
                  class="text-xs flex-shrink-0"
                >
                  {{ student.is_account_enabled ? '启用' : '禁用' }}
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
                  状态
                </th>
                <th class="px-4 py-3 text-left text-sm font-medium text-[#737373]">
                  操作
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="student in filteredStudents"
                :key="student.student_id"
                class="border-b border-[#e5e5e5] transition-colors hover:bg-[#f5f5f5]"
              >
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
                  <Badge :variant="student.is_account_enabled ? 'success' : 'secondary'">
                    {{ student.is_account_enabled ? '启用' : '禁用' }}
                  </Badge>
                </td>
                <td class="px-4 py-3">
                  <span class="text-[#737373] text-sm">-</span>
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
          <Label for="className">班级</Label>
          <Input
            id="className"
            v-model="newStudent.class_name"
            placeholder="输入班级名称"
            :class="addFormErrors.class_name ? 'border-[#ef4444]' : ''"
          />
          <p
            v-if="addFormErrors.class_name"
            class="text-sm text-[#ef4444]"
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
    <!-- 按班级禁用对话框（学期归档，支持多选班级） -->
    <Dialog
      v-model:open="showDisableDialog"
      title="按班级禁用"
      description="禁用后所选班级学生无法登录，班级将从列表中消失，历史数据保留"
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
  </div>
</template>
