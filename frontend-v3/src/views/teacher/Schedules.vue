<script setup lang="ts">
import { ref, computed } from 'vue'
import { useSchedules, useImportSchedules, useDeleteSchedule, useDownloadTemplate } from '@/composables/useSchedules'
import { useClasses, useToast } from '@/composables'
import { useAuthStore } from '@/stores/auth'
import { Card, Button, Badge, Dialog, DataContainer, MobilePicker } from '@/components/ui'
import ScheduleAdjustmentDialog from '@/components/teacher/ScheduleAdjustmentDialog.vue'
import { Upload, Download, Trash2, Calendar, Clock, MapPin, BookOpen, Layers, AlertCircle, UserX, AlertTriangle, CheckSquare, X, Settings2 } from 'lucide-vue-next'
import { getErrorMessage } from '@/lib/error'
import { getCurrentWeek } from '@/lib/date'

// ========== 课程类型颜色主题 ==========
const courseTypeThemes = [
  { bg: 'bg-blue-500/10', border: 'border-blue-500/30', text: 'text-blue-400', icon: 'text-blue-400', accent: 'bg-blue-500/20' },
  { bg: 'bg-green-500/10', border: 'border-green-500/30', text: 'text-green-400', icon: 'text-green-400', accent: 'bg-green-500/20' },
  { bg: 'bg-purple-500/10', border: 'border-purple-500/30', text: 'text-purple-400', icon: 'text-purple-400', accent: 'bg-purple-500/20' },
  { bg: 'bg-orange-500/10', border: 'border-orange-500/30', text: 'text-orange-400', icon: 'text-orange-400', accent: 'bg-orange-500/20' },
] as const

// 根据课程名称生成稳定的颜色索引
const getCourseThemeIndex = (courseName: string): number => {
  let hash = 0
  for (let i = 0; i < courseName.length; i++) {
    hash = courseName.charCodeAt(i) + ((hash << 5) - hash)
  }
  return Math.abs(hash) % courseTypeThemes.length
}

// 获取课程主题色
const getCourseTheme = (courseName: string) => {
  const index = getCourseThemeIndex(courseName)
  return courseTypeThemes[index]
}

// 卡片主题辅助函数
type CardColor = 'blue' | 'green' | 'purple' | 'orange'

const getCardStyle = (color: CardColor) => {
  const varPrefix = `--card-${color}`
  return {
    backgroundColor: `var(${varPrefix}-bg)`,
    borderColor: `var(${varPrefix}-border)`,
    '--tw-shadow-color': `var(${varPrefix}-shadow)`,
  } as Record<string, string>
}

const getCardIconStyle = (color: CardColor) => {
  const varPrefix = `--card-${color}`
  return {
    backgroundColor: `var(${varPrefix}-icon-bg)`,
    color: `var(${varPrefix}-icon-text)`,
  }
}

const getCardGlowStyle = (color: CardColor) => {
  const varPrefix = `--card-${color}`
  return {
    backgroundColor: `var(${varPrefix}-glow)`,
  }
}

// 计算课程卡片样式
const computedCourseCardClass = (schedule: typeof schedules.value[0]) => {
  const theme = getCourseTheme(schedule.course_name)
  const baseClass = 'flex-1 p-4 transition-all duration-200 relative overflow-hidden'

  if (hasConflict(schedule)) {
    return `${baseClass} border-red-500/50 bg-red-500/5 hover:border-red-500/70`
  }
  if (isSelected(schedule.id)) {
    return `${baseClass} border-primary/50 bg-primary/5 ${theme.border} ${theme.bg}`
  }
  return `${baseClass} hover:border-white/20 ${theme.border} ${theme.bg}`
}

// 获取当前用户
const authStore = useAuthStore()
const isAdmin = computed(() => authStore.isAdmin)
const currentUser = computed(() => authStore.user)

// 查询条件
const selectedClass = ref('')
const selectedDay = ref<number | undefined>(undefined)
const selectedWeek = ref<number | undefined>(undefined)

