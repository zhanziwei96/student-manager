<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { Card, Button, Input, Select, Dialog } from '@/components/ui'
import { Plus, Loader2, Pencil, Trash2, School } from 'lucide-vue-next'
import { classesApi, type CreateClassRequest, type UpdateClassRequest } from '@/api/classes'
import { cohortsApi } from '@/api/cohorts'
import { useToast } from '@/composables/useToast'
import { getErrorMessage } from '@/lib/error'
import type { AdminClass } from '@/types'

const { showToast } = useToast()
const queryClient = useQueryClient()

// 届数据（创建班级与筛选共用）
const { data: cohortsData } = useQuery({
  queryKey: ['cohorts'],
  queryFn: () => cohortsApi.list(),
})
const cohorts = computed(() => cohortsData.value ?? [])
const cohortOptions = computed(() => [
  { value: '', label: '全部届' },
  ...cohorts.value.map((c) => ({ value: c.year, label: c.label })),
])

// 班级列表（按届筛选）
const cohortFilter = ref('')
const { data: classesData, isPending } = useQuery({
  queryKey: ['classes', cohortFilter],
  queryFn: () => classesApi.list(cohortFilter.value || undefined),
})
const classes = computed(() => classesData.value ?? [])

// 创建
const showCreateDialog = ref(false)
const createForm = ref({ name: '', major: '', cohort_year: '' })
const createError = ref('')

const openCreateDialog = () => {
  createForm.value = { name: '', major: '', cohort_year: '' }
  createError.value = ''
  showCreateDialog.value = true
}

const { mutateAsync: createClass, isPending: isCreating } = useMutation({
  mutationFn: (data: CreateClassRequest) => classesApi.create(data),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['classes'] })
    showToast('班级创建成功', 'success')
    showCreateDialog.value = false
  },
  onError: (error) => showToast(getErrorMessage(error) || '创建失败', 'error'),
})

const handleCreate = async () => {
  if (!createForm.value.name.trim()) {
    createError.value = '请输入班级名'
    return
  }
  if (!createForm.value.cohort_year) {
    createError.value = '请选择所属届'
    return
  }
  await createClass({
    name: createForm.value.name.trim(),
    major: createForm.value.major.trim(),
    cohort_year: createForm.value.cohort_year,
  })
}

// 编辑
const showEditDialog = ref(false)
const editingClass = ref<AdminClass | null>(null)
const editForm = ref({ name: '', major: '' })
const editError = ref('')

const openEditDialog = (cls: AdminClass) => {
  editingClass.value = cls
  editForm.value = { name: cls.name, major: cls.major }
  editError.value = ''
  showEditDialog.value = true
}

const { mutateAsync: updateClass, isPending: isUpdating } = useMutation({
  mutationFn: ({ id, data }: { id: number; data: UpdateClassRequest }) => classesApi.update(id, data),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['classes'] })
    showToast('班级更新成功', 'success')
    showEditDialog.value = false
  },
  onError: (error) => showToast(getErrorMessage(error) || '更新失败', 'error'),
})

const handleUpdate = async () => {
  if (!editingClass.value) return
  if (!editForm.value.name.trim()) {
    editError.value = '请输入班级名'
    return
  }
  await updateClass({
    id: editingClass.value.id,
    data: { name: editForm.value.name.trim(), major: editForm.value.major.trim() },
  })
}

// 删除
const showDeleteDialog = ref(false)
const deletingClass = ref<AdminClass | null>(null)

const openDeleteDialog = (cls: AdminClass) => {
  deletingClass.value = cls
  showDeleteDialog.value = true
}

