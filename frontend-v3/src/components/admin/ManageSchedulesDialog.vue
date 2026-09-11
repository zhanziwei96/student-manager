<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Dialog, Button } from '@/components/ui'
import { Loader2, Search, Calendar, Filter, Check, X, Plus, Users } from 'lucide-vue-next'
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

// 当前选中的课程ID（即将保存的分配）
const selectedScheduleIds = ref<number[]>([])

// 原始分配的课程ID（用于对比变更）
const originalScheduleIds = ref<number[]>([])

// 星期几映射
const dayNames = ['', '周一', '周二', '周三', '周四', '周五', '周六', '周日']

// 初始化选中的课程
watch(() => [props.teacher, allSchedules.value], ([teacher, schedules]) => {
  if (!teacher || !('id' in teacher)) {
    selectedScheduleIds.value = []
    originalScheduleIds.value = []
    return
  }

  if (schedules && Array.isArray(schedules)) {
    const assignedIds = (schedules as { teacher_id: number | null; id: number }[])
      .filter((s: { teacher_id: number | null }) => s.teacher_id === teacher.id)
      .map((s: { id: number }) => s.id)
    selectedScheduleIds.value = [...assignedIds]
    originalScheduleIds.value = [...assignedIds]
  } else {
    selectedScheduleIds.value = []
    originalScheduleIds.value = []
  }
}, { immediate: true })

// 计算变更
const changes = computed(() => {
  const original = new Set(originalScheduleIds.value)
  const selected = new Set(selectedScheduleIds.value)
  
  const added = selectedScheduleIds.value.filter(id => !original.has(id))
  const removed = originalScheduleIds.value.filter(id => !selected.has(id))
  
  return { added, removed, hasChanges: added.length > 0 || removed.length > 0 }
})

