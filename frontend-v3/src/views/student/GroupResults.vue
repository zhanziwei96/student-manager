<script setup lang="ts">
import { computed } from 'vue'
import { useMyGroupResults } from '@/features/group-collaboration'
import { JojoRadarChart } from '@/features/group-collaboration/components'
import { Card, DataContainer, Badge } from '@/components/ui'
import { Trophy } from 'lucide-vue-next'
import type { GroupTaskResult } from '@/api'

const { data: results, isPending } = useMyGroupResults()

const resultList = computed(() => {
  if (!results.value) return []
  return results.value.map((r: GroupTaskResult) => ({
    ...r,
    dimensions: Object.keys(r.final_scores || {}),
    finalValues: Object.values(r.final_scores || {}),
    groupName: r.group_name || '',
  }))
})

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
        成绩单
      </h1>
      <p class="text-[#737373] mt-1">
        查看小组在各合作项目中的评分结果
      </p>
    </div>

    <DataContainer
      :loading="isPending"
      :has-data="resultList.length > 0"
      empty-text="暂无成绩数据"
    >
      <div class="grid gap-5">
        <Card
          v-for="item in resultList"
          :key="item.task_id"
          class="bg-white border-[#e5e5e5] p-5"
        >
          <div class="flex flex-col lg:flex-row lg:items-start gap-5">
            <!-- 左侧信息 -->
            <div class="flex-1">
              <div class="flex items-start justify-between">
                <div>
                  <h3 class="text-lg font-medium text-black">
                    {{ item.title }}
                  </h3>
                  <div class="mt-1 flex items-center gap-2">
                    <Badge :variant="statusMap[item.status]?.variant || 'default'">
                      {{ statusMap[item.status]?.label || item.status }}
                    </Badge>
                    <span class="text-xs text-[#a3a3a3]">
                      总分 {{ item.task_final }}
                    </span>
                  </div>
                </div>
                <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-yellow-400/20">
                  <Trophy class="h-5 w-5 text-yellow-500" />
                </div>
              </div>

              <div class="mt-4 overflow-x-auto">
                <table class="w-full min-w-[320px] text-sm">
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
                      v-for="dim in Object.keys(item.final_scores || {})"
                      :key="dim"
                      class="border-b border-[#f5f5f5]"
                    >
                      <td class="py-2 text-black">
                        {{ dim }}
                      </td>
                      <td class="py-2 text-right">
                        {{ item.teacher_scores[dim] ?? '-' }}
                      </td>
                      <td class="py-2 text-right">
                        {{ item.peer_scores[dim] ?? '-' }}
                      </td>
                      <td class="py-2 text-right font-medium text-primary">
                        {{ item.final_scores[dim] ?? '-' }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- 右侧雷达图 -->
            <div v-if="item.dimensions.length > 0" class="w-full lg:w-80 shrink-0 h-64 sm:h-80 lg:h-96">
              <JojoRadarChart
                :dimensions="item.dimensions"
                :final-scores="item.finalValues"
                :group-name="item.groupName"
                class="h-full"
              />
            </div>
          </div>
        </Card>
      </div>
    </DataContainer>
  </div>
</template>
