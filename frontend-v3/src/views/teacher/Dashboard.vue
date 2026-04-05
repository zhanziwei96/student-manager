<script setup lang="ts">
import { computed } from 'vue'
import { useStats, useTodaySchedules, useActiveClassSessions } from '@/composables'
import { Card, Button, DataContainer } from '@/components/ui'
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
    color: 'blue',
    link: '/teacher/students',
  },
  {
    title: '活跃课堂',
    value: activeSessionsCount.value,
    icon: Calendar,
    color: 'green',
    link: '/teacher/session',
  },
  {
    title: '授课时长',
    value: '-',
    icon: Clock,
    color: 'purple',
    link: '/teacher',
  },
])

// 获取卡片颜色配置
const getCardColors = (color: string) => {
  const colors: Record<string, { border: string; bg: string; iconBg: string; iconText: string; shadow: string }> = {
    blue: {
      border: 'border-blue-500/40',
      bg: 'bg-blue-500/15',
      iconBg: 'bg-blue-400/30',
      iconText: 'text-blue-200',
      shadow: 'shadow-blue-900/30',
    },
    green: {
      border: 'border-green-500/40',
      bg: 'bg-green-500/15',
      iconBg: 'bg-green-400/30',
      iconText: 'text-green-200',
      shadow: 'shadow-green-900/30',
    },
    purple: {
      border: 'border-purple-500/40',
      bg: 'bg-purple-500/15',
      iconBg: 'bg-purple-400/30',
      iconText: 'text-purple-200',
      shadow: 'shadow-purple-900/30',
    },
  }
  return colors[color] || colors.blue
}
</script>

<template>
  <div class="space-y-5">
    <!-- Header -->
    <div class="px-1">
      <h1 class="text-2xl font-bold text-white tracking-tight">
        教师仪表板
      </h1>
      <p class="text-white/50 text-sm mt-1">
        欢迎回来，教师
      </p>
    </div>

    <!-- Quick actions -->
    <div class="flex gap-3">
      <Button @click="router.push('/teacher/session')" class="shadow-lg shadow-primary/20">
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
      class="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-3"
    >
      <Card
        v-for="card in statCards"
        :key="card.title"
        class="group relative overflow-hidden p-4 shadow-lg transition-all duration-300 hover:scale-[1.02]"
        :class="getCardColors(card.color).border + ' ' + getCardColors(card.color).bg + ' ' + getCardColors(card.color).shadow""
      >
        <div class="relative z-10">
          <div class="flex items-start justify-between">
            <div>
              <p class="text-xs text-white/60">
                {{ card.title }}
              </p>
              <p class="mt-1 text-2xl font-bold text-white">
                {{ card.value }}
              </p>
            </div>
            <div :class="['flex h-10 w-10 items-center justify-center rounded-xl shadow-inner transition-transform group-hover:scale-110', getCardColors(card.color).iconBg]">
              <component
                :is="card.icon"
                :class="['h-5 w-5', getCardColors(card.color).iconText]"
              />
            </div>
          </div>
          <div class="mt-3">
            <Button
              variant="ghost"
              size="sm"
              class="p-0 h-auto text-xs text-white/70 hover:text-white"
              @click="router.push(card.link)"
            >
              查看详情
              <ArrowRight class="ml-1 h-3 w-3 transition-transform group-hover:translate-x-1" />
            </Button>
          </div>
        </div>
        <!-- 背景装饰 -->
        <div :class="['absolute -right-4 -bottom-4 h-16 w-16 rounded-full blur-2xl transition-colors opacity-30', getCardColors(card.color).iconBg]" />
      </Card>
    </div>

    <!-- Today's schedule - 增强视觉层次 -->
    <Card class="border-white/15 bg-white/[0.06] p-5 shadow-xl shadow-black/20">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h2 class="text-lg font-semibold text-white">
            今日课表
          </h2>
          <p class="text-xs text-white/50 mt-0.5">
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
            class="group flex items-center gap-3 rounded-xl border border-white/5 bg-white/[0.03] p-3.5 transition-all duration-200 hover:bg-white/[0.06] hover:border-white/10"
          >
            <div class="flex h-11 w-11 flex-col items-center justify-center rounded-xl bg-primary/20 text-primary shadow-inner">
              <Clock class="h-3.5 w-3.5 mb-0.5" />
              <span class="text-[10px] font-medium">{{ schedule.start_time?.slice(0, 5) }}</span>
            </div>
            <div class="flex-1 min-w-0">
              <p class="font-medium text-white text-sm truncate">
                {{ schedule.course_name }}
              </p>
              <p class="text-xs text-white/50 flex items-center gap-1.5">
                {{ schedule.class_name }}
                <span
                  v-if="schedule.classroom"
                  class="inline-flex items-center gap-0.5"
                >
                  <MapPin class="h-3 w-3" />
                  {{ schedule.classroom }}
                </span>
              </p>
            </div>
            <Button
              size="sm"
              class="shadow-md"
              @click="router.push('/teacher/session')"
            >
              去上课
            </Button>
          </div>
        </div>
      </DataContainer>
    </Card>
  </div>
</template>
