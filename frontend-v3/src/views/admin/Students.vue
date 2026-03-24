<script setup lang="ts">
import { ref, computed } from 'vue'
import { useStudents, useScoreUpdate, useStudentCreate } from '@/composables'

import { Card, Button, Badge, Dialog, Input, Label, DataContainer, SearchableSelect } from '@/components/ui'
import { Search, Plus, Minus } from 'lucide-vue-next'
import { Toast } from '@/components/ui'
import type { Student } from '@/types'

const { data: students, isPending, error, refetch } = useStudents()

const { mutateAsync: updateScore, isPending: isUpdatingScore } = useScoreUpdate()
const { mutateAsync: createStudent, isPending: isCreating } = useStudentCreate()

const searchQuery = ref('')
const selectedClass = ref<string>('')
const selectedStudent = ref<Student | null>(null)
const showScoreDialog = ref(false)
const scoreChange = ref(0)
const scoreReason = ref('')

const showToast = ref(false)
const toastMessage = ref('')
const toastVariant = ref<'default' | 'success' | 'error'>('default')

// 添加学生弹窗
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

// 按班级分组的学生
const studentsByClass = computed(() => {
  if (!students.value) return {}
  
  const grouped: Record<string, Student[]> = {}
  students.value.forEach(student => {
    const className = student.class_name || '未分班'
    if (!grouped[className]) {
      grouped[className] = []
    }
    grouped[className].push(student)
  })
  return grouped
})

// 班级列表（包含学生数量）
const classList = computed(() => {
  const list = Object.entries(studentsByClass.value).map(([name, students]) => ({
    name,
    count: students.length,
  }))
  // 按班级名称排序
  return list.sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'))
})

// 班级下拉选项
const classOptions = computed(() => [
  { value: '', label: '全部班级' },
  ...classList.value.map(c => ({ 
    value: c.name, 
    label: `${c.name} (${c.count}人)` 
  }))
])

// 过滤后的学生列表
const filteredStudents = computed(() => {
  if (!students.value) return []
  
  let result = students.value
  
  // 按班级筛选
  if (selectedClass.value) {
    result = result.filter(s => s.class_name === selectedClass.value)
  }
  
  // 按搜索词筛选
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(
      (s) =>
        s.name.toLowerCase().includes(query) ||
        s.student_id.toLowerCase().includes(query) ||
        s.class_name.toLowerCase().includes(query)
    )
  }
  
  return result
})

const openScoreDialog = (student: Student, isAdd: boolean) => {
  selectedStudent.value = student
  scoreChange.value = isAdd ? 10 : -10
  scoreReason.value = ''
  showScoreDialog.value = true
}

const handleUpdateScore = async () => {
  if (!selectedStudent.value) return

  try {
    await updateScore({
      id: selectedStudent.value.id,
      data: {
        score_change: scoreChange.value,
        reason: scoreReason.value,
      },
    })

    toastMessage.value = `${selectedStudent.value.name} 的分数已更新`
    toastVariant.value = 'success'
    showToast.value = true
    showScoreDialog.value = false
  } catch (err: any) {
    toastMessage.value = err.message || '更新分数失败'
    toastVariant.value = 'error'
    showToast.value = true
  }
}

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
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center">
      <!-- Class Filter -->
      <div class="w-full sm:w-64">
        <SearchableSelect
          v-model="selectedClass"
          :options="classOptions"
          placeholder="选择班级筛选..."
          search-placeholder="搜索班级..."
        />
      </div>

      <!-- Search -->
      <div class="relative flex-1">
        <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/50" />
        <Input
          v-model="searchQuery"
          placeholder="搜索姓名、学号或班级..."
          class="pl-10"
        />
      </div>
    </div>

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
                  <Badge :variant="student.status === 'active' ? 'success' : 'secondary'">
                    {{ student.status === 'active' ? '活跃' : '非活跃' }}
                  </Badge>
                </td>
                <td class="px-4 py-3">
                  <div class="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      @click="openScoreDialog(student, true)"
                    >
                      <Plus class="h-3 w-3" />
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      @click="openScoreDialog(student, false)"
                    >
                      <Minus class="h-3 w-3" />
                    </Button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>
    </DataContainer>

    <!-- Score Dialog -->
    <Dialog v-model:open="showScoreDialog" title="更新分数">
      <div class="space-y-4">
        <p v-if="selectedStudent" class="text-white/60">
          更新 <span class="font-medium text-white">{{ selectedStudent.name }}</span> 的分数
        </p>
        <div class="space-y-2">
          <Label for="scoreChange">分数变化</Label>
          <Input
            id="scoreChange"
            v-model.number="scoreChange"
            type="number"
            placeholder="输入分数（正数或负数）"
          />
        </div>
        <div class="space-y-2">
          <Label for="reason">原因</Label>
          <Input
            id="reason"
            v-model="scoreReason"
            placeholder="输入分数变化原因"
          />
        </div>
      </div>
      <template #footer>
        <Button variant="outline" @click="showScoreDialog = false">取消</Button>
        <Button
          :loading="isUpdatingScore"
          @click="handleUpdateScore"
        >
          更新分数
        </Button>
      </template>
    </Dialog>

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
