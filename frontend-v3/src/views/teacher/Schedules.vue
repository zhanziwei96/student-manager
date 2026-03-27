<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useSchedules, useImportSchedules, useDeleteSchedule, useDownloadTemplate } from '@/composables/useSchedules'
import { useClasses, useToast } from '@/composables'
import { useAuthStore } from '@/stores/auth'
import { Card, Button, Badge, Dialog, DataContainer } from '@/components/ui'
import { Upload, Download, Trash2, Calendar, Clock, MapPin, BookOpen } from 'lucide-vue-next'
import { Toast } from '@/components/ui'
import { getErrorMessage } from '@/lib/error'

// 获取当前用户权限
const authStore = useAuthStore()
const isAdmin = computed(() => authStore.isAdmin)

// 查询条件
const selectedClass = ref('')
const selectedDay = ref<number | undefined>(undefined)

// 获取数据
const { data: classes } = useClasses()

// 查询参数 - 使用 ref 存储筛选条件
const queryParams = ref({
  class_name: selectedClass.value || undefined,
  day_of_week: selectedDay.value
})

// 监听筛选条件变化，更新查询参数
watch([selectedClass, selectedDay], () => {
  queryParams.value = {
    class_name: selectedClass.value || undefined,
    day_of_week: selectedDay.value
  }
})

const { data: schedules, isPending, error, refetch } = useSchedules(queryParams)

// 导入相关
const showImportDialog = ref(false)
const selectedFile = ref<File | null>(null)
const { mutateAsync: importSchedules, isPending: isImporting } = useImportSchedules()

// 删除相关
const { mutateAsync: deleteSchedule, isPending: isDeleting } = useDeleteSchedule()

// 下载模板
const { download: downloadTemplate } = useDownloadTemplate()

// Toast (REVIEW-P1: 使用全局 useToast composable)
const { show, message: toastMessage, variant: toastVariant, success: showSuccessToast, error: showErrorToast, showToast } = useToast()

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

// 按星期分组
const schedulesByDay = computed(() => {
  const grouped: Record<number, typeof schedules.value> = {
    1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: []
  }
  schedules.value.forEach(s => {
    if (grouped[s.day_of_week]) {
      grouped[s.day_of_week].push(s)
    }
  })
  return grouped
})

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
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-white">
          课表管理
        </h1>
        <p class="text-white/60">
          管理课程安排，支持批量导入
        </p>
      </div>
      <div class="flex gap-2">
        <Button
          v-if="isAdmin"
          variant="outline"
          @click="downloadTemplate"
        >
          <Download class="mr-2 h-4 w-4" />
          下载模板
        </Button>
        <Button
          v-if="isAdmin"
          @click="showImportDialog = true"
        >
          <Upload class="mr-2 h-4 w-4" />
          导入课表
        </Button>
      </div>
    </div>

    <!-- Filters -->
    <Card class="border-white/10 bg-white/[0.02] p-4">
      <div class="flex flex-wrap gap-4">
        <div class="w-48">
          <label class="mb-1 block text-sm text-white/60">班级</label>
          <select
            v-model="selectedClass"
            class="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white focus:border-primary focus:outline-none [&>option]:bg-gray-900 [&>option]:text-white"
          >
            <option
              value=""
              class="bg-gray-900 text-white"
            >
              全部班级
            </option>
            <option
              v-for="cls in classes"
              :key="cls.name"
              :value="cls.name"
              class="bg-gray-900 text-white"
            >
              {{ cls.name }}
            </option>
          </select>
        </div>
        <div class="w-32">
          <label class="mb-1 block text-sm text-white/60">星期</label>
          <select
            v-model="selectedDay"
            class="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white focus:border-primary focus:outline-none [&>option]:bg-gray-900 [&>option]:text-white"
          >
            <option
              :value="undefined"
              class="bg-gray-900 text-white"
            >
              全部
            </option>
            <option
              v-for="day in weekDays"
              :key="day.value"
              :value="day.value"
              class="bg-gray-900 text-white"
            >
              {{ day.label }}
            </option>
          </select>
        </div>
      </div>
    </Card>

    <!-- Schedule List -->
    <DataContainer
      :loading="isPending"
      :error="error"
      :has-data="schedules.length > 0"
      empty-text="暂无课表数据，请先导入"
      @retry="refetch"
    >
      <div class="space-y-6">
        <div
          v-for="day in weekDays"
          :key="day.value"
        >
          <div
            v-if="schedulesByDay[day.value].length > 0"
            class="space-y-3"
          >
            <!-- Day Header -->
            <div class="flex items-center gap-2">
              <div class="flex h-6 w-6 items-center justify-center rounded-full bg-primary/20 text-xs text-primary">
                {{ day.label.charAt(1) }}
              </div>
              <h3 class="font-medium text-white">
                {{ day.label }}
              </h3>
              <span class="text-sm text-white/40">({{ schedulesByDay[day.value].length }}节课)</span>
            </div>

            <!-- Courses -->
            <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <Card
                v-for="schedule in schedulesByDay[day.value]"
                :key="schedule.id"
                class="border-white/10 bg-white/[0.02] p-4 hover:border-white/20 transition-colors"
              >
                <div class="flex items-start justify-between">
                  <div class="flex-1">
                    <div class="flex items-center gap-2">
                      <BookOpen class="h-4 w-4 text-primary" />
                      <h4 class="font-medium text-white">
                        {{ schedule.course_name }}
                      </h4>
                    </div>
                    <div class="mt-2 space-y-1 text-sm text-white/60">
                      <div class="flex items-center gap-2">
                        <Calendar class="h-3.5 w-3.5" />
                        {{ schedule.class_name }}
                      </div>
                      <div class="flex items-center gap-2">
                        <Clock class="h-3.5 w-3.5" />
                        {{ schedule.start_time }} - {{ schedule.end_time }}
                      </div>
                      <div
                        v-if="schedule.classroom"
                        class="flex items-center gap-2"
                      >
                        <MapPin class="h-3.5 w-3.5" />
                        {{ schedule.classroom }}
                      </div>
                    </div>
                    <div class="mt-2 flex items-center gap-2">
                      <Badge
                        variant="secondary"
                        class="text-xs"
                      >
                        {{ schedule.teacher_name || '未分配教师' }}
                      </Badge>
                      <span class="text-xs text-white/40">
                        第{{ schedule.week_start }}-{{ schedule.week_end }}周
                      </span>
                    </div>
                  </div>
                  <Button
                    v-if="isAdmin"
                    variant="ghost"
                    size="sm"
                    class="h-8 w-8 p-0 text-white/40 hover:text-red-400"
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
    </DataContainer>

    <!-- Import Dialog -->
    <Dialog
      v-model:open="showImportDialog"
      title="导入课表"
    >
      <div class="space-y-4">
        <div class="rounded-lg border border-white/10 bg-white/[0.02] p-4">
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

    <!-- Toast -->
    <Toast
      v-model:show="show"
      :message="toastMessage"
      :variant="toastVariant"
    />
  </div>
</template>
