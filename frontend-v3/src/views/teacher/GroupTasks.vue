<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useClasses, useToast } from '@/composables'
import { Card, Button, Badge, Select, DataContainer, Dialog } from '@/components/ui'
import {
  useTeacherGroupTasks,
  useCreateGroupTask,
  useStartGroupTask,
  useCloseGroupTask,
} from '@/features/group-collaboration'
import { Plus, Play, Square, BarChart2, PenLine } from 'lucide-vue-next'
import { getErrorMessage } from '@/lib/error'
import type { ClassInfo } from '@/api/classes'

const router = useRouter()
const { success: toastSuccess, error: toastError } = useToast()

// 班级选择
const { data: classes } = useClasses()
const selectedClass = ref('')
watch(
  () => classes.value,
  (list) => {
    if (list && list.length > 0 && !selectedClass.value) {
      selectedClass.value = list[0].name
    }
  },
  { immediate: true },
)

const classOptions = computed(() => [
  { value: '', label: '请选择班级', disabled: true },
  ...(classes.value || []).map((c: ClassInfo) => ({ value: c.name, label: c.name })),
])

// 任务列表
const { data: tasks, isPending: loadingTasks } = useTeacherGroupTasks(selectedClass)

// 创建任务
const showCreateDialog = ref(false)
const creating = ref(false)
const newTask = ref({ class_name: '', title: '', description: '', dimensions: [''] })

function addDimension() {
  if (newTask.value.dimensions.length < 5) newTask.value.dimensions.push('')
}
function removeDimension(idx: number) {
  newTask.value.dimensions.splice(idx, 1)
}

const { mutateAsync: createTask } = useCreateGroupTask()
async function handleCreate() {
  const dims = newTask.value.dimensions.filter(Boolean)
  if (!newTask.value.class_name || !newTask.value.title || dims.length === 0) {
    toastError('请填写完整信息')
    return
  }
  try {
    creating.value = true
    await createTask({
      class_name: newTask.value.class_name,
      title: newTask.value.title,
      description: newTask.value.description || undefined,
      dimensions: dims,
    })
    toastSuccess('任务创建成功')
    showCreateDialog.value = false
    newTask.value = { class_name: selectedClass.value, title: '', description: '', dimensions: [''] }
  } catch (err) {
    toastError(getErrorMessage(err) || '创建失败')
  } finally {
    creating.value = false
  }
}

watch(showCreateDialog, (open) => {
  if (open) {
    newTask.value.class_name = selectedClass.value
  }
})

// 启动/关闭任务
const { mutateAsync: startTask } = useStartGroupTask()
const { mutateAsync: closeTask } = useCloseGroupTask()

async function handleStart(taskId: number) {
  try {
    await startTask({ taskId })
    toastSuccess('任务已启动')
  } catch (err) {
    toastError(getErrorMessage(err) || '启动失败')
  }
}

async function handleClose(taskId: number) {
  try {
    await closeTask({ taskId })
    toastSuccess('任务已结束')
  } catch (err) {
    toastError(getErrorMessage(err) || '结束失败')
  }
}

const statusMap: Record<string, { label: string; variant: 'default' | 'secondary' | 'info' | 'success' }> = {
  preparing: { label: '准备中', variant: 'secondary' },
  evaluating: { label: '互评中', variant: 'info' },
  closed: { label: '已结束', variant: 'success' },
}
</script>

