<script setup lang="ts">
import { ref, watch } from 'vue'
import { useStudents, useStudentCreate } from '@/composables'
import { StudentFilters, useStudentFilters } from '@/features/students'
import { Card, Button, Badge, Dialog, Input, Label, DataContainer } from '@/components/ui'
import { Plus } from 'lucide-vue-next'
import { Toast } from '@/components/ui'

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

// === Toast 状态 ===
const showToast = ref(false)
const toastMessage = ref('')
const toastVariant = ref<'default' | 'success' | 'error'>('default')

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

    toastMessage.value = `学生 ${newStudent.value.name} 添加成功`
    toastVariant.value = 'success'
    showToast.value = true
    showAddDialog.value = false
  } catch (err: any) {
    toastMessage.value = err.message || '添加学生失败'
    toastVariant.value = 'error'
    showToast.value = true
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold text-white">学生管理</h1>
        <p class="text-white/60">管理学生档案和分数</p>
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
      <!-- Students table -->
      <Card class="overflow-hidden border-white/10">
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="border-b border-white/10 bg-white/[0.02]">
                <th class="px-4 py-3 text-left text-sm font-medium text-white/60">学号</th>
                <th class="px-4 py-3 text-left text-sm font-medium text-white/60">姓名</th>
                <th class="px-4 py-3 text-left text-sm font-medium text-white/60">班级</th>
                <th class="px-4 py-3 text-left text-sm font-medium text-white/60">分数</th>
                <th class="px-4 py-3 text-left text-sm font-medium text-white/60">状态</th>
                <th class="px-4 py-3 text-left text-sm font-medium text-white/60">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="student in filteredStudents"
                :key="student.id"
                class="border-b border-white/5 transition-colors hover:bg-white/[0.02]"
              >
                <td class="px-4 py-3 text-sm text-white/60">{{ student.student_id }}</td>
                <td class="px-4 py-3 text-sm font-medium text-white">{{ student.name }}</td>
                <td class="px-4 py-3 text-sm text-white/60">{{ student.class_name }}</td>
                <td class="px-4 py-3 text-sm font-bold text-primary">{{ student.score }}</td>
                <td class="px-4 py-3">
                  <Badge :variant="student.is_account_enabled ? 'success' : 'secondary'">
                    {{ student.is_account_enabled ? '启用' : '禁用' }}
                  </Badge>
                </td>
                <td class="px-4 py-3">
                  <span class="text-white/40 text-sm">-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>
    </DataContainer>

    <!-- Add Student Dialog -->
    <Dialog v-model:open="showAddDialog" title="添加学生">
      <div class="space-y-4">
        <div class="space-y-2">
          <Label for="studentId">学号</Label>
          <Input
            id="studentId"
            v-model="newStudent.student_id"
            placeholder="输入学号"
            :class="addFormErrors.student_id ? 'border-red-500' : ''"
          />
          <p v-if="addFormErrors.student_id" class="text-sm text-red-500">{{ addFormErrors.student_id }}</p>
        </div>
        <div class="space-y-2">
          <Label for="studentName">姓名</Label>
          <Input
            id="studentName"
            v-model="newStudent.name"
            placeholder="输入姓名"
            :class="addFormErrors.name ? 'border-red-500' : ''"
          />
          <p v-if="addFormErrors.name" class="text-sm text-red-500">{{ addFormErrors.name }}</p>
        </div>
        <div class="space-y-2">
          <Label for="className">班级</Label>
          <Input
            id="className"
            v-model="newStudent.class_name"
            placeholder="输入班级名称"
            :class="addFormErrors.class_name ? 'border-red-500' : ''"
          />
          <p v-if="addFormErrors.class_name" class="text-sm text-red-500">{{ addFormErrors.class_name }}</p>
        </div>
      </div>
      <template #footer>
        <Button variant="outline" @click="showAddDialog = false">取消</Button>
        <Button
          :loading="isCreating"
          @click="handleAddStudent"
        >
          添加
        </Button>
      </template>
    </Dialog>

    <!-- Toast -->
    <Toast v-model:show="showToast" :message="toastMessage" :variant="toastVariant" />
  </div>
</template>
