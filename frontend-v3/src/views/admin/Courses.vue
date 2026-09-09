<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { Card, Button, Badge, Input, Dialog } from '@/components/ui'
import { Plus, Loader2, Pencil, Archive, Library } from 'lucide-vue-next'
import { coursesApi } from '@/api/courses'
import { useToast } from '@/composables/useToast'
import { getErrorMessage } from '@/lib/error'
import type { Course } from '@/types'

const { showToast } = useToast()
const queryClient = useQueryClient()

// 课程目录
const { data: coursesData, isPending } = useQuery({
  queryKey: ['courses'],
  queryFn: () => coursesApi.list(),
})
const courses = computed(() => coursesData.value ?? [])

const invalidateCourses = () => queryClient.invalidateQueries({ queryKey: ['courses'] })

// 创建
const showCreateDialog = ref(false)
const createForm = ref({ code: '', name: '', department: '' })
const createError = ref('')

const openCreateDialog = () => {
  createForm.value = { code: '', name: '', department: '' }
  createError.value = ''
  showCreateDialog.value = true
}

const { mutateAsync: createCourse, isPending: isCreating } = useMutation({
  mutationFn: () => coursesApi.create({
    code: createForm.value.code.trim(),
    name: createForm.value.name.trim(),
    department: createForm.value.department.trim(),
  }),
  onSuccess: () => {
    invalidateCourses()
    showToast('课程创建成功', 'success')
    showCreateDialog.value = false
  },
  onError: (error) => showToast(getErrorMessage(error) || '创建失败', 'error'),
})

const handleCreate = async () => {
  if (!createForm.value.code.trim()) {
    createError.value = '请输入课程编码'
    return
  }
  if (!createForm.value.name.trim()) {
    createError.value = '请输入课程名称'
    return
  }
  await createCourse()
}

// 编辑
const showEditDialog = ref(false)
const editingCourse = ref<Course | null>(null)
const editForm = ref({ name: '', department: '' })

const openEditDialog = (course: Course) => {
  editingCourse.value = course
  editForm.value = { name: course.name, department: course.department }
  showEditDialog.value = true
}

const { mutateAsync: updateCourse, isPending: isUpdating } = useMutation({
  mutationFn: () => coursesApi.update(editingCourse.value!.id, {
    name: editForm.value.name.trim(),
    department: editForm.value.department.trim(),
  }),
  onSuccess: () => {
    invalidateCourses()
    showToast('课程更新成功', 'success')
    showEditDialog.value = false
  },
  onError: (error) => showToast(getErrorMessage(error) || '更新失败', 'error'),
})

// 归档 / 恢复
const { mutateAsync: setArchived, isPending: isArchiving } = useMutation({
  mutationFn: (course: Course) => coursesApi.update(course.id, {
    status: course.status === 'active' ? 'archived' : 'active',
  }),
  onSuccess: () => {
    invalidateCourses()
    showToast('课程状态已更新', 'success')
  },
  onError: (error) => showToast(getErrorMessage(error) || '操作失败', 'error'),
})
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-5">
      <div>
        <h1 class="text-2xl font-medium text-black">
          课程管理
        </h1>
        <p class="text-[#737373]">
          维护课程目录，教学班开课时选用
        </p>
      </div>
      <Button @click="openCreateDialog">
        <Plus class="mr-2 h-4 w-4" />
        创建课程
      </Button>
    </div>

    <!-- 课程列表 -->
    <Card class="overflow-hidden p-0">
      <div
        v-if="isPending"
        class="flex h-64 items-center justify-center"
      >
        <Loader2 class="h-8 w-8 animate-spin text-primary" />
      </div>

      <table
        v-else-if="courses.length > 0"
        class="w-full text-sm"
      >
        <thead class="bg-[#fafafa] text-[#737373] border-b border-[#e5e5e5]">
          <tr>
            <th class="px-4 py-3 text-left font-medium">
              编码
            </th>
            <th class="px-4 py-3 text-left font-medium">
              课程名称
            </th>
            <th class="px-4 py-3 text-left font-medium">
              开课院系
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
            v-for="course in courses"
            :key="course.id"
            class="text-[#737373] hover:bg-[#fafafa] transition-colors"
          >
            <td class="px-4 py-3 font-mono text-xs">
              {{ course.code }}
            </td>
            <td class="px-4 py-3 font-medium text-black">
              {{ course.name }}
            </td>
            <td class="px-4 py-3">
              {{ course.department || '—' }}
            </td>
            <td class="px-4 py-3">
              <Badge :variant="course.status === 'active' ? 'default' : 'secondary'">
                {{ course.status === 'active' ? '启用' : '已归档' }}
              </Badge>
            </td>
            <td class="px-4 py-3">
              <div class="flex justify-end gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  class="hover:bg-[#fafafa]"
                  @click="openEditDialog(course)"
                >
                  <Pencil class="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  :disabled="isArchiving"
                  class="hover:bg-[#fafafa]"
                  @click="setArchived(course)"
                >
                  <Archive class="h-4 w-4" />
                  {{ course.status === 'active' ? '归档' : '恢复' }}
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
        <Library class="mb-4 h-12 w-12 opacity-50" />
        <p>暂无课程数据</p>
        <p class="mt-1 text-sm text-[#a3a3a3]">
          点击右上角按钮创建课程
        </p>
      </div>
    </Card>

    <!-- Create Dialog -->
    <Dialog
      v-model:open="showCreateDialog"
      title="创建课程"
      description="课程编码建议使用院系缩写+序号，如 MATH1001"
    >
      <div class="space-y-4">
        <div>
          <label class="text-sm text-[#737373]">课程编码</label>
          <Input
            v-model="createForm.code"
            placeholder="如：MATH1001"
            class="mt-1"
          />
        </div>
        <div>
          <label class="text-sm text-[#737373]">课程名称</label>
          <Input
            v-model="createForm.name"
            placeholder="如：高等数学"
            class="mt-1"
          />
        </div>
        <div>
          <label class="text-sm text-[#737373]">开课院系</label>
          <Input
            v-model="createForm.department"
            placeholder="如：数学学院（可留空）"
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
      title="编辑课程"
      :description="`修改 '${editingCourse?.name}' 的信息`"
    >
      <div class="space-y-4">
        <div>
          <label class="text-sm text-[#737373]">课程名称</label>
          <Input
            v-model="editForm.name"
            placeholder="如：高等数学"
            class="mt-1"
          />
        </div>
        <div>
          <label class="text-sm text-[#737373]">开课院系</label>
          <Input
            v-model="editForm.department"
            placeholder="如：数学学院（可留空）"
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
          @click="updateCourse()"
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