// 获取数据
const { data: classes } = useClasses()

// 查询参数 - 使用 ref 存储筛选条件
const queryParams = computed(() => ({
  class_name: selectedClass.value || undefined,
  day_of_week: selectedDay.value,
  // 教师只看到自己的课程，管理员看到所有
  teacher_id: isAdmin.value ? undefined : currentUser.value?.id
}))

// 周次选项（1-20周）
const weekOptions = Array.from({ length: 20 }, (_, i) => i + 1)

// 为 MobilePicker 准备的周次选项
const weekPickerOptions = computed(() => {
  return weekOptions.map(week => ({
    value: week,
    label: `第${week}周`,
    subtitle: week === currentWeek.value ? '本周' : undefined
  }))
})

// 为 MobilePicker 准备的班级选项
const classPickerOptions = computed(() => {
  return (classes.value || []).map(cls => ({
    value: cls.name,
    label: cls.name
  }))
})

// 为 MobilePicker 准备的星期选项
const dayPickerOptions = [
  { value: 1, label: '周一' },
  { value: 2, label: '周二' },
  { value: 3, label: '周三' },
  { value: 4, label: '周四' },
  { value: 5, label: '周五' },
  { value: 6, label: '周六' },
  { value: 7, label: '周日' }
]

// 按周次筛选的课程
const filteredSchedulesByWeek = computed(() => {
  if (!selectedWeek.value) return schedules.value
  return schedules.value.filter(s => 
    selectedWeek.value! >= s.week_start && selectedWeek.value! <= s.week_end
  )
})

// 更新按星期分组的计算属性以使用周次筛选后的数据
const filteredSchedulesByDay = computed(() => {
  const grouped: Record<number, typeof schedules.value> = {
    1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: []
  }
  filteredSchedulesByWeek.value.forEach(s => {
    if (grouped[s.day_of_week]) {
      grouped[s.day_of_week].push(s)
    }
  })
  return grouped
})

const { data: schedules, isPending, error, refetch } = useSchedules(queryParams)

// 导入相关
const showImportDialog = ref(false)
const selectedFile = ref<File | null>(null)
const { mutateAsync: importSchedules, isPending: isImporting } = useImportSchedules()

// 删除相关
const { mutateAsync: deleteSchedule, isPending: isDeleting } = useDeleteSchedule()

// 调课相关
const showAdjustmentDialog = ref(false)
const adjustmentSchedule = ref<{
  id: number
  course_name: string
  class_name: string
  classroom?: string
  start_time?: string
  end_time?: string
} | null>(null)
const adjustmentWeek = ref(1)

const canAdjustSchedule = (schedule: typeof schedules.value[0]) => {
  return isAdmin.value || (currentUser.value?.id && schedule.teacher_id === currentUser.value.id)
}

const openAdjustmentDialog = (schedule: typeof schedules.value[0]) => {
  adjustmentSchedule.value = {
    id: schedule.id,
    course_name: schedule.course_name,
    class_name: schedule.class_name,
    classroom: schedule.classroom,
    start_time: schedule.start_time,
    end_time: schedule.end_time,
  }
  adjustmentWeek.value = selectedWeek.value || currentWeek.value
  showAdjustmentDialog.value = true
}

const handleAdjustmentSuccess = () => {
  showSuccessToast('课程调整已提交')
  refetch()
}

// 下载模板
const { download: downloadTemplate } = useDownloadTemplate()

// Toast (队列模式)
const { success: showSuccessToast, error: showErrorToast, showToast } = useToast()

// 星期选项
const weekDays = [
  { value: 1, label: '周一' },
  { value: 2, label: '周二' },
  { value: 3, label: '周三' },
  { value: 4, label: '周四' },
  { value: 5, label: '周五' },
  { value: 6, label: '周六' },
  { value: 7, label: '周日' },
]

// ========== 统计卡片数据 ==========
// 总课程数
const totalSchedules = computed(() => schedules.value.length)

