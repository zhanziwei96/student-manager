<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { Card, Button, Badge, Input, Dialog } from '@/components/ui'
import { Plus, Loader2, Pencil, CheckCircle2, Copy, CalendarRange } from 'lucide-vue-next'
import { semestersApi } from '@/api/semesters'
import { useToast } from '@/composables/useToast'
import { getErrorMessage } from '@/lib/error'
import type { Semester } from '@/types'

const { showToast } = useToast()
const queryClient = useQueryClient()

// 学期列表
const { data: semestersData, isPending } = useQuery({
  queryKey: ['semesters'],
  queryFn: () => semestersApi.list(),
})
const semesters = computed(() => semestersData.value ?? [])

const invalidateSemesters = () => queryClient.invalidateQueries({ queryKey: ['semesters'] })

// 创建
const showCreateDialog = ref(false)
const createForm = ref({ label: '', start_date: '', total_weeks: 20 })
const createError = ref('')

const openCreateDialog = () => {
  createForm.value = { label: '', start_date: '', total_weeks: 20 }
  createError.value = ''
  showCreateDialog.value = true
}

const { mutateAsync: createSemester, isPending: isCreating } = useMutation({
  mutationFn: () => semestersApi.create({
    label: createForm.value.label.trim(),
    start_date: createForm.value.start_date,
    total_weeks: createForm.value.total_weeks,
  }),
  onSuccess: () => {
    invalidateSemesters()
    showToast('学期创建成功', 'success')
    showCreateDialog.value = false
  },
  onError: (error) => showToast(getErrorMessage(error) || '创建失败', 'error'),
})

const handleCreate = async () => {
  if (!createForm.value.label.trim()) {
    createError.value = '请输入学期标识'
    return
  }
  if (!createForm.value.start_date) {
    createError.value = '请选择开学日期'
    return
  }
  await createSemester()
}

// 编辑
const showEditDialog = ref(false)
const editingSemester = ref<Semester | null>(null)
const editForm = ref({ start_date: '', total_weeks: 20 })

const openEditDialog = (sem: Semester) => {
  editingSemester.value = sem
  editForm.value = { start_date: sem.start_date, total_weeks: sem.total_weeks }
  showEditDialog.value = true
}

const { mutateAsync: updateSemester, isPending: isUpdating } = useMutation({
  mutationFn: () => semestersApi.update(editingSemester.value!.id, {
    start_date: editForm.value.start_date,
    total_weeks: editForm.value.total_weeks,
  }),
  onSuccess: () => {
    invalidateSemesters()
    showToast('学期更新成功', 'success')
    showEditDialog.value = false
  },
  onError: (error) => showToast(getErrorMessage(error) || '更新失败', 'error'),
})

// 切换当前学期
const showActivateDialog = ref(false)
const activatingSemester = ref<Semester | null>(null)

const openActivateDialog = (sem: Semester) => {
  activatingSemester.value = sem
  showActivateDialog.value = true
}

const { mutateAsync: activateSemester, isPending: isActivating } = useMutation({
  mutationFn: () => semestersApi.activate(activatingSemester.value!.id),
  onSuccess: () => {
    invalidateSemesters()
    showToast(`已切换到 ${activatingSemester.value?.label}`, 'success')
    showActivateDialog.value = false
  },
  onError: (error) => showToast(getErrorMessage(error) || '切换失败', 'error'),
})

// 学期 rollover
const showRolloverDialog = ref(false)

