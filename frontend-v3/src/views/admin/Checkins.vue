<script setup lang="ts">
import { computed, ref } from 'vue'
import { Card, Select } from '@/components/ui'
import { CheckCircle, Users, Clock, TrendingUp } from 'lucide-vue-next'
import { useSessionCheckinStats } from '@/composables/useCheckins'
import { useActiveClassSessions } from '@/composables/useCourseSessions'

// 先取活跃课堂列表，再按所选课堂拉签到统计
// （不传 session_id 时后端按「当前教师」的身份查，管理员拿不到数据）
const { data: sessionsData, isPending: isLoadingSessions } = useActiveClassSessions()
const sessions = computed(() => sessionsData.value ?? [])

const selectedId = ref<number>()
const sessionId = computed(() => selectedId.value ?? sessions.value[0]?.id)
const { data: stats } = useSessionCheckinStats(sessionId)

const sessionOptions = computed(() =>
  sessions.value.map((s) => ({
    value: s.id,
    label: `${s.class_name}${s.course_name ? ` · ${s.course_name}` : ''}（${s.teacher_name}）`,
  })),
)
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-5">
      <div>
        <h1 class="text-2xl font-medium text-black">
          签到统计
        </h1>
        <p class="text-[#737373]">
          查看当前活跃课堂的签到统计
        </p>
      </div>
      <Select
        v-if="sessions.length > 1"
        v-model="selectedId"
        :options="sessionOptions"
        class="w-full sm:w-80"
      />
    </div>

    <!-- 没有进行中的课堂 -->
    <Card
      v-if="!isLoadingSessions && sessions.length === 0"
      class="flex h-64 flex-col items-center justify-center border-[#e5e5e5] text-[#737373]"
    >
      <p>当前没有进行中的课堂</p>
      <p class="mt-1 text-sm text-[#a3a3a3]">
        教师在「课堂签到」里开始课堂后，这里会实时显示签到数据
      </p>
    </Card>

    <!-- Stats Cards - CSS变量主题色 -->
    <div
      v-else
      class="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4 mb-5"
    >
      <!-- 总学生数 -->
      <Card class="relative overflow-hidden p-4 border-[#e5e5e5] bg-[#fafafa]">
        <div class="relative z-10 flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-[#f5f5f5]">
            <Users class="h-5 w-5 text-[#525252]" />
          </div>
          <div>
            <p class="text-xs text-[#a3a3a3]">
              总学生数
            </p>
            <p class="text-xl font-medium text-black">
              {{ stats?.total || 0 }}
            </p>
          </div>
        </div>
      </Card>

      <!-- 已签到 -->
      <Card class="relative overflow-hidden p-4 border-[#e5e5e5] bg-[#fafafa]">
        <div class="relative z-10 flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-[#f5f5f5]">
            <CheckCircle class="h-5 w-5 text-[#525252]" />
          </div>
          <div>
            <p class="text-xs text-[#a3a3a3]">
              已签到
            </p>
            <p class="text-xl font-medium text-[#16a34a]">
              {{ stats?.checked_in || 0 }}
            </p>
          </div>
        </div>
      </Card>

      <!-- 未签到 -->
      <Card class="relative overflow-hidden p-4 border-[#e5e5e5] bg-[#fafafa]">
        <div class="relative z-10 flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-[#f5f5f5]">
            <Clock class="h-5 w-5 text-[#525252]" />
          </div>
          <div>
            <p class="text-xs text-[#a3a3a3]">
              未签到
            </p>
            <p class="text-xl font-medium text-[#dc2626]">
              {{ stats?.not_checked_in || 0 }}
            </p>
          </div>
        </div>
      </Card>

      <!-- 签到率 -->
      <Card class="relative overflow-hidden p-4 border-[#e5e5e5] bg-[#fafafa]">
        <div class="relative z-10 flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-[#f5f5f5]">
            <TrendingUp class="h-5 w-5 text-[#525252]" />
          </div>
          <div>
            <p class="text-xs text-[#a3a3a3]">
              签到率
            </p>
            <p class="text-xl font-medium text-[#3b82f6]">
              {{ stats?.rate || 0 }}%
            </p>
          </div>
        </div>
      </Card>
    </div>
  </div>
</template>