// 当前周次
const currentWeek = computed(() => getCurrentWeek())

// 本周课程数（基于选中的周次或当前周）
const thisWeekSchedules = computed(() => {
  const week = selectedWeek.value || currentWeek.value
  return schedules.value.filter(s => 
    week >= s.week_start && week <= s.week_end
  ).length
})

// 未分配教师的课程数
const unassignedSchedules = computed(() => {
  return schedules.value.filter(s => !s.teacher_id).length
})

// 冲突检测
const conflicts = computed(() => {
  const conflictList: Array<{
    type: 'teacher' | 'classroom'
    day: number
    time: string
    items: typeof schedules.value
  }> = []
  
  // 按天分组检测
  for (let day = 1; day <= 7; day++) {
    const daySchedules = schedules.value.filter(s => s.day_of_week === day)
    
    // 检测教师时间冲突
    const teacherMap = new Map<number, typeof daySchedules>()
    daySchedules.forEach(s => {
      if (s.teacher_id) {
        if (!teacherMap.has(s.teacher_id)) {
          teacherMap.set(s.teacher_id, [])
        }
        teacherMap.get(s.teacher_id)!.push(s)
      }
    })
    
    teacherMap.forEach((teacherSchedules, _teacherId) => {
      // 检查时间重叠
      for (let i = 0; i < teacherSchedules.length; i++) {
        for (let j = i + 1; j < teacherSchedules.length; j++) {
          const s1 = teacherSchedules[i]
          const s2 = teacherSchedules[j]
          // 时间重叠检测
          if (s1.start_time < s2.end_time && s2.start_time < s1.end_time) {
            conflictList.push({
              type: 'teacher',
              day,
              time: `${s1.start_time}-${s1.end_time}`,
              items: [s1, s2]
            })
          }
        }
      }
    })
    
    // 检测教室时间冲突
    const classroomMap = new Map<string, typeof daySchedules>()
    daySchedules.forEach(s => {
      if (s.classroom) {
        if (!classroomMap.has(s.classroom)) {
          classroomMap.set(s.classroom, [])
        }
        classroomMap.get(s.classroom)!.push(s)
      }
    })
    
    classroomMap.forEach((roomSchedules, _classroom) => {
      for (let i = 0; i < roomSchedules.length; i++) {
        for (let j = i + 1; j < roomSchedules.length; j++) {
          const s1 = roomSchedules[i]
          const s2 = roomSchedules[j]
          if (s1.start_time < s2.end_time && s2.start_time < s1.end_time) {
            conflictList.push({
              type: 'classroom',
              day,
              time: `${s1.start_time}-${s1.end_time}`,
              items: [s1, s2]
            })
          }
        }
      }
    })
  }
  
  return conflictList
})

const conflictCount = computed(() => conflicts.value.length)

// 判断某个课程是否有冲突
const getScheduleConflicts = (schedule: typeof schedules.value[0]) => {
  return conflicts.value.filter(c => 
    c.items.some(item => item.id === schedule.id)
  )
}

const hasConflict = (schedule: typeof schedules.value[0]) => {
  return getScheduleConflicts(schedule).length > 0
}

// 处理文件选择
const handleFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0]
  }
}

// 处理导入
const handleImport = async () => {
  if (!selectedFile.value) {
    showErrorToast('请选择文件')
    return
  }

  try {
    const result = await importSchedules(selectedFile.value)
    showImportDialog.value = false
    selectedFile.value = null
    
    if (result.errors && result.errors.length > 0) {
      showToast(`导入完成: ${result.imported} 条成功, ${result.errors.length} 条失败`, 'default')
    } else {
      showSuccessToast(`成功导入 ${result.imported} 条课程`)
    }
  } catch (err: unknown) {
    showErrorToast(getErrorMessage(err) || '导入失败')
  }
}

// 处理删除
const handleDelete = async (id: number) => {
  if (!confirm('确定要删除这门课程吗？')) return
  
  try {
    await deleteSchedule(id)
    showSuccessToast('课程已删除')
  } catch (err: unknown) {
    showErrorToast(getErrorMessage(err) || '删除失败')
  }
}

