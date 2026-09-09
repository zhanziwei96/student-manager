<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { Card, Select } from '@/components/ui'
import { Loader2, Trophy } from 'lucide-vue-next'
import { rankingsApi, type RankingStudentEntry } from '@/api/rankings'
import { enrollmentsApi } from '@/api/enrollments'
import { useAuthQuery } from '@/composables/useAuth'

const { user } = useAuthQuery()
const studentId = computed(() => user.value?.username || '')

// 我的选课（科目下拉数据源）
const { data: enrollmentsData } = useQuery({
  queryKey: ['my-enrollments', studentId],
  queryFn: () => enrollmentsApi.getMyEnrollments(studentId.value),
  enabled: () => !!studentId.value,
})
const courseOptions = computed(() => {
  const seen = new Map<number, string>()
  for (const e of enrollmentsData.value ?? []) seen.set(e.course_id, e.course_name)
  return [...seen.entries()].map(([value, label]) => ({ value, label }))
})

// 本班该科目个人排行榜（后端强制学生 scope=class 自己班）
const courseId = ref<string>('')
const params = computed(() =>
  courseId.value === '' ? null : {
    type: 'individual' as const,
    course_id: Number(courseId.value),
    scope: 'class' as const,
  },
)

const { data, isPending } = useQuery({
  queryKey: ['rankings', params],
  queryFn: () => rankingsApi.getRankings(params.value!),
  enabled: () => params.value !== null,
})
// 学生榜固定为个人榜（后端强制 scope=class）
const entries = computed<RankingStudentEntry[]>(() => (data.value?.entries ?? []) as RankingStudentEntry[])
const myRank = computed(() => data.value?.my_rank ?? null)
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-5">
      <div>
        <h1 class="text-2xl font-medium text-black">
          排行榜
        </h1>
        <p class="text-[#737373]">
          查看本班各科学生成绩排名
        </p>
      </div>
    </div>

    <!-- 科目选择 -->
    <div class="mb-5 w-full sm:w-64">
      <Select
        v-model="courseId"
        :options="courseOptions"
        placeholder="选择科目"
      />
    </div>

    <!-- 榜单 -->
    <Card class="overflow-hidden p-0">
      <div
        v-if="courseId === ''"
        class="flex h-64 flex-col items-center justify-center text-[#737373]"
      >
        <Trophy class="mb-4 h-12 w-12 opacity-50" />
        <p>请选择科目</p>
        <p class="mt-1 text-sm text-[#a3a3a3]">
          按科目查看本班学生成绩排名
        </p>
      </div>

      <div
        v-else-if="isPending"
        class="flex h-64 items-center justify-center"
      >
        <Loader2 class="h-8 w-8 animate-spin text-primary" />
      </div>

      <div v-else>
        <!-- 我的排名提示 -->
        <div
          v-if="myRank"
          class="border-b border-[#e5e5e5] bg-[#fafafa] px-4 py-3 text-sm"
        >
          <span class="text-[#737373]">我的排名：</span>
          <span class="font-medium text-black">第 {{ myRank.rank }} 名</span>
          <span class="ml-2 text-[#a3a3a3]">{{ myRank.score }} 分</span>
        </div>

        <table
          v-if="entries.length > 0"
          class="w-full text-sm"
        >
          <thead class="bg-[#fafafa] text-[#737373] border-b border-[#e5e5e5]">
            <tr>
              <th class="px-4 py-3 text-left font-medium w-16">
                排名
              </th>
              <th class="px-4 py-3 text-left font-medium">
                学生
              </th>
              <th class="px-4 py-3 text-right font-medium">
                成绩
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[#e5e5e5]">
            <tr
              v-for="entry in entries"
              :key="entry.student_id"
              class="transition-colors"
              :class="entry.student_id === studentId ? 'bg-[#fafafa]' : 'text-[#737373] hover:bg-[#fafafa]'"
            >
              <td class="px-4 py-3">
                <span
                  class="inline-flex h-6 w-6 items-center justify-center rounded-full text-xs font-medium"
                  :class="entry.rank === 1 ? 'bg-[#f59e0b]/15 text-[#f59e0b]' : entry.rank <= 3 ? 'bg-[#e5e5e5] text-black' : 'text-[#a3a3a3]'"
                >
                  {{ entry.rank }}
                </span>
              </td>
              <td class="px-4 py-3">
                <span class="font-medium text-black">
                  {{ entry.name }}
                </span>
                <span
                  v-if="entry.student_id === studentId"
                  class="ml-2 text-xs text-[#a3a3a3]"
                >
                  （我）
                </span>
              </td>
              <td class="px-4 py-3 text-right font-medium text-black">
                {{ entry.score }}
              </td>
            </tr>
          </tbody>
        </table>

        <div
          v-else
          class="flex h-64 flex-col items-center justify-center text-[#737373]"
        >
          <p>暂无成绩数据</p>
        </div>
      </div>
    </Card>
  </div>
</template>
