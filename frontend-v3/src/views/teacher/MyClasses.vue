<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { useToast } from '@/composables'
import { Card, Button, Checkbox, DataContainer } from '@/components/ui'
import { teacherClassesApi } from '@/api/teacherClasses'
import { getErrorMessage } from '@/lib/error'

/**
 * 老师"我的班级"管理页
 *
 * 业务纠正后：老师自己决定教哪些班级。
 * - 展示全部可选班级，勾选状态表示当前负责
 * - 勾选/取消勾选后点保存，调用 PUT /teacher/classes
 */

const queryClient = useQueryClient()

// 当前老师教的班级
const { data: mineData, isPending: isMinePending, error: mineError, refetch: refetchMine } = useQuery({
  queryKey: ['teacher-classes'],
  queryFn: () => teacherClassesApi.getMine(),
})

// 全部可选班级
const { data: allData, isPending: isAllPending, error: allError, refetch: refetchAll } = useQuery({
  queryKey: ['classes'],
  queryFn: () => teacherClassesApi.getAll(),
})

// 勾选状态（初始化自当前教的班级）
const selectedClassNames = ref<string[]>([])
watch(
  mineData,
  (val) => {
    selectedClassNames.value = [...(val ?? [])]
  },
  { immediate: true }
)

const loading = computed(() => isMinePending.value || isAllPending.value)
const loadError = computed(() => (mineError.value ?? allError.value) ?? null)
const allClasses = computed(() => allData.value ?? [])

const isSaving = ref(false)

const toggleClass = (className: string, checked: boolean) => {
  if (checked) {
    selectedClassNames.value = [...selectedClassNames.value, className]
  } else {
    selectedClassNames.value = selectedClassNames.value.filter((c) => c !== className)
  }
}

const retry = () => {
  refetchMine()
  refetchAll()
}

// === Toast 状态 (队列模式) ===
const { success: showSuccessToast, error: showErrorToast } = useToast()

const handleSave = async () => {
  try {
    isSaving.value = true
    await teacherClassesApi.updateMine(selectedClassNames.value)
    await queryClient.invalidateQueries({ queryKey: ['teacher-classes'] })
    await queryClient.invalidateQueries({ queryKey: ['classes'] })
    showSuccessToast('班级列表已更新')
  } catch (err: unknown) {
    showErrorToast(getErrorMessage(err) || '保存班级失败')
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-5">
      <div>
        <h1 class="text-2xl font-medium text-black">
          我的班级
        </h1>
        <p class="text-[#737373]">
          勾选你负责的班级并保存
        </p>
      </div>
      <Button
        variant="outline"
        :loading="isSaving"
        data-testid="save-my-classes-btn"
        @click="handleSave"
      >
        保存
      </Button>
    </div>

    <!-- Data Container -->
    <DataContainer
      :loading="loading"
      :error="loadError"
      :has-data="allClasses.length > 0"
      empty-text="暂无可选班级"
      @retry="retry"
    >
      <Card class="border-[#e5e5e5] bg-white p-4">
        <div class="space-y-1">
          <div
            v-for="cls in allClasses"
            :key="cls"
            class="flex items-center gap-2 rounded-md p-2 hover:bg-[#fafafa]"
          >
            <Checkbox
              :checked="selectedClassNames.includes(cls)"
              @update:checked="(checked: boolean) => toggleClass(cls, checked)"
            />
            <span class="text-sm text-black">{{ cls }}</span>
          </div>
        </div>
      </Card>
    </DataContainer>
  </div>
</template>
