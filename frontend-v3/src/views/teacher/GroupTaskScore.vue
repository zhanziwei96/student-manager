<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTaskResults, useSubmitTeacherScore } from '@/features/group-collaboration'
import { Card, Button, Select, DataContainer } from '@/components/ui'
import { useToast } from '@/composables'
import { ArrowLeft } from 'lucide-vue-next'
import { getErrorMessage } from '@/lib/error'
import type { TaskResultItem } from '@/api'

const route = useRoute()
const router = useRouter()
const { success: toastSuccess, error: toastError } = useToast()

const taskId = computed(() => Number(route.params.id))
const { data, isPending } = useTaskResults(taskId.value)

const groups = computed(() => {
  if (!data.value?.results) return []
  return Object.values(data.value.results).map((r: TaskResultItem) => ({
    id: r.group_id,
    name: r.group_name,
  }))
})

const dimensions = computed(() => {
  if (!data.value?.dimensions) return []
  return data.value.dimensions.map((d) =>
    typeof d === 'string' ? { id: 0, name: d } : { id: d.id, name: d.name }
  )
})

const selectedGroupId = ref('')
watch(groups, (list) => {
  if (list.length > 0 && !selectedGroupId.value) {
    selectedGroupId.value = String(list[0].id)
  }
})

const scores = ref<Record<string, number>>({})

watch([selectedGroupId, dimensions], () => {
  scores.value = {}
  dimensions.value.forEach((d) => {
    scores.value[d.id] = 0
  })
}, { immediate: true })

const { mutateAsync: submit } = useSubmitTeacherScore()
const submitting = ref(false)

async function handleSubmit() {
  if (!selectedGroupId.value) return
  const groupId = Number(selectedGroupId.value)
  try {
    submitting.value = true
    for (const dim of dimensions.value) {
      const score = scores.value[dim.id]
      if (score == null || score < 0 || score > 100) {
        toastError(`维度 "${dim.name}" 的分数需在 0-100 之间`)
        return
      }
      await submit({
        taskId: taskId.value,
        data: {
          target_group_id: groupId,
          dimension_id: dim.id,
          score,
        },
      })
    }
    toastSuccess('评分已保存')
  } catch (err) {
    toastError(getErrorMessage(err) || '评分失败')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="space-y-5">
    <div class="flex items-center gap-3">
      <button
        class="p-2 rounded-full hover:bg-[#f5f5f5] text-[#737373]"
        @click="router.back()"
      >
        <ArrowLeft class="h-5 w-5" />
      </button>
      <div>
        <h1 class="text-2xl font-medium text-black">
          教师评分
        </h1>
        <p class="text-[#737373] text-sm">
          {{ data?.task?.title || '加载中...' }}
        </p>
      </div>
    </div>

    <DataContainer
      :loading="isPending"
      :has-data="groups.length > 0"
      empty-text="无可评分小组"
    >
      <Card class="bg-white border-[#e5e5e5] p-5">
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-black mb-1">
              评分对象
            </label>
            <Select
              v-model="selectedGroupId"
              :options="groups.map(g => ({ value: String(g.id), label: g.name }))"
              class="w-full sm:w-64"
            />
          </div>

          <div class="space-y-3">
            <div
              v-for="dim in dimensions"
              :key="dim.id"
              class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 sm:gap-4"
            >
              <label class="text-sm text-[#737373]">
                {{ dim.name }}
              </label>
              <input
                v-model.number="scores[dim.id]"
                type="number"
                min="0"
                max="100"
                class="w-full sm:w-24 rounded-full border border-[#e5e5e5] bg-white px-3 py-2 text-sm text-black text-right focus:outline-none focus:ring-2 focus:ring-[#3b82f6]/50"
              >
            </div>
          </div>

          <div class="pt-4 border-t border-[#e5e5e5] flex justify-end">
            <Button
              variant="cta"
              :loading="submitting"
              @click="handleSubmit"
            >
              提交评分
            </Button>
          </div>
        </div>
      </Card>
    </DataContainer>
  </div>
</template>
