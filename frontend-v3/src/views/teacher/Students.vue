<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useStudents, useScoreUpdate } from '@/composables'
import { Card, Button, Badge, Dialog, Input, Label, DataContainer, SearchableSelect } from '@/components/ui'
import { Search, TrendingUp, TrendingDown, MessageCircle, AlertTriangle, UserX, Plus, Minus } from 'lucide-vue-next'
import { Toast } from '@/components/ui'
import type { Student } from '@/types'

const { data: students, isPending, error, refetch } = useStudents()
const { mutateAsync: updateScore, isPending: isUpdatingScore } = useScoreUpdate()

const searchQuery = ref('')
const selectedClass = ref<string>('')
const selectedStudent = ref<Student | null>(null)
const showScoreDialog = ref(false)
const scoreChange = ref(0)
const scoreReason = ref('')

const showToast = ref(false)
const toastMessage = ref('')
const toastVariant = ref<'default' | 'success' | 'error'>('default')

// 快速分数选项
const quickScoreOptions = [
  { label: '课堂提问', score: 2, icon: MessageCircle, color: 'text-green-400', bgColor: 'bg-green-500/10', borderColor: 'border-green-500/30' },
  { label: '违反纪律', score: -2, icon: AlertTriangle, color: 'text-orange-400', bgColor: 'bg-orange-500/10', borderColor: 'border-orange-500/30' },
  { label: '旷课', score: -5, icon: UserX, color: 'text-red-400', bgColor: 'bg-red-500/10', borderColor: 'border-red-500/30' },
]

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

// 默认选中第一个班级
watch(classList, (list) => {
  if (list.length > 0 && !selectedClass.value) {
    selectedClass.value = list[0].name
  }
}, { immediate: true })

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

const openScoreDialog = (student: Student, defaultScore: number = 0, defaultReason: string = '') => {
  selectedStudent.value = student
  scoreChange.value = defaultScore || 10
  scoreReason.value = defaultReason
  showScoreDialog.value = true
}

// 处理快速分数调整
const handleQuickScore = async (student: Student, score: number, reason: string) => {
  try {
    await updateScore({
      id: student.id,
      data: {
        score_change: score,
        reason: reason,
      },
    })
    toastMessage.value = `${student.name} ${score > 0 ? '+' : ''}${score}分`
    toastVariant.value = 'success'
    showToast.value = true
  } catch (err: any) {
    toastMessage.value = err.message || '调整分数失败'
    toastVariant.value = 'error'
    showToast.value = true
  }
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
          :key="student.id"
          class="border-white/10 bg-white/[0.02] p-4 hover:bg-white/[0.04] transition-colors"
          :class="student.is_active ? 'border-green-500/30' : ''"
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
            <Badge :variant="student.is_active ? 'success' : 'secondary'" class="text-xs">
              {{ student.is_active ? '活跃' : '非活跃' }}
            </Badge>
          </div>
          
          <!-- 分数显示 -->
          <div class="mb-3">
            <p class="text-xs text-white/40 mb-1">当前分数</p>
            <p class="text-xl font-bold text-primary">{{ student.score }}</p>
          </div>
          
          <!-- 快速操作按钮 -->
          <div class="grid grid-cols-3 gap-2">
            <Button
              v-for="option in quickScoreOptions"
              :key="option.label"
              size="sm"
              variant="outline"
              class="flex flex-col items-center gap-1 h-auto py-2 px-1 text-xs"
              :class="[option.borderColor, option.color, option.bgColor]"
              :disabled="isUpdatingScore"
              @click="handleQuickScore(student, option.score, option.label)"
            >
              <component :is="option.icon" class="h-3.5 w-3.5" />
              <span>{{ option.label }}</span>
              <span :class="option.score > 0 ? 'text-green-400' : 'text-red-400'">
                {{ option.score > 0 ? '+' : '' }}{{ option.score }}
              </span>
            </Button>
          </div>
          
          <!-- 自定义分数按钮 -->
          <div class="mt-2 flex gap-2">
            <Button
              size="sm"
              variant="outline"
              class="flex-1 border-green-500/30 text-green-400 hover:bg-green-500/10"
              @click="openScoreDialog(student, 10, '加分')"
            >
              <Plus class="h-3 w-3 mr-1" />
              加分
            </Button>
            <Button
              size="sm"
              variant="outline"
              class="flex-1 border-red-500/30 text-red-400 hover:bg-red-500/10"
              @click="openScoreDialog(student, -10, '扣分')"
            >
              <Minus class="h-3 w-3 mr-1" />
              扣分
            </Button>
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
