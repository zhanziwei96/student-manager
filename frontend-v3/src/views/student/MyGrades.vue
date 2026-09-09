<script setup lang="ts">
import { computed } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { Card, Badge } from '@/components/ui'
import { Loader2, GraduationCap, Users } from 'lucide-vue-next'
import { enrollmentsApi } from '@/api/enrollments'
import { groupsApi } from '@/api/groups'
import { useAuthQuery } from '@/composables/useAuth'

const { user } = useAuthQuery()
const studentId = computed(() => user.value?.username || '')

// 我的成绩：当前学期选课列表
const { data: enrollmentsData, isPending } = useQuery({
  queryKey: ['my-enrollments', studentId],
  queryFn: () => enrollmentsApi.getMyEnrollments(studentId.value),
  enabled: () => !!studentId.value,
})
const enrollments = computed(() => enrollmentsData.value ?? [])

// 我的小组分（每科小组累计分）
const { data: myGroupsData } = useQuery({
  queryKey: ['my-groups', studentId],
  queryFn: () => groupsApi.getMyGroups(),
  enabled: () => !!studentId.value,
})
const myGroups = computed(() => myGroupsData.value ?? [])
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-5">
      <div>
        <h1 class="text-2xl font-medium text-black">
          我的成绩
        </h1>
        <p class="text-[#737373]">
          当前学期各科个人成绩与期末成绩
        </p>
      </div>
    </div>

    <!-- 选课成绩列表 -->
    <Card class="overflow-hidden p-0">
      <div
        v-if="isPending"
        class="flex h-64 items-center justify-center"
      >
        <Loader2 class="h-8 w-8 animate-spin text-primary" />
      </div>

      <table
        v-else-if="enrollments.length > 0"
        class="w-full text-sm"
      >
        <thead class="bg-[#fafafa] text-[#737373] border-b border-[#e5e5e5]">
          <tr>
            <th class="px-4 py-3 text-left font-medium">
              课程
            </th>
            <th class="px-4 py-3 text-left font-medium">
              教师
            </th>
            <th class="px-4 py-3 text-right font-medium">
              平时成绩
            </th>
            <th class="px-4 py-3 text-right font-medium">
              期末成绩
            </th>
            <th class="px-4 py-3 text-left font-medium">
              状态
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-[#e5e5e5]">
          <tr
            v-for="enrollment in enrollments"
            :key="enrollment.enrollment_id"
            class="text-[#737373] hover:bg-[#fafafa] transition-colors"
          >
            <td class="px-4 py-3">
              <p class="font-medium text-black">
                {{ enrollment.course_name }}
              </p>
              <p class="text-xs text-[#a3a3a3]">
                {{ enrollment.class_scope }}
              </p>
            </td>
            <td class="px-4 py-3">
              {{ enrollment.teacher_name }}
            </td>
            <td class="px-4 py-3 text-right font-medium text-black">
              {{ enrollment.score }}
            </td>
            <td class="px-4 py-3 text-right font-medium text-black">
              {{ enrollment.final_score ?? '—' }}
            </td>
            <td class="px-4 py-3">
              <Badge :variant="enrollment.status === 'enrolled' ? 'default' : 'secondary'">
                {{ enrollment.status === 'enrolled' ? '在读' : '已退课' }}
              </Badge>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Empty state -->
      <div
        v-else
        class="flex h-64 flex-col items-center justify-center text-[#737373]"
      >
        <GraduationCap class="mb-4 h-12 w-12 opacity-50" />
        <p>暂无选课成绩</p>
        <p class="mt-1 text-sm text-[#a3a3a3]">
          请联系管理员确认选课名单
        </p>
      </div>
    </Card>

    <!-- 小组成绩 -->
    <Card class="mt-5 overflow-hidden p-0">
      <table
        v-if="myGroups.length > 0"
        class="w-full text-sm"
      >
        <thead class="bg-[#fafafa] text-[#737373] border-b border-[#e5e5e5]">
          <tr>
            <th
              colspan="3"
              class="px-4 py-3 text-left font-medium"
            >
              <span class="inline-flex items-center gap-1.5">
                <Users class="h-4 w-4" />
                小组成绩
              </span>
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-[#e5e5e5]">
          <tr
            v-for="group in myGroups"
            :key="group.id"
            class="text-[#737373]"
          >
            <td class="px-4 py-3">
              <p class="font-medium text-black">
                {{ group.name }}
              </p>
              <p class="text-xs text-[#a3a3a3]">
                {{ group.course_name || '未分科' }}
              </p>
            </td>
            <td class="px-4 py-3">
              {{ group.leader_name || group.leader_student_id }} 组
            </td>
            <td class="px-4 py-3 text-right font-medium text-black">
              {{ group.score }}
            </td>
          </tr>
        </tbody>
      </table>
    </Card>
  </div>
</template>
