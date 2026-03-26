<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useQueryClient } from '@tanstack/vue-query'
import { useStudents, useScoreUpdate } from '@/composables'
import { Card, Button, Badge, Dialog, Input, Label, DataContainer, SearchableSelect } from '@/components/ui'
import { Search, MessageCircle, AlertTriangle, UserX, Plus, Minus } from 'lucide-vue-next'
import { Toast } from '@/components/ui'
import type { Student } from '@/types'

// === 使用 Vue Query ===
const queryClient = useQueryClient()
const { data: studentsData, isPending, error, refetch } = useStudents()
const { mutateAsync: updateScore, isPending: isUpdatingScore } = useScoreUpdate()

// === 本地响应式状态 ===
const students = ref<Student[]>([])

// 同步 Vue Query 数据到本地
watch(() => studentsData.value, (newData) => {
  if (newData) {
    students.value = [...newData]
  }
}, { immediate: true, deep: true })

// === 搜索和筛选 ===
const searchQuery = ref('')
const selectedClass = ref<string>('')
const selectedStudent = ref<Student | null>(null)
const showScoreDialog = ref(false)
const scoreChange = ref(0)
const scoreReason = ref('')

const showToast = ref(false)
const toastMessage = ref('')
const toastVariant = ref<'default' | 'success' | 'error'>('default')

// 快速分数选项 (Indigo 单色系设计)
const quickScoreOptions = [
  { label: '课堂提问', score: 2, icon: MessageCircle },
  { label: '违反纪律', score: -2, icon: AlertTriangle },
  { label: '旷课', score: -5, icon: UserX },
]

