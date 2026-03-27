<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Dialog, Button, Checkbox } from '@/components/ui'
import { Loader2, Search, Calendar, Filter } from 'lucide-vue-next'
import { useToast } from '@/composables/useToast'
import { useSchedules } from '@/composables/useSchedules'
import { useClasses } from '@/composables/useClasses'
import { schedulesApi } from '@/api/schedules'
import type { User } from '@/types'
import type { CourseSchedule } from '@/api/schedules'
import { getErrorMessage } from '@/lib/error'

const props = defineProps<{
  teacher: User | null
  open: boolean
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  'success': []
}>()

const { showToast } = useToast()

// 获取所有课表和班级
const { data: allSchedules, isPending: isLoadingSchedules } = useSchedules()
const { data: allClasses } = useClasses()

// 搜索和筛选
const searchQuery = ref('')
const selectedClass = ref<string>('')

// 选中的课程ID列表
const selectedScheduleIds = ref<number[]>([])

// 星期几映射
const dayNames = ['', '周一', '周二', '周三', '周四', '周五', '周六', '周日']

// 初始化选中的课程
watch(() => [props.teacher, allSchedules.value], ([teacher, schedules]) => {
  if (teacher && schedules) {
    // 获取该教师已分配的课程ID
    selectedScheduleIds.value = schedules
      .filter(s => s.teacher_id === teacher.id)
      .map(s => s.id)
  } else {
    selectedScheduleIds.value = []
  }
}, { immediate: true })

// 过滤后的课程列表
const filteredSchedules = computed(() => {
  if (!allSchedules.value) return []
  
  let result = allSchedules.value
  
  // 按班级筛选
  if (selectedClass.value) {
    result = result.filter(s => s.class_name === selectedClass.value)
  }
  
  // 按搜索词筛选
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(s => 
      s.course_name.toLowerCase().includes(query) ||
      s.class_name.toLowerCase().includes(query)
    )
  }
  
  return result
})

// 按星期几分组的课程
const groupedSchedules = computed(() => {
  const groups: Record<number, CourseSchedule[]> = {}
  
  filteredSchedules.value.forEach(schedule => {
    if (!groups[schedule.day_of_week]) {
      groups[schedule.day_of_week] = []
    }
    groups[schedule.day_of_week].push(schedule)
  })
  
  // 每天内按开始时间排序
  Object.keys(groups).forEach(day => {
    groups[Number(day)].sort((a, b) => a.start_time.localeCompare(b.start_time))
  })
  
  return groups
})

// 已选择的数量
const selectedCount = computed(() => selectedScheduleIds.value.length)

// 切换课程选择
const toggleSchedule = (scheduleId: number) => {
  const index = selectedScheduleIds.value.indexOf(scheduleId)
  if (index > -1) {
    selectedScheduleIds.value.splice(index, 1)
  } else {
    selectedScheduleIds.value.push(scheduleId)
  }
}

// 是否选中
const isSelected = (scheduleId: number) => {
  return selectedScheduleIds.value.includes(scheduleId)
}

// 保存中状态
const isSaving = ref(false)

// 保存修改
const handleSave = async () => {
  if (!props.teacher) return
  
  isSaving.value = true
  try {
    // 获取当前教师已分配的课程
    const currentAssignedIds = allSchedules.value
      ?.filter(s => s.teacher_id === props.teacher!.id)
      .map(s => s.id) || []
    
    // 需要取消分配的课程（之前已分配但现在未选中的）
    const toUnassign = currentAssignedIds.filter(id => !selectedScheduleIds.value.includes(id))
    
    // 需要分配的课程（之前未分配但现在选中的）
    const toAssign = selectedScheduleIds.value.filter(id => !currentAssignedIds.includes(id))
    
    // 执行分配和取消分配
    await Promise.all([
      // 分配新课程
      ...toAssign.map(id => schedulesApi.assign(id, props.teacher!.id, props.teacher!.name)),
      // 取消分配旧课程
      ...toUnassign.map(id => schedulesApi.unassign(id))
    ])
    
    showToast('课表分配已更新', 'success')
    emit('success')
    emit('update:open', false)
  } catch (error: unknown) {
    showToast(getErrorMessage(error) || '保存失败', 'error')
  } finally {
    isSaving.value = false
  }
}

