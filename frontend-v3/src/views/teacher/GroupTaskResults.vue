<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTaskResults } from '@/features/group-collaboration'
import { JojoRadarChart } from '@/features/group-collaboration/components'
import { Card, DataContainer, Badge } from '@/components/ui'
import { ArrowLeft } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const taskId = computed(() => Number(route.params.id))
const { data, isPending, error } = useTaskResults(taskId.value)

const resultsList = computed(() => {
  if (!data.value?.results) return []
  return Object.values(data.value.results).map((r: any) => ({
    groupId: r.group_id,
    groupName: r.group_name,
    teacherScores: r.teacher_scores,
    peerScores: r.peer_scores,
    finalScores: r.final_scores,
    taskFinal: r.task_final,
  }))
})

const dimensions = computed(() =>
  (data.value?.dimensions || []).map((d: any) =>
    typeof d === 'string' ? d : d.name
  )
)
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
          任务结果
        </h1>
        <p class="text-[#737373] text-sm">
          {{ data?.task?.title || '加载中...' }}
        </p>
      </div>
    </div>

    <DataContainer
      :loading="isPending"
      :error="error"
      :has-data="resultsList.length > 0"
      empty-text="暂无结果数据"
    >
      <div class="space-y-4">
        <Card
          v-for="item in resultsList"
          :key="item.groupId"
          class="bg-white border-[#e5e5e5] p-5"
        >
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
            <h3 class="font-medium text-black">
              {{ item.groupName }}
            </h3>
            <Badge variant="info">
              总分 {{ item.taskFinal }}
            </Badge>
          </div>

          <!-- 雷达图 -->
          <JojoRadarChart
            :dimensions="dimensions"
            :final-scores="dimensions.map((d) => item.finalScores[d] ?? 0)"
            :group-name="item.groupName"
            class="mb-4 h-64 sm:h-80 lg:h-96"
          />

          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-[#e5e5e5] text-[#737373]">
                  <th class="py-2 text-left font-medium">
                    维度
                  </th>
                  <th class="py-2 text-right font-medium">
                    教师评分
                  </th>
                  <th class="py-2 text-right font-medium">
                    同伴评分
                  </th>
                  <th class="py-2 text-right font-medium">
                    最终得分
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="dim in dimensions"
                  :key="dim"
                  class="border-b border-[#f5f5f5]"
                >
                  <td class="py-2 text-black">
                    {{ dim }}
                  </td>
                  <td class="py-2 text-right">
                    {{ item.teacherScores[dim] ?? '-' }}
                  </td>
                  <td class="py-2 text-right">
                    {{ item.peerScores[dim] ?? '-' }}
                  </td>
                  <td class="py-2 text-right font-medium text-primary">
                    {{ item.finalScores[dim] ?? '-' }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </DataContainer>
  </div>
</template>