const { mutateAsync: deleteClass, isPending: isDeleting } = useMutation({
  mutationFn: (id: number) => classesApi.delete(id),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['classes'] })
    showToast('班级已删除', 'success')
    showDeleteDialog.value = false
  },
  onError: (error) => showToast(getErrorMessage(error) || '删除失败', 'error'),
})
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-5">
      <div>
        <h1 class="text-2xl font-medium text-black">
          班级管理
        </h1>
        <p class="text-[#737373]">
          按届管理班级，创建后可为学生分配
        </p>
      </div>
      <Button @click="openCreateDialog">
        <Plus class="mr-2 h-4 w-4" />
        创建班级
      </Button>
    </div>

    <!-- 届筛选 -->
    <div class="mb-5 w-full sm:w-48">
      <Select
        v-model="cohortFilter"
        :options="cohortOptions"
        placeholder="选择届"
      />
    </div>

    <!-- 班级列表 -->
    <Card class="overflow-hidden p-0">
      <div
        v-if="isPending"
        class="flex h-64 items-center justify-center"
      >
        <Loader2 class="h-8 w-8 animate-spin text-primary" />
      </div>

      <table
        v-else-if="classes.length > 0"
        class="w-full text-sm"
      >
        <thead class="bg-[#fafafa] text-[#737373] border-b border-[#e5e5e5]">
          <tr>
            <th class="px-4 py-3 text-left font-medium">
              班级
            </th>
            <th class="px-4 py-3 text-left font-medium">
              专业
            </th>
            <th class="px-4 py-3 text-left font-medium">
              所属届
            </th>
            <th class="px-4 py-3 text-right font-medium">
              学生数
            </th>
            <th class="px-4 py-3 text-right font-medium">
              操作
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-[#e5e5e5]">
          <tr
            v-for="cls in classes"
            :key="cls.id"
            class="text-[#737373] hover:bg-[#fafafa] transition-colors"
          >
            <td class="px-4 py-3 font-medium text-black">
              {{ cls.name }}
            </td>
            <td class="px-4 py-3">
              {{ cls.major || '—' }}
            </td>
            <td class="px-4 py-3">
              {{ cls.cohort_year }}届
            </td>
            <td class="px-4 py-3 text-right">
              {{ cls.student_count }}
            </td>
            <td class="px-4 py-3">
              <div class="flex justify-end gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  class="hover:bg-[#fafafa]"
                  @click="openEditDialog(cls)"
                >
                  <Pencil class="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  class="hover:bg-red-500/10"
                  @click="openDeleteDialog(cls)"
                >
                  <Trash2 class="h-4 w-4 text-[#ef4444]" />
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
        <School class="mb-4 h-12 w-12 opacity-50" />
        <p>暂无班级数据</p>
        <p class="mt-1 text-sm text-[#a3a3a3]">
          点击右上角按钮创建班级
        </p>
      </div>
    </Card>

    <!-- Create Dialog -->
    <Dialog
      v-model:open="showCreateDialog"
      title="创建班级"
      description="新班级属于指定的届"
    >
      <div class="space-y-4">
        <div>
          <label class="text-sm text-[#737373]">所属届</label>
          <Select
            v-model="createForm.cohort_year"
            :options="cohorts.map((c) => ({ value: c.year, label: c.label }))"
            placeholder="选择届"
            class="mt-1"
          />
        </div>
        <div>
          <label class="text-sm text-[#737373]">班级名</label>
          <Input
            v-model="createForm.name"
            placeholder="如：1班"
            class="mt-1"
          />
        </div>
        <div>
          <label class="text-sm text-[#737373]">专业</label>
          <Input
            v-model="createForm.major"
            placeholder="如：计算机科学与技术（可留空）"
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
      title="编辑班级"
      :description="`修改 '${editingClass?.display_name}' 的信息`"
    >
      <div class="space-y-4">
        <div>
          <label class="text-sm text-[#737373]">班级名</label>
          <Input
            v-model="editForm.name"
            placeholder="如：1班"
            class="mt-1"
          />
        </div>
        <div>
          <label class="text-sm text-[#737373]">专业</label>
          <Input
            v-model="editForm.major"
            placeholder="如：计算机科学与技术（可留空）"
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

    <!-- Delete Dialog -->
    <Dialog
      v-model:open="showDeleteDialog"
      title="删除班级"
      :description="`确定要删除 '${deletingClass?.display_name}' 吗？班下有学生时将无法删除。`"
    >
      <template #footer>
        <Button
          variant="outline"
          @click="showDeleteDialog = false"
        >
          取消
        </Button>
        <Button
          variant="destructive"
          :disabled="isDeleting"
          @click="deletingClass && deleteClass(deletingClass.id)"
        >
          <Loader2
            v-if="isDeleting"
            class="mr-2 h-4 w-4 animate-spin"
          />
          删除
        </Button>
      </template>
    </Dialog>
  </div>
</template>
