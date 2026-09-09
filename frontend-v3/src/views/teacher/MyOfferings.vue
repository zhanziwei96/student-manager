<script setup lang="ts">
import { computed } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { useRouter } from 'vue-router'
import { Card, Button, Badge } from '@/components/ui'
import { Loader2, ClipboardList, Trophy, Presentation } from 'lucide-vue-next'
import { offeringsApi } from '@/api/offerings'

const router = useRouter()

// 我的教学班（本学期本人授课）
const { data: offeringsData, isPending } = useQuery({
  queryKey: ['teacher-offerings'],
  queryFn: () => offeringsApi.listMine(),
})
const offerings = computed(() => offeringsData.value ?? [])

const goGrades = (offeringId: number) => {
  router.push(`/teacher/offerings/${offeringId}/grades`)
}

const goRankings = (courseId: number) => {
  router.push({ path: '/teacher/rankings', query: { course_id: String(courseId) } })
}
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-5">
      <div>
        <h1 class="text-2xl font-medium text-black">
          我的教学班
        </h1>
        <p class="text-[#737373]">
          本学期授课任务与成绩管理
        </p>
      </div>
    </div>

    <!-- 教学班列表 -->
    <Card class="overflow-hidden p-0">
      <div
        v-if="isPending"
        class="flex h-64 items-center justify-center"
      >
        <Loader2 class="h-8 w-8 animate-spin text-primary" />
      </div>

      <table
        v-else-if="offerings.length > 0"
        class="w-full text-sm"
      >
        <thead class="bg-[#fafafa] text-[#737373] border-b border-[#e5e5e5]">
          <tr>
            <th class="px-4 py-3 text-left font-medium">
              课程
            </th>
            <th class="px-4 py-3 text-left font-medium">
              面向范围
            </th>
            <th class="px-4 py-3 text-right font-medium">
              选课人数
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
            v-for="offering in offerings"
            :key="offering.id"
            class="text-[#737373] hover:bg-[#fafafa] transition-colors"
          >
            <td class="px-4 py-3">
              <p class="font-medium text-black">
                {{ offering.course_name }}
              </p>
              <p class="font-mono text-xs text-[#a3a3a3]">
                {{ offering.course_code }}
              </p>
            </td>
            <td class="px-4 py-3">
              {{ offering.class_scope }}
            </td>
            <td class="px-4 py-3 text-right">
              {{ offering.enrolled_count }}<span class="text-xs text-[#a3a3a3]"> / {{ offering.capacity ?? '不限' }}</span>
            </td>
            <td class="px-4 py-3">
              <Badge :variant="offering.status === 'active' ? 'default' : 'secondary'">
                {{ offering.status === 'active' ? '开课中' : '已结课' }}
              </Badge>
            </td>
            <td class="px-4 py-3">
              <div class="flex justify-end gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  class="hover:bg-[#fafafa]"
                  @click="goGrades(offering.id)"
                >
                  <ClipboardList class="mr-1 h-4 w-4" />
                  成绩录入
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  class="hover:bg-[#fafafa]"
                  @click="goRankings(offering.course_id)"
                >
                  <Trophy class="mr-1 h-4 w-4" />
                  排行榜
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
        <Presentation class="mb-4 h-12 w-12 opacity-50" />
        <p>本学期暂无授课任务</p>
        <p class="mt-1 text-sm text-[#a3a3a3]">
          请联系管理员安排教学班
        </p>
      </div>
    </Card>
  </div>
</template>
