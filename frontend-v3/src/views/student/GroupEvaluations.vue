<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useStudentGroupTasks, useEvaluations, useSubmitStudentScores } from '@/features/group-collaboration'
import { Card, Button, Select, DataContainer, Badge } from '@/components/ui'
import { useToast } from '@/composables'
import { CheckCircle2, Circle } from 'lucide-vue-next'
import { getErrorMessage } from '@/lib/error'

const { success: toastSuccess, error: toastError } = useToast()

const { data: tasks, isPending: loadingTasks } = useStudentGroupTasks()
const selectedTaskId = ref('')

watch(
  () => tasks.value,
  (list) => {
    if (list && list.length > 0 && !selectedTaskId.value) {
      selectedTaskId.value = String(list[0].id)
    }
  },
  { immediate: true },
)

const taskOptions = computed(() => [
  { value: '', label: '请选择任务', disabled: true },
  ...(tasks.value || []).map((t) => ({ value: String(t.id), label: t.title })),
])

const currentTaskId = computed(() => Number(selectedTaskId.value) || 0)
const { data: evaluations, isPending: loadingEvaluations } = useEvaluations(currentTaskId)

const isLoading = computed(() =>
  loadingTasks.value || (currentTaskId.value > 0 && loadingEvaluations.value),
)

// 本地分数状态
const localScores = ref<Record<number, Record<number, number>>>({})

watch(
  () => evaluations.value,
  (list) => {
    if (!list) return
    const next: Record<number, Record<number, number>> = {}
    list.forEach((target) => {
      next[target.target_group_id] = {}
      target.dimensions.forEach((d) => {
        next[target.target_group_id][d.id] = 0
      })
    })
    localScores.value = next
  },
  { immediate: true },
)

const { mutateAsync: submitScores, isPending: submitting } = useSubmitStudentScores()

async function handleSubmit(targetGroupId: number) {
  const dims = evaluations.value?.find((e) => e.target_group_id === targetGroupId)?.dimensions
  if (!dims) return

  const scores = dims.map((d) => {
    const score = localScores.value[targetGroupId]?.[d.id] ?? 0
    return { dimension_id: d.id, score: Number(score) }
  })

  for (const s of scores) {
    if (s.score < 0 || s.score > 100) {
      toastError('分数需在 0-100 之间')
      return
    }
  }

  try {
    await submitScores({
      taskId: currentTaskId.value,
      data: { target_group_id: targetGroupId, scores },
    })
    toastSuccess('评分已提交')
  } catch (err) {
    toastError(getErrorMessage(err) || '提交失败')
  }
}
</script>

<template>
  <div class="space-y-5">
    <div>
      <h1 class="text-2xl font-medium text-black">
        组间互评
      </h1>
      <p class="text-[#737373] mt-1">
        为分配给你的小组进行多维度评分
      </p>
    </div>

    <div class="flex items-center gap-3">
      <Select v-model="selectedTaskId" :options="taskOptions" class="w-full sm:w-64" />
    </div>

    <DataContainer
      :loading="isLoading"
      :has-data="(tasks?.length || 0) > 0 && (evaluations || []).length > 0"
      :empty-text="(tasks?.length || 0) === 0 ? '暂无任务' : '当前任务无互评对象'"
    >
      <div class="grid gap-4">
        <Card
          v-for="target in evaluations"
          :key="target.target_group_id"
          class="bg-white border-[#e5e5e5] p-5"
        >
          <div class="flex items-start justify-between mb-4">
            <div>
              <h3 class="font-medium text-black">
                {{ target.target_group_name }}
              </h3>
            </div>
            <Badge v-if="target.all_scored" variant="success">
              <CheckCircle2 class="h-3.5 w-3.5 mr-1" />
              已完成
            </Badge>
            <Badge v-else variant="secondary">
              <Circle class="h-3.5 w-3.5 mr-1" />
              待评分
            </Badge>
          </div>

          <div class="space-y-3">
            <div
              v-for="dim in target.dimensions"
              :key="dim.id"
              class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 sm:gap-4"
            >
              <div class="flex items-center gap-2">
                <span class="text-sm text-[#737373]">
                  {{ dim.name }}
                </span>
                <Badge v-if="dim.scored" variant="success" class="text-[10px]">已评</Badge>
              </div>
              <input
                v-model.number="localScores[target.target_group_id][dim.id]"
                type="number"
                min="0"
                max="100"
                :disabled="dim.scored"
                class="w-full sm:w-24 rounded-full border border-[#e5e5e5] bg-white px-3 py-2 text-sm text-black text-right focus:outline-none focus:ring-2 focus:ring-[#3b82f6]/50 disabled:bg-[#fafafa] disabled:text-[#a3a3a3]"
              >
            </div>
          </div>

          <div class="mt-4 pt-4 border-t border-[#e5e5e5] flex justify-end">
            <Button
              variant="cta"
              :loading="submitting"
              :disabled="target.all_scored"
              @click="handleSubmit(target.target_group_id)"
            >
              提交评分
            </Button>
          </div>
        </Card>
      </div>
    </DataContainer>
  </div>
</template>