// ========== 批量操作 ==========
const isBatchMode = ref(false)
const selectedScheduleIds = ref<number[]>([])
const showBatchActions = computed(() => selectedScheduleIds.value.length > 0)

// 切换批量模式
const toggleBatchMode = () => {
  isBatchMode.value = !isBatchMode.value
  if (!isBatchMode.value) {
    selectedScheduleIds.value = []
  }
}

// 选择/取消选择课程
const toggleSelectSchedule = (id: number) => {
  const index = selectedScheduleIds.value.indexOf(id)
  if (index > -1) {
    selectedScheduleIds.value.splice(index, 1)
  } else {
    selectedScheduleIds.value.push(id)
  }
}

// 是否已选中
const isSelected = (id: number) => selectedScheduleIds.value.includes(id)

// 全选当前筛选结果
const selectAll = () => {
  selectedScheduleIds.value = filteredSchedulesByWeek.value.map(s => s.id)
}

// 取消全选
const deselectAll = () => {
  selectedScheduleIds.value = []
}

// 批量删除
const handleBatchDelete = async () => {
  if (selectedScheduleIds.value.length === 0) return
  
  if (!confirm(`确定要删除选中的 ${selectedScheduleIds.value.length} 门课程吗？此操作不可恢复。`)) {
    return
  }
  
  try {
    await Promise.all(selectedScheduleIds.value.map(id => deleteSchedule(id)))
    showSuccessToast(`已删除 ${selectedScheduleIds.value.length} 门课程`)
    selectedScheduleIds.value = []
    isBatchMode.value = false
  } catch (err: unknown) {
    showErrorToast(getErrorMessage(err) || '批量删除失败')
  }
}
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-5">
      <div class="min-w-0">
        <h1 class="text-xl sm:text-2xl font-bold text-white">
          课表管理
        </h1>
        <p class="text-sm text-white/60 mt-1">
          管理课程安排，支持批量导入
        </p>
      </div>
      <div class="flex flex-wrap gap-2 sm:flex-shrink-0">
        <!-- 批量模式切换 -->
        <Button
          v-if="isAdmin"
          :variant="isBatchMode ? 'default' : 'outline'"
          size="sm"
          class="min-h-[40px]"
          @click="toggleBatchMode"
        >
          <CheckSquare class="mr-1.5 h-4 w-4" />
          <span class="hidden sm:inline">{{ isBatchMode ? '退出批量' : '批量操作' }}</span>
          <span class="sm:hidden">批量</span>
        </Button>
        <Button
          v-if="isAdmin"
          variant="outline"
          size="sm"
          class="min-h-[40px]"
          @click="downloadTemplate"
        >
          <Download class="mr-1.5 h-4 w-4" />
          <span class="hidden sm:inline">下载模板</span>
          <span class="sm:hidden">模板</span>
        </Button>
        <Button
          v-if="isAdmin"
          size="sm"
          class="min-h-[40px]"
          @click="showImportDialog = true"
        >
          <Upload class="mr-1.5 h-4 w-4" />
          <span class="hidden sm:inline">导入课表</span>
          <span class="sm:hidden">导入</span>
        </Button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-2 gap-4 lg:grid-cols-4 mb-5">
      <!-- 总课程数 - blue主题 -->
      <Card class="relative overflow-hidden p-4 transition-all duration-300" :style="getCardStyle('blue')">
        <div class="relative z-10 flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-lg flex-shrink-0 shadow-inner" :style="getCardIconStyle('blue')">
            <Layers class="h-5 w-5" :style="{ color: 'var(--card-blue-icon-text)' }" />
          </div>
          <div class="min-w-0">
            <p class="text-sm text-white/60 truncate">
              总课程数
            </p>
            <p class="text-2xl font-bold text-white">
              {{ totalSchedules }}
            </p>
          </div>
        </div>
        <div class="absolute -right-4 -bottom-4 h-16 w-16 rounded-full blur-2xl opacity-30" :style="getCardGlowStyle('blue')" />
      </Card>

      <!-- 本周课程 - green主题 -->
      <Card class="relative overflow-hidden p-4 transition-all duration-300" :style="getCardStyle('green')">
        <div class="relative z-10 flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-lg flex-shrink-0 shadow-inner" :style="getCardIconStyle('green')">
            <Calendar class="h-5 w-5" :style="{ color: 'var(--card-green-icon-text)' }" />
          </div>
          <div class="min-w-0">
            <p class="text-sm text-white/60 truncate">
              本周课程（第{{ currentWeek }}周）
            </p>
            <p class="text-2xl font-bold text-white">
              {{ thisWeekSchedules }}
            </p>
          </div>
        </div>
        <div class="absolute -right-4 -bottom-4 h-16 w-16 rounded-full blur-2xl opacity-30" :style="getCardGlowStyle('green')" />
      </Card>

      <!-- 冲突检测 -->
      <Card 
        class="border-white/10 p-4 transition-colors"
        :class="conflictCount > 0 ? 'bg-red-500/5 border-red-500/20' : 'bg-white/[0.02]'"
      >
        <div class="flex items-center gap-3">
          <div 
            class="flex h-10 w-10 items-center justify-center rounded-lg"
            :class="conflictCount > 0 ? 'bg-red-500/10' : 'bg-yellow-500/10'"
          >
            <AlertCircle 
              class="h-5 w-5" 
              :class="conflictCount > 0 ? 'text-red-400' : 'text-yellow-400'"
            />
          </div>
          <div>
            <p
              class="text-sm"
              :class="conflictCount > 0 ? 'text-red-400' : 'text-white/60'"
            >
              冲突检测
            </p>
            <p 
              class="text-2xl font-bold"
              :class="conflictCount > 0 ? 'text-red-400' : 'text-white'"
            >
              {{ conflictCount }}
            </p>
          </div>
        </div>
      </Card>

      <!-- 未分配教师 -->
      <Card 
        class="border-white/10 p-4 transition-colors"
        :class="unassignedSchedules > 0 ? 'bg-orange-500/5 border-orange-500/20' : 'bg-white/[0.02]'"
      >
        <div class="flex items-center gap-3">
          <div 
            class="flex h-10 w-10 items-center justify-center rounded-lg"
            :class="unassignedSchedules > 0 ? 'bg-orange-500/10' : 'bg-blue-500/10'"
          >
            <UserX 
              class="h-5 w-5" 
              :class="unassignedSchedules > 0 ? 'text-orange-400' : 'text-blue-400'"
            />
          </div>
          <div>
            <p
              class="text-sm"
              :class="unassignedSchedules > 0 ? 'text-orange-400' : 'text-white/60'"
            >
              未分配教师
            </p>
            <p 
              class="text-2xl font-bold"
              :class="unassignedSchedules > 0 ? 'text-orange-400' : 'text-white'"
            >
              {{ unassignedSchedules }}
            </p>
          </div>
        </div>
      </Card>
    </div>

    <!-- Filters -->
    <Card class="p-4 mb-5">
      <div class="flex flex-col sm:flex-row sm:flex-wrap sm:items-end gap-3 sm:gap-4">
        <div class="w-full sm:w-48">
          <label class="mb-1 block text-sm text-white/60">班级</label>
          <MobilePicker
            v-model="selectedClass"
            title="选择班级"
            placeholder="全部班级"
            clearable
            :options="classPickerOptions"
          />
        </div>
        <div class="w-full sm:w-32">
          <label class="mb-1 block text-sm text-white/60">星期</label>
          <MobilePicker
            v-model="selectedDay"
            title="选择星期"
            placeholder="全部"
            clearable
            :options="dayPickerOptions"
          />
        </div>
        <!-- 周次筛选器 -->
        <div class="w-full sm:w-40">
          <label class="mb-1 block text-sm text-white/60">周次</label>
          <MobilePicker
            v-model="selectedWeek"
            title="选择周次"
            placeholder="全部周次"
            searchable
            clearable
            search-placeholder="搜索周次..."
            :options="weekPickerOptions"
          />
        </div>
        <!-- 快速跳转本周 -->
        <Button
          v-if="selectedWeek !== currentWeek"
          variant="outline"
          size="sm"
          class="w-full sm:w-auto min-h-[44px] sm:min-h-[36px]"
          @click="selectedWeek = currentWeek"
        >
          <Calendar class="mr-1 h-4 w-4" />
          本周
        </Button>
      </div>
    </Card>

    <!-- Schedule List -->
    <DataContainer
      :loading="isPending"
      :error="error"
      :has-data="filteredSchedulesByWeek.length > 0"
      empty-text="暂无课表数据，请先导入"
      @retry="refetch"
    >
      <div class="space-y-6">
        <div
          v-for="day in weekDays"
          :key="day.value"
        >
          <div
            v-if="filteredSchedulesByDay[day.value].length > 0"
            class="space-y-3"
          >
            <!-- Day Header -->
            <div class="flex items-center gap-3 mb-4">
              <div class="flex h-8 w-8 items-center justify-center rounded-xl bg-primary/20 text-sm font-bold text-primary shadow-lg shadow-primary/10">
                {{ day.label.charAt(1) }}
              </div>
              <h3 class="text-lg font-semibold text-white">
                {{ day.label }}
              </h3>
              <span class="px-2.5 py-0.5 rounded-full text-xs font-medium bg-white/5 text-white/60 border border-white/10">
                {{ filteredSchedulesByDay[day.value].length }} 节课
              </span>
            </div>

            <!-- 批量操作栏 -->
            <div
              v-if="isBatchMode && filteredSchedulesByDay[day.value].length > 0"
              class="flex items-center gap-2 py-2"
            >
              <Button
                variant="outline"
                size="sm"
                @click="selectAll"
              >
                全选本页
              </Button>
              <Button
                variant="outline"
                size="sm"
                @click="deselectAll"
              >
                取消全选
              </Button>
              <span class="text-sm text-white/60">
                已选择 {{ selectedScheduleIds.length }} 门课程
              </span>
            </div>

            <!-- Courses Timeline -->
            <div class="relative">
              <!-- 时间线轴线 -->
              <div class="absolute left-[7px] top-0 bottom-0 w-0.5 bg-gradient-to-b from-white/10 via-white/5 to-transparent" />

              <div class="space-y-3">
                <div
                  v-for="schedule in filteredSchedulesByDay[day.value]"
                  :key="schedule.id"
                  class="relative flex items-start gap-4"
                  @click="isBatchMode && toggleSelectSchedule(schedule.id)"
                >
                  <!-- 时间节点 -->
                  <div class="relative flex flex-col items-center pt-2">
                    <!-- 时间点指示器 -->
                    <div
                      class="w-4 h-4 rounded-full border-2 transition-all duration-200 z-10"
                      :class="[
                        hasConflict(schedule)
                          ? 'bg-red-500 border-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]'
                          : getCourseTheme(schedule.course_name).bg.replace('/10', '/20').replace('bg-', 'border-'),
                        hasConflict(schedule)
                          ? ''
                          : getCourseTheme(schedule.course_name).border.replace('/30', '')
                      ]"
                    >
                      <div
                        v-if="!hasConflict(schedule)"
                        class="w-full h-full rounded-full"
                        :class="getCourseTheme(schedule.course_name).bg.replace('/10', '/40')"
                      />
                    </div>
                  </div>

                  <!-- 课程卡片 -->
                  <Card
                    :class="computedCourseCardClass(schedule)"
                  >
                    <!-- 主题色装饰条 -->
                    <div
                      v-if="!hasConflict(schedule)"
                      class="absolute left-0 top-0 bottom-0 w-1 transition-all duration-200"
                      :class="getCourseTheme(schedule.course_name).accent.replace('/20', '')"
                    />

                    <!-- 批量选择框 -->
                    <div
                      v-if="isBatchMode"
                      class="absolute top-3 right-3"
                    >
                      <div
                        class="flex h-5 w-5 items-center justify-center rounded border transition-colors"
                        :class="isSelected(schedule.id)
                          ? 'bg-primary border-primary'
                          : 'border-white/30 bg-white/5'"
                      >
                        <CheckSquare
                          v-if="isSelected(schedule.id)"
                          class="h-3.5 w-3.5 text-white"
                        />
                      </div>
                    </div>

                    <!-- 冲突标记 -->
                    <div
                      v-if="hasConflict(schedule)"
                      class="absolute -top-2 -right-2 flex h-6 w-6 items-center justify-center rounded-full bg-red-500 text-white shadow-lg shadow-red-500/30"
                      title="存在冲突"
                    >
                      <AlertTriangle class="h-3.5 w-3.5" />
                    </div>

                    <div class="flex items-start justify-between">
                      <div class="flex-1 min-w-0">
                        <!-- 课程标题行 -->
                        <div class="flex items-center gap-2 mb-2">
                          <div
                            class="flex h-8 w-8 items-center justify-center rounded-lg"
                            :class="hasConflict(schedule) ? 'bg-red-500/10' : getCourseTheme(schedule.course_name).accent"
                          >
                            <BookOpen
                              class="h-4 w-4"
                              :class="hasConflict(schedule) ? 'text-red-400' : getCourseTheme(schedule.course_name).icon"
                            />
                          </div>
                          <h4
                            class="font-semibold text-base truncate"
                            :class="hasConflict(schedule) ? 'text-red-400' : 'text-white'"
                          >
                            {{ schedule.course_name }}
                          </h4>
                        </div>

                        <!-- 时间信息 - 突出显示 -->
                        <div class="flex items-center gap-2 mb-3">
                          <div
                            class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-sm font-medium"
                            :class="hasConflict(schedule) ? 'bg-red-500/10 text-red-400' : 'bg-white/5 text-white/80'"
                          >
                            <Clock class="h-3.5 w-3.5" />
                            {{ schedule.start_time }} - {{ schedule.end_time }}
                          </div>
                        </div>

                        <!-- 详细信息网格 -->
                        <div class="grid grid-cols-2 gap-2 text-sm">
                          <div class="flex items-center gap-2 text-white/60">
                            <Calendar
                              class="h-3.5 w-3.5"
                              :class="hasConflict(schedule) ? 'text-red-400/60' : getCourseTheme(schedule.course_name).icon"
                            />
                            <span class="truncate">{{ schedule.class_name }}</span>
                          </div>
                          <div
                            v-if="schedule.classroom"
                            class="flex items-center gap-2 text-white/60"
                          >
                            <MapPin
                              class="h-3.5 w-3.5"
                              :class="hasConflict(schedule) ? 'text-red-400/60' : getCourseTheme(schedule.course_name).icon"
                            />
                            <span class="truncate">{{ schedule.classroom }}</span>
                          </div>
                        </div>

                        <!-- 冲突提示 -->
                        <div
                          v-if="hasConflict(schedule)"
                          class="mt-3"
                        >
                          <div
                            v-for="(conflict, idx) in getScheduleConflicts(schedule).slice(0, 1)"
                            :key="idx"
                            class="text-xs text-red-400 flex items-center gap-1.5 bg-red-500/10 px-2 py-1.5 rounded-md"
                          >
                            <AlertTriangle class="h-3 w-3 flex-shrink-0" />
                            <span v-if="conflict.type === 'teacher'">
                              教师时间冲突：{{ conflict.time }}
                            </span>
                            <span v-else>
                              教室冲突：{{ conflict.time }}
                            </span>
                          </div>
                        </div>

                        <!-- 底部标签 -->
                        <div class="mt-3 flex items-center gap-2 flex-wrap">
                          <Badge
                            :variant="hasConflict(schedule) ? 'error' : 'secondary'"
                            class="text-xs"
                          >
                            {{ schedule.teacher_name || '未分配教师' }}
                          </Badge>
                          <span class="text-xs text-white/40">
                            第{{ schedule.week_start }}-{{ schedule.week_end }}周
                          </span>
                        </div>
                      </div>

                      <!-- 调课按钮 -->
                      <Button
                        v-if="canAdjustSchedule(schedule)"
                        variant="ghost"
                        size="sm"
                        class="h-8 w-8 p-0 text-white/40 hover:text-primary flex-shrink-0 ml-1"
                        @click="openAdjustmentDialog(schedule)"
                      >
                        <Settings2 class="h-4 w-4" />
                      </Button>

                      <!-- 删除按钮 -->
                      <Button
                        v-if="isAdmin"
                        variant="ghost"
                        size="sm"
                        class="h-8 w-8 p-0 text-white/40 hover:text-red-400 flex-shrink-0 ml-1"
                        :loading="isDeleting"
                        @click="handleDelete(schedule.id)"
                      >
                        <Trash2 class="h-4 w-4" />
                      </Button>
                    </div>
                  </Card>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </DataContainer>

    <!-- 调课弹窗 -->
    <ScheduleAdjustmentDialog
      v-model:open="showAdjustmentDialog"
      :schedule="adjustmentSchedule"
      :week-number="adjustmentWeek"
      @success="handleAdjustmentSuccess"
    />

    <!-- Import Dialog -->
    <Dialog
      v-model:open="showImportDialog"
      title="导入课表"
    >
      <div class="space-y-4">
        <div class="rounded-lg border border-border bg-background-card p-4">
          <h4 class="mb-2 text-sm font-medium text-white">
            导入说明
          </h4>
          <ul class="space-y-1 text-sm text-white/60">
            <li>1. 支持 .xlsx 或 .csv 格式</li>
            <li>2. 请先下载模板，按模板格式填写</li>
            <li>3. 必填字段：课程名称、班级、教师姓名、星期、开始时间、结束时间</li>
            <li>4. 星期：1=周一，2=周二，...，7=周日</li>
          </ul>
        </div>

        <div>
          <label class="mb-2 block text-sm text-white/60">选择文件</label>
          <input
            type="file"
            accept=".xlsx,.csv"
            class="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white file:mr-4 file:rounded-md file:border-0 file:bg-primary file:px-3 file:py-1 file:text-sm file:text-white hover:file:bg-primary/80"
            @change="handleFileChange"
          >
          <p
            v-if="selectedFile"
            class="mt-2 text-sm text-white/60"
          >
            已选择: {{ selectedFile.name }}
          </p>
        </div>
      </div>

      <template #footer>
        <Button
          variant="outline"
          @click="showImportDialog = false"
        >
          取消
        </Button>
        <Button
          :loading="isImporting"
          @click="handleImport"
        >
          <Upload class="mr-2 h-4 w-4" />
          导入
        </Button>
      </template>
    </Dialog>

    <!-- 底部批量操作栏 -->
    <div
      v-if="showBatchActions"
      class="fixed bottom-6 left-1/2 z-50 flex -translate-x-1/2 items-center gap-3 rounded-lg border border-white/10 bg-[#030307] px-4 py-3 shadow-lg"
    >
      <span class="text-sm text-white/80">
        已选择 <span class="font-bold text-primary">{{ selectedScheduleIds.length }}</span> 门课程
      </span>
      <div class="h-4 w-px bg-white/10" />
      <Button
        variant="destructive"
        size="sm"
        @click="handleBatchDelete"
      >
        <Trash2 class="mr-1 h-4 w-4" />
        批量删除
      </Button>
      <Button
        variant="outline"
        size="sm"
        @click="deselectAll"
      >
        <X class="mr-1 h-4 w-4" />
        取消
      </Button>
    </div>
  </div>
</template>
