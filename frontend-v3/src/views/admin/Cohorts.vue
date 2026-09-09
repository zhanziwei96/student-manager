<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { Card, Button, Badge, Input, Dialog } from '@/components/ui'
import { Plus, Loader2, GraduationCap, RotateCcw, Layers } from 'lucide-vue-next'
import { cohortsApi } from '@/api/cohorts'
import { useToast } from '@/composables/useToast'
import { getErrorMessage } from '@/lib/error'
import type { Cohort } from '@/types'

const { showToast } = useToast()
const queryClient = useQueryClient()

// 届列表
const { data: cohortsData, isPending } = useQuery({
  queryKey: ['cohorts'],
  queryFn: () => cohortsApi.list(),
})
const cohorts = computed(() => cohortsData.value ?? [])

const invalidateCohorts = () => queryClient.invalidateQueries({ queryKey: ['cohorts'] })

// 创建
const showCreateDialog = ref(false)
const createForm = ref({ year: '', label: '' })
const createError = ref('')

const openCreateDialog = () => {
  createForm.value = { year: '', label: '' }
  createError.value = ''
  showCreateDialog.value = true
}

const { mutateAsync: createCohort, isPending: isCreating } = useMutation({
  mutationFn: () => cohortsApi.create({
    year: createForm.value.year.trim(),
    label: createForm.value.label.trim() || undefined,
  }),
  onSuccess: () => {
    invalidateCohorts()
    showToast('届创建成功', 'success')
    showCreateDialog.value = false
  },
  onError: (error) => showToast(getErrorMessage(error) || '创建失败', 'error'),
})

const handleCreate = async () => {
  if (!createForm.value.year.trim()) {
    createError.value = '请输入届（入学年份）'
    return
  }
  await createCohort()
}

// 毕业归档 / 恢复
const showArchiveDialog = ref(false)
const archivingCohort = ref<Cohort | null>(null)

const openArchiveDialog = (cohort: Cohort) => {
  archivingCohort.value = cohort
  showArchiveDialog.value = true
}

const { mutateAsync: setGraduated, isPending: isArchiving } = useMutation({
  mutationFn: () => cohortsApi.update(archivingCohort.value!.year, { status: 'graduated' }),
  onSuccess: () => {
    invalidateCohorts()
    showToast(`${archivingCohort.value?.label} 已归档`, 'success')
    showArchiveDialog.value = false
  },
  onError: (error) => showToast(getErrorMessage(error) || '归档失败', 'error'),
})

const { mutateAsync: restoreCohort, isPending: isRestoring } = useMutation({
  mutationFn: (year: string) => cohortsApi.update(year, { status: 'active' }),
  onSuccess: () => {
    invalidateCohorts()
    showToast('届已恢复', 'success')
  },
  onError: (error) => showToast(getErrorMessage(error) || '恢复失败', 'error'),
})
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-5">
      <div>
        <h1 class="text-2xl font-medium text-black">
          届管理
        </h1>
        <p class="text-[#737373]">
          按入学年份管理届，毕业时归档
        </p>
      </div>
      <Button @click="openCreateDialog">
        <Plus class="mr-2 h-4 w-4" />
        创建届
      </Button>
    </div>

    <!-- 届列表 -->
    <Card class="overflow-hidden p-0">
      <div
        v-if="isPending"
        class="flex h-64 items-center justify-center"
      >
        <Loader2 class="h-8 w-8 animate-spin text-primary" />
      </div>

      <table
        v-else-if="cohorts.length > 0"
        class="w-full text-sm"
      >
        <thead class="bg-[#fafafa] text-[#737373] border-b border-[#e5e5e5]">
          <tr>
            <th class="px-4 py-3 text-left font-medium">
              届
            </th>
            <th class="px-4 py-3 text-left font-medium">
              显示名
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
            v-for="cohort in cohorts"
            :key="cohort.year"
            class="text-[#737373] hover:bg-[#fafafa] transition-colors"
          >
            <td class="px-4 py-3 font-medium text-black">
              {{ cohort.year }}
            </td>
            <td class="px-4 py-3">
              {{ cohort.label }}
            </td>
            <td class="px-4 py-3">
              <Badge :variant="cohort.status === 'active' ? 'default' : 'secondary'">
                {{ cohort.status === 'active' ? '在读' : '已毕业' }}
              </Badge>
            </td>
            <td class="px-4 py-3">
              <div class="flex justify-end">
                <Button
                  v-if="cohort.status === 'active'"
                  variant="outline"
                  size="sm"
                  class="hover:bg-[#fafafa]"
                  @click="openArchiveDialog(cohort)"
                >
                  <GraduationCap class="mr-1 h-4 w-4" />
                  毕业归档
                </Button>
                <Button
                  v-else
                  variant="outline"
                  size="sm"
                  class="hover:bg-[#fafafa]"
                  @click="restoreCohort(cohort.year)"
                >
                  <RotateCcw
                    v-if="!isRestoring"
                    class="mr-1 h-4 w-4"
                  />
                  <Loader2
                    v-else
                    class="mr-1 h-4 w-4 animate-spin"
                  />
                  恢复
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
        <Layers class="mb-4 h-12 w-12 opacity-50" />
        <p>暂无届数据</p>
        <p class="mt-1 text-sm text-[#a3a3a3]">
          点击右上角按钮创建届
        </p>
      </div>
    </Card>

    <!-- Create Dialog -->
    <Dialog
      v-model:open="showCreateDialog"
      title="创建届"
      description="届以入学年份标识，如 2026"
    >
      <div class="space-y-4">
        <div>
          <label class="text-sm text-[#737373]">入学年份</label>
          <Input
            v-model="createForm.year"
            placeholder="如：2026"
            class="mt-1"
          />
        </div>
        <div>
          <label class="text-sm text-[#737373]">显示名</label>
          <Input
            v-model="createForm.label"
            placeholder="如：2026届（可留空，默认 年份届）"
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

    <!-- Archive Dialog -->
    <Dialog
      v-model:open="showArchiveDialog"
      title="毕业归档"
      :description="`确定将 '${archivingCohort?.label}' 标记为已毕业吗？归档后可在列表恢复。`"
    >
      <template #footer>
        <Button
          variant="outline"
          @click="showArchiveDialog = false"
        >
          取消
        </Button>
        <Button
          variant="destructive"
          :disabled="isArchiving"
          @click="setGraduated()"
        >
          <Loader2
            v-if="isArchiving"
            class="mr-2 h-4 w-4 animate-spin"
          />
          归档
        </Button>
      </template>
    </Dialog>
  </div>
</template>