const { mutateAsync: rollover, isPending: isRollingOver } = useMutation({
  mutationFn: () => semestersApi.rollover(),
  onSuccess: () => {
    invalidateSemesters()
    showToast('学期数据已复制', 'success')
    showRolloverDialog.value = false
  },
  onError: (error) => showToast(getErrorMessage(error) || '复制失败', 'error'),
})
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-5">
      <div>
        <h1 class="text-2xl font-medium text-black">
          学期管理
        </h1>
        <p class="text-[#737373]">
          管理学期，切换当前学期并复制开学数据
        </p>
      </div>
      <div class="flex gap-2">
        <Button
          variant="outline"
          @click="showRolloverDialog = true"
        >
          <Copy class="mr-2 h-4 w-4" />
          复制上一学期
        </Button>
        <Button @click="openCreateDialog">
          <Plus class="mr-2 h-4 w-4" />
          创建学期
        </Button>
      </div>
    </div>

    <!-- 学期列表 -->
    <Card class="overflow-hidden p-0">
      <div
        v-if="isPending"
        class="flex h-64 items-center justify-center"
      >
        <Loader2 class="h-8 w-8 animate-spin text-primary" />
      </div>

      <table
        v-else-if="semesters.length > 0"
        class="w-full text-sm"
      >
        <thead class="bg-[#fafafa] text-[#737373] border-b border-[#e5e5e5]">
          <tr>
            <th class="px-4 py-3 text-left font-medium">
              学期
            </th>
            <th class="px-4 py-3 text-left font-medium">
              开学日期
            </th>
            <th class="px-4 py-3 text-right font-medium">
              周数
            </th>
            <th class="px-4 py-3 text-left font-medium">
              状态
            </th>
            <th class="px-4 py-3 text-right font-medium">
              操作
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-[#e5e5e5]">
          <tr
            v-for="sem in semesters"
            :key="sem.id"
            class="text-[#737373] hover:bg-[#fafafa] transition-colors"
          >
            <td class="px-4 py-3">
              <span class="font-medium text-black">{{ sem.label }}</span>
              <Badge
                v-if="sem.is_current"
                variant="success"
                class="ml-2"
              >
                当前
              </Badge>
            </td>
            <td class="px-4 py-3">
              {{ sem.start_date }}
            </td>
            <td class="px-4 py-3 text-right">
              {{ sem.total_weeks }}
            </td>
            <td class="px-4 py-3">
              <Badge :variant="sem.status === 'active' ? 'default' : 'secondary'">
                {{ sem.status === 'active' ? '进行中' : '已归档' }}
              </Badge>
            </td>
            <td class="px-4 py-3">
              <div class="flex justify-end gap-2">
                <Button
                  v-if="!sem.is_current && sem.status === 'active'"
                  variant="outline"
                  size="sm"
                  class="hover:bg-[#fafafa]"
                  @click="openActivateDialog(sem)"
                >
                  <CheckCircle2 class="mr-1 h-4 w-4" />
                  设为当前
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  class="hover:bg-[#fafafa]"
                  @click="openEditDialog(sem)"
                >
                  <Pencil class="h-4 w-4" />
                </Button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Empty state -->
      <div
        v-else
        class="flex h-64 flex-col items-center justify-center text-[#737373]"
      >
        <CalendarRange class="mb-4 h-12 w-12 opacity-50" />
        <p>暂无学期数据</p>
        <p class="mt-1 text-sm text-[#a3a3a3]">
          点击右上角按钮创建学期
        </p>
      </div>
    </Card>

    <!-- Create Dialog -->
    <Dialog
      v-model:open="showCreateDialog"
      title="创建学期"
      description="学期标识建议使用 学年-学期 格式，如 2026-2027-1"
    >
      <div class="space-y-4">
        <div>
          <label class="text-sm text-[#737373]">学期标识</label>
          <Input
            v-model="createForm.label"
            placeholder="如：2026-2027-1"
            class="mt-1"
          />
        </div>
        <div>
          <label class="text-sm text-[#737373]">开学日期</label>
          <Input
            v-model="createForm.start_date"
            type="date"
            class="mt-1"
          />
        </div>
        <div>
          <label class="text-sm text-[#737373]">总周数</label>
          <Input
            v-model.number="createForm.total_weeks"
            type="number"
            min="1"
            max="30"
            class="mt-1"
          />
        </div>
        <p
          v-if="createError"
          class="text-sm text-red-400"
        >
          {{ createError }}
        </p>
      </div>
      <template #footer>
        <Button
          variant="outline"
          @click="showCreateDialog = false"
        >
          取消
        </Button>
        <Button
          :disabled="isCreating"
          @click="handleCreate"
        >
          <Loader2
            v-if="isCreating"
            class="mr-2 h-4 w-4 animate-spin"
          />
          创建
        </Button>
      </template>
    </Dialog>

    <!-- Edit Dialog -->
    <Dialog
      v-model:open="showEditDialog"
      title="编辑学期"
      :description="`修改 '${editingSemester?.label}' 的日期与周数`"
    >
      <div class="space-y-4">
        <div>
          <label class="text-sm text-[#737373]">开学日期</label>
          <Input
            v-model="editForm.start_date"
            type="date"
            class="mt-1"
          />
        </div>
        <div>
          <label class="text-sm text-[#737373]">总周数</label>
          <Input
            v-model.number="editForm.total_weeks"
            type="number"
            min="1"
            max="30"
            class="mt-1"
          />
        </div>
      </div>
      <template #footer>
        <Button
          variant="outline"
          @click="showEditDialog = false"
        >
          取消
        </Button>
        <Button
          :disabled="isUpdating"
          @click="updateSemester()"
        >
          <Loader2
            v-if="isUpdating"
            class="mr-2 h-4 w-4 animate-spin"
          />
          保存
        </Button>
      </template>
    </Dialog>

    <!-- Activate Dialog -->
    <Dialog
      v-model:open="showActivateDialog"
      title="切换当前学期"
      :description="`确定切换到 '${activatingSemester?.label}' 吗？签到、课表与成绩数据都将按该学期口径展示。`"
    >
      <template #footer>
        <Button
          variant="outline"
          @click="showActivateDialog = false"
        >
          取消
        </Button>
        <Button
          :disabled="isActivating"
          @click="activateSemester()"
        >
          <Loader2
            v-if="isActivating"
            class="mr-2 h-4 w-4 animate-spin"
          />
          确认切换
        </Button>
      </template>
    </Dialog>

    <!-- Rollover Dialog -->
    <Dialog
      v-model:open="showRolloverDialog"
      title="复制上一学期"
      description="将上一学期的学生行政班归属、开课计划与选课名单复制到当前学期（教师默认留任）。请先创建并切换目标学期。"
    >
      <template #footer>
        <Button
          variant="outline"
          @click="showRolloverDialog = false"
        >
          取消
        </Button>
        <Button
          :disabled="isRollingOver"
          @click="rollover()"
        >
          <Loader2
            v-if="isRollingOver"
            class="mr-2 h-4 w-4 animate-spin"
          />
          开始复制
        </Button>
      </template>
    </Dialog>
  </div>
</template>