// 按班级分组的学生
const studentsByClass = computed(() => {
  if (!students.value.length) return {}
  
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

// 班级列表
const classList = computed(() => {
  const list = Object.entries(studentsByClass.value).map(([name, students]) => ({
    name,
    count: students.length,
  }))
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

// 默认选中第一个班级
watch(classList, (list) => {
  if (list.length > 0 && !selectedClass.value) {
    selectedClass.value = list[0].name
  }
}, { immediate: true })

// 过滤后的学生列表
const filteredStudents = computed(() => {
  if (!students.value.length) return []
  
  let result = [...students.value]
  
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

// === 事件处理 ===
const openScoreDialog = (student: Student, defaultScore: number = 0, defaultReason: string = '') => {
  selectedStudent.value = student
  scoreChange.value = defaultScore || 10
  scoreReason.value = defaultReason
  showScoreDialog.value = true
}

// 处理快速分数调整
const handleQuickScore = async (student: Student, score: number, reason: string) => {
  try {
    const result = await updateScore({
      studentId: student.student_id,
      data: {
        score_change: score,
        reason: reason,
      },
    })
    
    // 更新 Vue Query 缓存
    const currentData = queryClient.getQueryData<Student[]>(['students'])
    if (currentData) {
      const newData = currentData.map((s) =>
        s.student_id === student.student_id
          ? { ...s, score: result.score }
          : s
      )
      queryClient.setQueryData(['students'], newData)
    }
    
    // 同步更新本地数据（确保 UI 立即响应）
    const index = students.value.findIndex(s => s.student_id === student.student_id)
    if (index !== -1) {
      students.value[index] = { ...students.value[index], score: result.score }
    }
    
    toastMessage.value = `${student.name} ${score > 0 ? '+' : ''}${score}分`
    toastVariant.value = 'success'
    showToast.value = true
  } catch (err: any) {
    toastMessage.value = err.message || '调整分数失败'
    toastVariant.value = 'error'
    showToast.value = true
  }
}

// 处理自定义分数更新
const handleUpdateScore = async () => {
  if (!selectedStudent.value) return

  try {
    const result = await updateScore({
      studentId: selectedStudent.value.student_id,
      data: {
        score_change: scoreChange.value,
        reason: scoreReason.value,
      },
    })
    
    // 更新 Vue Query 缓存
    const currentData = queryClient.getQueryData<Student[]>(['students'])
    if (currentData) {
      const newData = currentData.map((s) =>
        s.student_id === selectedStudent.value!.student_id
          ? { ...s, score: result.score }
          : s
      )
      queryClient.setQueryData(['students'], newData)
    }
    
    // 同步更新本地数据（确保 UI 立即响应）
    const index = students.value.findIndex(s => s.student_id === selectedStudent.value!.student_id)
    if (index !== -1) {
      students.value[index] = { ...students.value[index], score: result.score }
    }

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
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-white">我的学生</h1>
      <p class="text-white/60">查看和管理学生分数</p>
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
          placeholder="搜索学生..."
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
      <!-- Students list -->
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        <Card
          v-for="student in filteredStudents"
          :key="student.student_id"
          class="border-white/10 bg-white/[0.02] p-4 hover:bg-white/[0.04] transition-colors"
          :class="student.checkin_status === 'checked_in' ? 'border-green-500/30' : ''"
        >
          <!-- 学生信息 -->
          <div class="flex items-start justify-between mb-3">
            <div class="flex items-center gap-3">
              <div class="flex h-10 w-10 items-center justify-center rounded-full bg-primary/20">
                <span class="text-sm font-medium text-primary">
                  {{ student.name.charAt(0).toUpperCase() }}
                </span>
              </div>
              <div>
                <p class="font-medium text-white">{{ student.name }}</p>
                <p class="text-xs text-white/60">{{ student.student_id }}</p>
                <p class="text-xs text-white/40">{{ student.class_name }}</p>
              </div>
            </div>
            <Badge :variant="student.checkin_status === 'checked_in' ? 'success' : 'secondary'" class="text-xs">
              {{ student.checkin_status === 'checked_in' ? '已签到' : '未签到' }}
            </Badge>
          </div>
          
          <!-- 分数显示 -->
          <div class="mb-3">
            <p class="text-xs text-white/40 mb-1">当前分数</p>
            <p class="text-xl font-bold text-primary">{{ student.score }}</p>
          </div>
          
          <!-- 快速操作按钮 (使用设计体系 Grafana 柔和配色) -->
          <div class="grid grid-cols-3 gap-2">
            <button
              v-for="option in quickScoreOptions"
              :key="option.label"
              class="group relative flex flex-col items-center gap-1 rounded-lg py-2.5 px-1 text-xs transition-all duration-200 disabled:opacity-50"
              :class="[
                option.score > 0 
                  ? 'bg-success-soft-muted text-success-soft hover:bg-success-soft/25' 
                  : 'bg-error-soft-muted text-error-soft hover:bg-error-soft/25'
              ]"
              :disabled="isUpdatingScore"
              @click="handleQuickScore(student, option.score, option.label)"
            >
              <component :is="option.icon" class="h-4 w-4 opacity-80 group-hover:opacity-100" />
              <span class="font-medium">{{ option.label }}</span>
              <span class="text-[10px] opacity-70">
                {{ option.score > 0 ? '+' : '' }}{{ option.score }}
              </span>
              <!-- 光晕效果 -->
              <div 
                class="absolute inset-0 rounded-lg opacity-0 transition-opacity duration-200 group-hover:opacity-100 pointer-events-none"
                :class="option.score > 0 ? 'shadow-[0_0_12px_rgba(115,191,105,0.25)]' : 'shadow-[0_0_12px_rgba(224,47,68,0.25)]'"
              />
            </button>
          </div>
          
          <!-- 自定义分数按钮 (使用设计体系 Grafana 柔和配色) -->
          <div class="mt-3 flex gap-2">
            <button
              class="ch-button ch-button--sm ch-button--success-soft flex-1"
              @click="openScoreDialog(student, 10, '加分')"
            >
              <Plus class="h-3.5 w-3.5" />
              加分
            </button>
            <button
              class="ch-button ch-button--sm ch-button--error-soft flex-1"
              @click="openScoreDialog(student, -10, '扣分')"
            >
              <Minus class="h-3.5 w-3.5" />
              扣分
            </button>
          </div>
        </Card>
      </div>
    </DataContainer>

    <!-- Score Dialog -->
    <Dialog v-model:open="showScoreDialog" :title="selectedStudent ? `调整 ${selectedStudent.name} 的分数` : '调整分数'">
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

    <!-- Toast -->
    <Toast v-model:show="showToast" :message="toastMessage" :variant="toastVariant" />
  </div>
</template>
