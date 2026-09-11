<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { useRoute } from 'vue-router'
import { Card, Button, Select } from '@/components/ui'
import { Loader2, Trophy, Users, UserRound } from 'lucide-vue-next'
import { rankingsApi, type RankingEntry, type RankingGroupEntry, type RankingStudentEntry } from '@/api/rankings'
import { offeringsApi } from '@/api/offerings'
import { classesApi } from '@/api/classes'

const route = useRoute()

// 授课科目（去重，来自我的教学班）
const { data: mine } = useQuery({
  queryKey: ['teacher-offerings'],
  queryFn: () => offeringsApi.listMine(),
})
const courseOptions = computed(() => {
  const seen = new Map<number, string>()
  for (const o of mine.value ?? []) seen.set(o.course_id, o.course_name)
  return [...seen.entries()].map(([value, label]) => ({ value, label }))
})

// 查询条件
const courseId = ref<string>(route.query.course_id ? String(route.query.course_id) : '')
const type = ref<'individual' | 'group'>('individual')
const scope = ref<'class' | 'all'>('class')
const selectedClassId = ref<number | ''>('')

const params = computed(() =>
  courseId.value === '' ? null : {
    type: type.value,
    course_id: Number(courseId.value),
    scope: scope.value,
    class_id: scope.value === 'class' && selectedClassId.value !== '' ? selectedClassId.value : undefined,
  },
)

const { data, isPending } = useQuery({
  queryKey: ['rankings', params],
  queryFn: () => rankingsApi.getRankings(params.value!),
  enabled: () => params.value !== null,
})

// 班内榜班级下拉：响应 classes 为展示名，按 display_name 反查 class_id
const { data: allClasses } = useQuery({
  queryKey: ['classes'],
  queryFn: () => classesApi.list(),
})
const classOptions = computed(() =>
  (data.value?.classes ?? []).flatMap((name) => {
    const cls = (allClasses.value ?? []).find((c) => c.display_name === name)
    return cls ? [{ value: cls.id, label: name }] : []
  }),
)
// 未选中时自动选第一个
watch(classOptions, (list) => {
  if (list.length > 0 && !list.some((o) => o.value === selectedClassId.value)) {
    selectedClassId.value = list[0].value
  }
})

const entries = computed<RankingEntry[]>(() => data.value?.entries ?? [])

const isGroupEntry = () => type.value === 'group'

const entryKey = (entry: RankingEntry) =>
  type.value === 'individual'
    ? (entry as RankingStudentEntry).student_id
    : (entry as RankingGroupEntry).group_id

const switchType = (next: 'individual' | 'group') => {
  if (type.value === next) return
  type.value = next
}

const switchScope = (next: 'class' | 'all') => {
  if (scope.value === next) return
  scope.value = next
}
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-5">
      <div>
        <h1 class="text-2xl font-medium text-black">
          成绩排行榜
        </h1>
        <p class="text-[#737373]">
          按所授科目查看个人与小组成绩排名
        </p>
      </div>
    </div>

    <!-- 筛选区 -->
    <div class="mb-5 flex flex-col gap-4">
      <div class="w-full sm:w-64">
        <Select
          v-model="courseId"
          :options="courseOptions"
          placeholder="选择科目"
        />
      </div>

      <div class="flex flex-col gap-3 sm:flex-row sm:items-center">
        <!-- 类型切换 -->
        <div class="flex rounded-full border border-[#e5e5e5] bg-white p-1 w-fit">
          <Button
            variant="ghost"
            size="sm"
            :class="type === 'individual' ? 'bg-[#e5e5e5] text-black' : 'text-[#737373]'"
            @click="switchType('individual')"
          >
            <UserRound class="mr-1 h-4 w-4" />
            个人成绩
          </Button>
          <Button
            variant="ghost"
            size="sm"
            :class="type === 'group' ? 'bg-[#e5e5e5] text-black' : 'text-[#737373]'"
            @click="switchType('group')"
          >
            <Users class="mr-1 h-4 w-4" />
            小组成绩
          </Button>
        </div>

        <!-- 范围切换 -->
        <div class="flex rounded-full border border-[#e5e5e5] bg-white p-1 w-fit">
          <Button
            variant="ghost"
            size="sm"
            :class="scope === 'class' ? 'bg-[#e5e5e5] text-black' : 'text-[#737373]'"
            @click="switchScope('class')"
          >
            班内
          </Button>
          <Button
            variant="ghost"
            size="sm"
            :class="scope === 'all' ? 'bg-[#e5e5e5] text-black' : 'text-[#737373]'"
            @click="switchScope('all')"
          >
            跨班
          </Button>
        </div>

        <!-- 班内榜班级选择 -->
        <div
          v-if="scope === 'class' && classOptions.length > 0"
          class="w-full sm:w-48"
        >
          <Select
            v-model="selectedClassId"
            :options="classOptions"
            placeholder="选择班级"
          />
        </div>
      </div>
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
          排行榜按您所授科目的成绩排名
        </p>
      </div>

      <div
        v-else-if="isPending"
        class="flex h-64 items-center justify-center"
      >
        <Loader2 class="h-8 w-8 animate-spin text-primary" />
      </div>

      <table
        v-else-if="entries.length > 0"
        class="w-full text-sm"
      >
        <thead class="bg-[#fafafa] text-[#737373] border-b border-[#e5e5e5]">
          <tr>
            <th class="px-4 py-3 text-left font-medium w-16">
              排名
            </th>
            <th class="px-4 py-3 text-left font-medium">
              {{ type === 'individual' ? '学生' : '小组' }}
            </th>
            <th
              v-if="scope === 'all'"
              class="px-4 py-3 text-left font-medium"
            >
              班级
            </th>
            <th class="px-4 py-3 text-right font-medium">
              成绩
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-[#e5e5e5]">
          <tr
            v-for="entry in entries"
            :key="entryKey(entry)"
            class="text-[#737373] hover:bg-[#fafafa] transition-colors"
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
              <p class="font-medium text-black">
                {{ entry.name }}
              </p>
              <p
                v-if="isGroupEntry()"
                class="text-xs text-[#a3a3a3]"
              >
                {{ (entry as RankingGroupEntry).members.join('、') }}
              </p>
            </td>
            <td
              v-if="scope === 'all'"
              class="px-4 py-3"
            >
              {{ entry.class_name }}
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
        <p class="mt-1 text-sm text-[#a3a3a3]">
          成绩录入后自动生成排名
        </p>
      </div>
    </Card>
  </div>
</template>
