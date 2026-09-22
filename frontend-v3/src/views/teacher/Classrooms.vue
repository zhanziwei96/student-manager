<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { Card, Button, Badge, Input, Dialog } from '@/components/ui'
import { Plus, Loader2, Pencil, Armchair } from 'lucide-vue-next'
import { classroomsApi } from '@/api/seats'
import { useToast } from '@/composables/useToast'
import { getErrorMessage } from '@/lib/error'
import { ApiError } from '@/lib/api'
import type { ClassroomInfo } from '@/types/seats'

const { showToast } = useToast()
const queryClient = useQueryClient()

// 教室列表
const { data: classroomsData, isPending } = useQuery({
  queryKey: ['classrooms'],
  queryFn: () => classroomsApi.list(),
})
const classrooms = computed(() => classroomsData.value ?? [])

const invalidateClassrooms = () => queryClient.invalidateQueries({ queryKey: ['classrooms'] })

// 新建
const showCreateDialog = ref(false)
const createForm = ref({ name: '', rows: 6, cols: 8 })
const createError = ref('')

const openCreateDialog = () => {
  createForm.value = { name: '', rows: 6, cols: 8 }
  createError.value = ''
  showCreateDialog.value = true
}

const { mutateAsync: createClassroom, isPending: isCreating } = useMutation({
  mutationFn: () => classroomsApi.create({
    name: createForm.value.name.trim(),
    rows: createForm.value.rows,
    cols: createForm.value.cols,
  }),
})

const handleCreate = async () => {
  if (!createForm.value.name.trim()) {
    createError.value = '请输入教室名称'
    return
  }
  try {
    await createClassroom()
    await invalidateClassrooms()
    showToast('教室创建成功', 'success')
    showCreateDialog.value = false
  } catch (error) {
    showToast(getErrorMessage(error) || '创建失败', 'error')
  }
}

// 编辑布局
const showEditDialog = ref(false)
const editingClassroom = ref<ClassroomInfo | null>(null)
const editForm = ref({ name: '', rows: 6, cols: 8 })
const editError = ref('')

const openEditDialog = (room: ClassroomInfo) => {
  editingClassroom.value = room
  editForm.value = { name: room.name, rows: room.rows, cols: room.cols }
  editError.value = ''
  showEditDialog.value = true
}

const { mutateAsync: updateClassroom, isPending: isUpdating } = useMutation({
  mutationFn: () => classroomsApi.update(editingClassroom.value!.id, {
    name: editForm.value.name.trim(),
    rows: editForm.value.rows,
    cols: editForm.value.cols,
  }),
})

/** 409 布局冲突：data.removed_seat_nos 是座位编号数组，展示给用户 */
const layoutConflictMessage = (error: unknown): string | null => {
  if (error instanceof ApiError && error.statusCode === 409) {
    const removed = (error.data as { data?: { removed_seat_nos?: string[] } } | undefined)
      ?.data?.removed_seat_nos
    if (removed && removed.length > 0) {
      return `无法缩小布局：座位 ${removed.join('、')} 已有分配或故障标记，请先处理`
    }
  }
  return null
}

const handleUpdate = async () => {
  if (!editForm.value.name.trim()) {
    editError.value = '请输入教室名称'
    return
  }
  try {
    await updateClassroom()
    await invalidateClassrooms()
    showToast('教室更新成功', 'success')
    showEditDialog.value = false
  } catch (error) {
    // 布局冲突留在弹窗内展示（用户需据此调整行列），其他错误走 toast
    editError.value = layoutConflictMessage(error) ?? ''
    if (!editError.value) {
      showToast(getErrorMessage(error) || '更新失败', 'error')
    }
  }
}
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-5">
      <div>
        <h1 class="text-2xl font-medium text-black">
          教室管理
        </h1>
        <p class="text-[#737373]">
          管理座位图教室，配置座位布局
        </p>
      </div>
      <Button @click="openCreateDialog">
        <Plus class="mr-2 h-4 w-4" />
        新建教室
      </Button>
    </div>

    <!-- 教室列表 -->
    <Card class="overflow-hidden p-0">
      <div
        v-if="isPending"
        class="flex h-64 items-center justify-center"
      >
        <Loader2 class="h-8 w-8 animate-spin text-primary" />
      </div>

      <table
        v-else-if="classrooms.length > 0"
        class="w-full text-sm"
      >
        <thead class="bg-[#fafafa] text-[#737373] border-b border-[#e5e5e5]">
          <tr>
            <th class="px-4 py-3 text-left font-medium">
              教室
            </th>
            <th class="px-4 py-3 text-left font-medium">
              布局
            </th>
            <th class="px-4 py-3 text-left font-medium">
              座位数
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
            v-for="room in classrooms"
            :key="room.id"
            class="text-[#737373] hover:bg-[#fafafa] transition-colors"
          >
            <td class="px-4 py-3">
              <span class="font-medium text-black">{{ room.name }}</span>
            </td>
            <td class="px-4 py-3">
              {{ room.rows }}×{{ room.cols }}
            </td>
            <td class="px-4 py-3">
              {{ room.seat_count }} 个座位
            </td>
            <td class="px-4 py-3">
              <Badge :variant="room.status === 'active' ? 'default' : 'secondary'">
                {{ room.status === 'active' ? '启用' : '已归档' }}
              </Badge>
            </td>
            <td class="px-4 py-3">
              <div class="flex justify-end gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  class="hover:bg-[#fafafa]"
                  @click="openEditDialog(room)"
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
        <Armchair class="mb-4 h-12 w-12 opacity-50" />
        <p>暂无教室</p>
        <p class="mt-1 text-sm text-[#a3a3a3]">
          点击右上角按钮新建教室
        </p>
      </div>
    </Card>

    <!-- Create Dialog -->
    <Dialog
      v-model:open="showCreateDialog"
      title="新建教室"
      description="创建后按排×列自动生成座位网格"
    >
      <div class="space-y-4">
        <div>
          <label class="text-sm text-[#737373]">教室名称</label>
          <Input
            v-model="createForm.name"
            placeholder="如：机房301"
            class="mt-1"
          />
        </div>
        <div>
          <label class="text-sm text-[#737373]">排数</label>
          <Input
            v-model.number="createForm.rows"
            type="number"
            min="1"
            max="50"
            class="mt-1"
          />
        </div>
        <div>
          <label class="text-sm text-[#737373]">列数</label>
          <Input
            v-model.number="createForm.cols"
            type="number"
            min="1"
            max="50"
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
      title="编辑教室"
      :description="`修改 '${editingClassroom?.name}' 的名称与布局；缩小布局会删除超出范围的座位`"
    >
      <div class="space-y-4">
        <div>
          <label class="text-sm text-[#737373]">教室名称</label>
          <Input
            v-model="editForm.name"
            class="mt-1"
          />
        </div>
        <div>
          <label class="text-sm text-[#737373]">排数</label>
          <Input
            v-model.number="editForm.rows"
            type="number"
            min="1"
            max="50"
            class="mt-1"
          />
        </div>
        <div>
          <label class="text-sm text-[#737373]">列数</label>
          <Input
            v-model.number="editForm.cols"
            type="number"
            min="1"
            max="50"
            class="mt-1"
          />
        </div>
        <p
          v-if="editError"
          class="text-sm text-red-400"
        >
          {{ editError }}
        </p>
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
          @click="handleUpdate"
        >
          <Loader2
            v-if="isUpdating"
            class="mr-2 h-4 w-4 animate-spin"
          />
          保存
        </Button>
      </template>
    </Dialog>
  </div>
</template>