<template>
  <div class="space-y-5">
    <div>
      <h1 class="text-2xl font-medium text-black">
        合作项目
      </h1>
      <p class="text-[#737373] mt-1">
        管理班级的小组合作任务
      </p>
    </div>

    <div class="flex flex-wrap items-center gap-3">
      <Select v-model="selectedClass" :options="classOptions" class="w-48" />
      <Button variant="cta" @click="showCreateDialog = true">
        <Plus class="h-4 w-4" />
        创建任务
      </Button>
    </div>

    <DataContainer
      :loading="loadingTasks"
      :has-data="(tasks || []).length > 0"
      empty-text="该班级暂无合作任务"
    >
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card
          v-for="task in tasks"
          :key="task.id"
          class="bg-white border-[#e5e5e5] p-5"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <h3 class="font-medium text-black truncate">
                {{ task.title }}
              </h3>
              <p class="text-xs text-[#a3a3a3] mt-0.5">
                {{ task.class_name }}
              </p>
            </div>
            <Badge :variant="statusMap[task.status]?.variant || 'default'">
              {{ statusMap[task.status]?.label || task.status }}
            </Badge>
          </div>
          <div class="mt-4 flex flex-col sm:flex-row gap-2">
            <Button
              v-if="task.status === 'preparing'"
              size="sm"
              @click="handleStart(task.id)"
            >
              <Play class="h-3.5 w-3.5 mr-1" />
              启动
            </Button>
            <Button
              v-if="task.status === 'evaluating'"
              size="sm"
              variant="outline"
              @click="handleClose(task.id)"
            >
              <Square class="h-3.5 w-3.5 mr-1" />
              结束
            </Button>
            <Button
              size="sm"
              variant="outline"
              @click="router.push(`/teacher/group-tasks/${task.id}/results`)"
            >
              <BarChart2 class="h-3.5 w-3.5 mr-1" />
              结果
            </Button>
            <Button
              v-if="task.status !== 'preparing'"
              size="sm"
              variant="outline"
              @click="router.push(`/teacher/group-tasks/${task.id}/score`)"
            >
              <PenLine class="h-3.5 w-3.5 mr-1" />
              评分
            </Button>
          </div>
        </Card>
      </div>
    </DataContainer>

    <Dialog
      v-model:open="showCreateDialog"
      title="创建合作任务"
    >
      <div class="space-y-3">
        <Select
          v-model="newTask.class_name"
          :options="classOptions"
          placeholder="选择班级"
        />
        <input
          v-model="newTask.title"
          placeholder="任务名称"
          class="w-full rounded-full border border-[#e5e5e5] bg-white px-3 py-2 text-sm text-black placeholder:text-[#a3a3a3] focus:outline-none focus:ring-2 focus:ring-[#3b82f6]/50"
        >
        <textarea
          v-model="newTask.description"
          placeholder="任务描述（可选）"
          rows="3"
          class="w-full rounded-xl border border-[#e5e5e5] bg-white px-3 py-2 text-sm text-black placeholder:text-[#a3a3a3] focus:outline-none focus:ring-2 focus:ring-[#3b82f6]/50"
        />
        <div class="space-y-2">
          <p class="text-sm text-[#737373]">
            评分维度
          </p>
          <div
            v-for="(_, idx) in newTask.dimensions"
            :key="idx"
            class="flex gap-2"
          >
            <input
              v-model="newTask.dimensions[idx]"
              placeholder="维度名称"
              class="flex-1 rounded-full border border-[#e5e5e5] bg-white px-3 py-2 text-sm text-black placeholder:text-[#a3a3a3] focus:outline-none focus:ring-2 focus:ring-[#3b82f6]/50"
            >
            <Button
              v-if="newTask.dimensions.length > 1"
              size="sm"
              variant="destructive"
              @click="removeDimension(idx)"
            >
              删除
            </Button>
          </div>
          <Button
            v-if="newTask.dimensions.length < 5"
            size="sm"
            variant="outline"
            @click="addDimension"
          >
            + 添加维度
          </Button>
        </div>
      </div>
      <template #footer>
        <div class="flex w-full gap-2 sm:justify-end">
          <Button
            variant="outline"
            @click="showCreateDialog = false"
          >
            取消
          </Button>
          <Button
            variant="cta"
            :loading="creating"
            @click="handleCreate"
          >
            确认创建
          </Button>
        </div>
      </template>
    </Dialog>
  </div>
</template>
