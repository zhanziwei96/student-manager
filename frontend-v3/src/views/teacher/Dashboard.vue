<script setup lang="ts">
import { computed } from 'vue'
import { useStats, useTodaySchedules, useActiveClassSessions } from '@/composables'
import { Card, Button, DataContainer, Badge } from '@/components/ui'
import { Users, Calendar, Clock, Loader2, ArrowRight, MapPin } from 'lucide-vue-next'
import { useRouter } from 'vue-router'

const router = useRouter()
const { data: stats, isPending, error } = useStats()
const { data: todaySchedules, isPending: isLoadingSchedules } = useTodaySchedules()
const { data: activeSessions } = useActiveClassSessions()

// 活跃课堂数量
const activeSessionsCount = computed(() => activeSessions.value?.length || 0)

// 获取今天的星期
const todayWeekDay = computed(() => {
  const days = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return days[new Date().getDay()]
})

const statCards = computed(() => [
  {
    title: '我的学生',
    value: stats.value?.total_students ?? 0,
    icon: Users,
    link: '/teacher/students',
  },
  {
    title: '活跃课堂',
    value: activeSessionsCount.value,
    icon: Calendar,
    link: '/teacher/session',
  },
  {
    title: '授课时长',
    value: '-',
    icon: Clock,
    link: '/teacher/schedules',
  },
])

</script>

<template>
  <div class="space-y-5">
    <!-- Header -->
    <div class="px-1">
      <h1 class="text-2xl font-medium text-black tracking-tight">
        教师仪表板
      </h1>
      <p class="text-[#a3a3a3] text-sm mt-1">
        欢迎回来，教师
      </p>
    </div>

    <!-- Quick actions -->
    <div class="flex gap-3 mb-5">
      <Button @click="router.push('/teacher/session')">
        <Calendar class="mr-2 h-4 w-4" />
        开始上课
      </Button>
      <Button
        variant="outline"
        @click="router.push('/teacher/students')"
      >
        <Users class="mr-2 h-4 w-4" />
        查看学生
      </Button>
    </div>

    <!-- Loading state -->
    <div
      v-if="isPending"
      class="flex h-64 items-center justify-center"
    >
      <Loader2 class="h-8 w-8 animate-spin text-primary" />
    </div>

    <!-- Error state -->
    <div
      v-else-if="error"
      class="rounded-xl border border-red-500/30 bg-red-500/15 p-4 text-red-400"
    >
      加载统计数据失败: {{ error.message }}
    </div>

    <!-- Stats grid - 移动端2列布局 -->
    <div
      v-else
      class="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-3 mb-5"
    >
      <Card
        v-for="card in statCards"
        :key="card.title"
        class="group relative overflow-hidden p-4 cursor-pointer"
        :class="'bg-white border-[#e5e5e5]'"
        @click="router.push(card.link)"
      >
        <div class="relative z-10">
          <div class="flex items-start justify-between">
            <div>
              <p class="mt-3 text-xs font-medium text-[#737373]">
                {{ card.title }}
              </p>
              <p class="mt-1 text-2xl font-medium text-black">
                {{ card.value }}
              </p>
            </div>
            <div
              class="flex h-10 w-10 items-center justify-center rounded-xl transition-transform"
              :class="'bg-primary/10 text-primary'"
            >
              <component
                :is="card.icon"
                class="h-5 w-5"
              />
            </div>
          </div>
          <div class="mt-3">
            <span class="text-xs text-[#737373] flex items-center">
              查看详情
              <ArrowRight class="ml-1 h-3 w-3 transition-transform group-hover:translate-x-1" />
            </span>
          </div>
        </div>
        <!-- 背景装饰 -->
      </Card>
    </div>

    <!-- Today's schedule - 增强视觉层次 -->
    <Card class="border-[#e5e5e5] bg-white p-5 mt-5">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h2 class="text-lg font-medium text-black">
            今日课表
          </h2>
          <p class="text-xs text-[#a3a3a3] mt-0.5">
            {{ todayWeekDay }}的课程安排
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          @click="router.push('/teacher/schedules')"
        >
          管理课表
        </Button>
      </div>

      <DataContainer
        :loading="isLoadingSchedules"
        :has-data="todaySchedules?.length > 0"
        empty-text="今天没有课程安排"
      >
        <div class="space-y-2.5">
          <div
            v-for="schedule in todaySchedules"
            :key="schedule.id"
            class="group flex items-center gap-3 rounded-xl border border-[#e5e5e5] bg-white p-3.5 hover:bg-[#fafafa] hover:border-[#e5e5e5]"
          >
            <div class="flex h-11 w-11 flex-col items-center justify-center rounded-xl bg-primary/20 text-primary">
              <Clock class="h-3.5 w-3.5 mb-0.5" />
              <span class="text-[10px] font-medium">{{ schedule.start_time?.slice(0, 5) }}</span>
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <p class="font-medium text-black text-sm truncate">
                  {{ schedule.course_name }}
                </p>
                <Badge
                  v-if="schedule.session_status === 'makeup' || schedule.adjustment"
                  variant="outline"
                  class="bg-[#f5f5f5] text-[#525252] border-[#e5e5e5] text-[10px]"
                >
                  补课
                </Badge>
              </div>
              <p class="text-xs text-[#a3a3a3] flex items-center gap-1.5">
                {{ schedule.class_name }}
                <span
                  v-if="(schedule.adjustment?.new_classroom || schedule.classroom)"
                  class="inline-flex items-center gap-0.5"
                >
                  <MapPin class="h-3 w-3" />
                  {{ schedule.adjustment?.new_classroom || schedule.classroom }}
                </span>
              </p>
            </div>
            <template v-if="schedule.session_status === 'active'">
              <Button
                size="sm"
                class="bg-green-500 hover:bg-green-600 text-white"
                @click="router.push('/teacher/session')"
              >
                进入课堂
              </Button>
            </template>
            <template v-else-if="schedule.session_status === 'ended'">
              <span class="text-xs text-[#a3a3a3]">已结束</span>
            </template>
            <template v-else-if="schedule.session_status === 'cancelled' || schedule.session_status === 'skipped'">
              <Badge variant="outline" class="bg-[#fafafa] text-[#a3a3a3] border-[#e5e5e5]">
                已停课
              </Badge>
            </template>
            <template v-else>
              <Button
                size="sm"
                class="bg-green-500 hover:bg-green-600 text-white"
                @click="router.push(`/teacher/session?scheduleId=${schedule.id}&className=${encodeURIComponent(schedule.class_name)}&courseName=${encodeURIComponent(schedule.course_name)}`)"
              >
                去上课
              </Button>
            </template>
          </div>
        </div>
      </DataContainer>
    </Card>
  </div>
</template>