// 过滤后的课程列表
const filteredSchedules = computed(() => {
  if (!allSchedules.value) return []
  
  let result = allSchedules.value
  
  // 按班级筛选（class_id）
  if (selectedClass.value) {
    result = result.filter(s => s.class_id === Number(selectedClass.value))
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

// 按星期几分组的课程（分离已分配和可分配）
const groupedSchedules = computed(() => {
  const groups: Record<number, { 
    assigned: CourseSchedule[], 
    available: CourseSchedule[] 
  }> = {}
  
  // 初始化所有天
  for (let day = 1; day <= 7; day++) {
    groups[day] = { assigned: [], available: [] }
  }
  
  filteredSchedules.value.forEach(schedule => {
    const day = schedule.day_of_week
    if (!groups[day]) return
    
    // 检查是否已分配给当前教师
    const isAssignedToCurrent = selectedScheduleIds.value.includes(schedule.id)
    
    if (isAssignedToCurrent) {
      groups[day].assigned.push(schedule)
    } else {
      groups[day].available.push(schedule)
    }
  })
  
  // 每天内按开始时间排序
  Object.keys(groups).forEach(day => {
    const dayNum = Number(day)
    groups[dayNum].assigned.sort((a: CourseSchedule, b: CourseSchedule) => a.start_time.localeCompare(b.start_time))
    groups[dayNum].available.sort((a: CourseSchedule, b: CourseSchedule) => a.start_time.localeCompare(b.start_time))
  })
  
  return groups
})

// 获取某天是否有课程
const hasSchedulesForDay = (day: number) => {
  const dayGroup = groupedSchedules.value[day]
  return dayGroup.assigned.length > 0 || dayGroup.available.length > 0
}

// 添加课程到已分配
const addSchedule = (scheduleId: number) => {
  if (!selectedScheduleIds.value.includes(scheduleId)) {
    selectedScheduleIds.value.push(scheduleId)
  }
}

// 从已分配中移除课程
const removeSchedule = (scheduleId: number) => {
  const index = selectedScheduleIds.value.indexOf(scheduleId)
  if (index > -1) {
    selectedScheduleIds.value.splice(index, 1)
  }
}

// 移除某天所有已分配课程
const removeAllForDay = (day: number) => {
  const dayGroup = groupedSchedules.value[day]
  dayGroup.assigned.forEach(s => removeSchedule(s.id))
}

// 添加某天所有可分配课程（只添加未被他人占用的）
const addAllAvailableForDay = (day: number) => {
  const dayGroup = groupedSchedules.value[day]
  dayGroup.available.forEach(s => {
    // 只添加未被其他教师占用的
    if (!s.teacher_id || s.teacher_id === props.teacher?.id) {
      addSchedule(s.id)
    }
  })
}

// 检查课程是否被其他教师占用
const isOccupiedByOther = (schedule: CourseSchedule) => {
  return schedule.teacher_id && schedule.teacher_id !== props.teacher?.id
}

// 保存中状态
const isSaving = ref(false)

// 保存修改
const handleSave = async () => {
  if (!props.teacher) return
  
  isSaving.value = true
  try {
    // 需要取消分配的课程
    const toUnassign = changes.value.removed
    // 需要分配的课程
    const toAssign = changes.value.added
    
    // 执行分配和取消分配
    await Promise.all([
      ...toAssign.map(id => schedulesApi.assign(id, props.teacher!.id, props.teacher!.name)),
      ...toUnassign.map(id => schedulesApi.unassign(id))
    ])
    
    // 更新原始分配记录
    originalScheduleIds.value = [...selectedScheduleIds.value]
    
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
  // 重置选择到原始状态
  if (props.teacher) {
    selectedScheduleIds.value = [...originalScheduleIds.value]
  }
  selectedClass.value = ''
  searchQuery.value = ''
  emit('update:open', false)
}
</script>

<template>
  <Dialog
    :open="open"
    :title="`管理课表 - ${teacher?.name || ''}`"
    description="管理该教师负责的课程"
    @update:open="handleClose"
  >
    <div class="space-y-4">
      <!-- 加载中 -->
      <div
        v-if="isLoadingSchedules"
        class="flex h-32 items-center justify-center"
      >
        <Loader2 class="h-6 w-6 animate-spin text-black" />
      </div>

      <template v-else>
        <!-- 筛选和搜索 -->
        <div class="flex gap-2">
          <div class="relative flex-1">
            <Filter class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#a3a3a3]" />
            <select
              v-model="selectedClass"
              class="w-full appearance-none rounded-full border border-[#e5e5e5] bg-[#fafafa] py-2 pl-10 pr-8 text-sm text-black focus:border-black focus:outline-none"
            >
              <option value="">
                全部班级
              </option>
              <option
                v-for="cls in allClasses"
                :key="cls.id"
                :value="cls.id"
              >
                {{ cls.display_name }}
              </option>
            </select>
          </div>
          <div class="relative flex-1">
            <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#a3a3a3]" />
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索课程..."
              class="w-full rounded-full border border-[#e5e5e5] bg-[#fafafa] py-2 pl-10 pr-4 text-sm text-black placeholder:text-[#a3a3a3] focus:border-black focus:outline-none"
            >
          </div>
        </div>

        <!-- 课程列表 -->
        <div
          v-if="Object.keys(groupedSchedules).some(day => hasSchedulesForDay(Number(day)))" 
          class="max-h-[400px] space-y-4 overflow-y-auto"
        >
          <div
            v-for="day in [1, 2, 3, 4, 5, 6, 7]"
            :key="day"
          >
            <div
              v-if="hasSchedulesForDay(day)"
              class="space-y-2"
            >
              <!-- 星期标题 -->
              <div class="flex items-center justify-between sticky top-0 bg-white py-1">
                <h4 class="text-sm font-medium text-black">
                  {{ dayNames[day] }}
                  <span class="text-xs text-[#a3a3a3] ml-1">
                    ({{ groupedSchedules[day].assigned.length }}已分配, {{ groupedSchedules[day].available.filter(s => !isOccupiedByOther(s)).length }}可分配)
                  </span>
                </h4>
                <div class="flex gap-1">
                  <button
                    v-if="groupedSchedules[day].available.filter(s => !isOccupiedByOther(s)).length > 0"
                    type="button"
                    class="text-xs px-2 py-0.5 rounded bg-[#e5e5e5] text-black hover:bg-[#d4d4d4] transition-colors"
                    @click="addAllAvailableForDay(day)"
                  >
                    全部添加
                  </button>
                  <button
                    v-if="groupedSchedules[day].assigned.length > 0"
                    type="button"
                    class="text-xs px-2 py-0.5 rounded bg-[rgba(239,68,68,0.1)] text-[#dc2626] hover:bg-[rgba(239,68,68,0.1)] transition-colors"
                    @click="removeAllForDay(day)"
                  >
                    全部移除
                  </button>
                </div>
              </div>

              <!-- 已分配课程 -->
              <div
                v-if="groupedSchedules[day].assigned.length > 0"
                class="space-y-1.5"
              >
                <div
                  v-for="schedule in groupedSchedules[day].assigned"
                  :key="schedule.id"
                  class="flex items-center gap-2 rounded-xl bg-[rgba(34,197,94,0.1)] border border-[rgba(34,197,94,0.3)] px-3 py-2 group hover:bg-[rgba(34,197,94,0.15)] transition-colors cursor-pointer"
                  @click="removeSchedule(schedule.id)"
                >
                  <Check class="h-4 w-4 text-[#16a34a]" />
                  <Calendar class="h-4 w-4 text-[#16a34a]" />
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2">
                      <span class="text-sm font-medium text-black">{{ schedule.course_name }}</span>
                      <span class="text-xs text-[#737373]">({{ schedule.class_name }})</span>
                    </div>
                    <div class="text-xs text-[#a3a3a3]">
                      {{ schedule.start_time }} - {{ schedule.end_time }}
                      <span
                        v-if="schedule.classroom"
                        class="ml-1"
                      >📍 {{ schedule.classroom }}</span>
                    </div>
                  </div>
                  <button
                    type="button"
                    class="p-1 rounded hover:bg-[rgba(239,68,68,0.1)] text-[#a3a3a3] hover:text-[#dc2626] transition-colors opacity-0 group-hover:opacity-100"
                    title="移除"
                  >
                    <X class="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>

              <!-- 可分配课程 -->
              <div
                v-if="groupedSchedules[day].available.length > 0"
                class="space-y-1.5"
              >
                <div
                  v-for="schedule in groupedSchedules[day].available"
                  :key="schedule.id"
                  class="flex items-center gap-2 rounded-xl border border-[#e5e5e5] bg-[#fafafa] px-3 py-2 transition-colors"
                  :class="isOccupiedByOther(schedule) ? 'opacity-50 cursor-not-allowed' : 'hover:bg-[#fafafa] cursor-pointer'"
                  @click="!isOccupiedByOther(schedule) && addSchedule(schedule.id)"
                >
                  <div 
                    class="w-4 h-4 rounded border flex items-center justify-center transition-colors"
                    :class="isOccupiedByOther(schedule) ? 'border-[#e5e5e5]' : 'border-[#d4d4d4] group-hover:border-[#d4d4d4]'"
                  >
                    <Plus 
                      v-if="!isOccupiedByOther(schedule)" 
                      class="h-3 w-3 text-transparent group-hover:text-[#525252] transition-colors" 
                    />
                  </div>
                  <Calendar class="h-4 w-4 text-[#a3a3a3]" />
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2">
                      <span class="text-sm text-[#262626]">{{ schedule.course_name }}</span>
                      <span class="text-xs text-[#a3a3a3]">({{ schedule.class_name }})</span>
                    </div>
                    <div class="text-xs text-[#a3a3a3]">
                      {{ schedule.start_time }} - {{ schedule.end_time }}
                      <span
                        v-if="schedule.classroom"
                        class="ml-1"
                      >📍 {{ schedule.classroom }}</span>
                    </div>
                  </div>
                  <div
                    v-if="isOccupiedByOther(schedule)"
                    class="flex items-center gap-1 text-xs text-[#d97706]"
                  >
                    <Users class="h-3 w-3" />
                    <span>已由 {{ schedule.teacher_name }} 授课</span>
                  </div>
                </div>
              </div>

              <!-- 分隔线 -->
              <div class="border-t border-[#f5f5f5] pt-2" />
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <div
          v-else
          class="flex h-32 flex-col items-center justify-center text-[#737373]"
        >
          <Calendar class="mb-2 h-8 w-8" />
          <p>{{ searchQuery || selectedClass ? '未找到匹配的课程' : '暂无课程数据' }}</p>
        </div>

        <!-- 变更摘要 -->
        <div 
          class="rounded-xl border p-3 transition-colors"
          :class="changes.hasChanges ? 'border-[#d4d4d4] bg-[#fafafa]' : 'border-[#e5e5e5] bg-[#fafafa]'"
        >
          <div class="flex items-center justify-between">
            <p class="text-sm text-[#737373]">
              <span v-if="!changes.hasChanges">暂无变更</span>
              <span
                v-else
                class="flex items-center gap-3"
              >
                <span
                  v-if="changes.added.length > 0"
                  class="text-[#16a34a]"
                >
                  +{{ changes.added.length }} 门新增
                </span>
                <span
                  v-if="changes.removed.length > 0"
                  class="text-[#dc2626]"
                >
                  -{{ changes.removed.length }} 门移除
                </span>
              </span>
            </p>
            <span class="text-xs text-[#a3a3a3]">
              共负责 {{ selectedScheduleIds.length }} 门课程
            </span>
          </div>
        </div>
      </template>
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
        :disabled="isSaving || !changes.hasChanges"
        @click="handleSave"
      >
        <Loader2
          v-if="isSaving"
          class="mr-2 h-4 w-4 animate-spin"
        />
        {{ changes.hasChanges ? `保存变更 (${changes.added.length + changes.removed.length})` : '暂无变更' }}
      </Button>
    </template>
  </Dialog>
</template>