// 关闭弹窗
const handleClose = () => {
  // 重置选择
  if (props.teacher && allSchedules.value) {
    selectedScheduleIds.value = allSchedules.value
      .filter(s => s.teacher_id === props.teacher!.id)
      .map(s => s.id)
  }
  selectedClass.value = ''
  searchQuery.value = ''
  emit('update:open', false)
}
</script>

<template>
  <Dialog
    :open="open"
    @update:open="handleClose"
    :title="`管理课表 - ${teacher?.name || ''}`"
    description="选择该教师负责的课程"
  >
    <div class="space-y-4">
      <!-- 筛选和搜索 -->
      <div class="flex gap-2">
        <div class="relative flex-1">
          <Filter class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/50" />
          <select
            v-model="selectedClass"
            class="w-full appearance-none rounded-lg border border-white/10 bg-white/[0.02] py-2 pl-10 pr-8 text-sm text-white focus:border-primary focus:outline-none"
          >
            <option value="">全部班级</option>
            <option v-for="cls in allClasses" :key="cls.name" :value="cls.name">
              {{ cls.name }}
            </option>
          </select>
        </div>
        <div class="relative flex-1">
          <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/50" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索课程..."
            class="w-full rounded-lg border border-white/10 bg-white/[0.02] py-2 pl-10 pr-4 text-sm text-white placeholder:text-white/40 focus:border-primary focus:outline-none"
          />
        </div>
      </div>

      <!-- 加载中 -->
      <div v-if="isLoadingSchedules" class="flex h-32 items-center justify-center">
        <Loader2 class="h-6 w-6 animate-spin text-primary" />
      </div>

      <!-- 课程列表 -->
      <div v-else-if="Object.keys(groupedSchedules).length > 0" class="max-h-[400px] space-y-4 overflow-y-auto">
        <div
          v-for="day in [1, 2, 3, 4, 5, 6, 7]"
          :key="day"
        >
          <div v-if="groupedSchedules[day]?.length" class="space-y-2">
            <h4 class="sticky top-0 bg-[#030307] py-1 text-sm font-medium text-primary">
              {{ dayNames[day] }}
            </h4>
            <div
              v-for="schedule in groupedSchedules[day]"
              :key="schedule.id"
              class="flex items-center gap-3 rounded-lg border border-white/10 bg-white/[0.02] p-3 hover:bg-white/[0.04] cursor-pointer transition-colors"
              @click="toggleSchedule(schedule.id)"
            >
              <Checkbox
                :checked="isSelected(schedule.id)"
                @click.stop
                @update:checked="() => toggleSchedule(schedule.id)"
              />
              <Calendar class="h-4 w-4 text-primary" />
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <span class="text-sm font-medium text-white">{{ schedule.course_name }}</span>
                  <span class="text-xs text-white/60">({{ schedule.class_name }})</span>
                </div>
                <div class="text-xs text-white/50">
                  {{ schedule.start_time }} - {{ schedule.end_time }}
                  <span v-if="schedule.classroom" class="ml-2">📍 {{ schedule.classroom }}</span>
                </div>
              </div>
              <div v-if="schedule.teacher_name && schedule.teacher_id !== teacher?.id" class="text-xs text-yellow-400">
                已由 {{ schedule.teacher_name }} 授课
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="flex h-32 flex-col items-center justify-center text-white/60">
        <Calendar class="mb-2 h-8 w-8" />
        <p>{{ searchQuery || selectedClass ? '未找到匹配的课程' : '暂无课程数据' }}</p>
      </div>

      <!-- 已选择统计 -->
      <div class="rounded-lg border border-white/10 bg-white/[0.02] p-3">
        <p class="text-sm text-white/80">
          已选择: <span class="font-medium text-primary">{{ selectedCount }}</span> 门课程
        </p>
      </div>
    </div>

    <template #footer>
      <Button
        type="button"
        variant="outline"
        @click="handleClose"
      >
        取消
      </Button>
      <Button
        type="button"
        :disabled="isSaving"
        @click="handleSave"
      >
        <Loader2
          v-if="isSaving"
          class="mr-2 h-4 w-4 animate-spin"
        />
        保存
      </Button>
    </template>
  </Dialog>
</template>
