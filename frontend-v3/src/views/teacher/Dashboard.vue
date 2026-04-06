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
    color: 'blue' as CardColor,
    link: '/teacher/students',
  },
  {
    title: '活跃课堂',
    value: activeSessionsCount.value,
    icon: Calendar,
    color: 'green' as CardColor,
    link: '/teacher/session',
  },
  {
    title: '授课时长',
    value: '-',
    icon: Clock,
    color: 'purple' as CardColor,
    link: '/teacher/schedules',
  },
])

// 卡片颜色类型
type CardColor = 'blue' | 'green' | 'purple'

// 获取卡片样式 - 使用 CSS 变量
const getCardStyle = (color: CardColor) => {
  const varPrefix = `--card-${color}`
  return {
    backgroundColor: `var(${varPrefix}-bg)`,
    borderColor: `var(${varPrefix}-border)`,
    '--tw-shadow-color': `var(${varPrefix}-shadow)`,
  } as Record<string, string>
}

const getCardIconStyle = (color: CardColor) => {
  const varPrefix = `--card-${color}`
  return {
    backgroundColor: `var(${varPrefix}-icon-bg)`,
    color: `var(${varPrefix}-icon-text)`,
  }
}

const getCardGlowStyle = (color: CardColor) => {
  const varPrefix = `--card-${color}`
  return {
    backgroundColor: `var(${varPrefix}-glow)`,
  }
}

const getCardTextMutedColor = (color: CardColor) => {
  const colors: Record<CardColor, string> = {
    blue: 'text-blue-200/80',
    green: 'text-green-200/80',
    purple: 'text-purple-200/80',
  }
  return colors[color]
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
    <div class="flex gap-3 mb-5">
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
      class="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-3 mb-5"
    >
      <Card
        v-for="card in statCards"
        :key="card.title"
        class="group relative overflow-hidden p-4 shadow-lg transition-all duration-300 hover:scale-[1.02] cursor-pointer"
        :style="getCardStyle(card.color)"
        @click="router.push(card.link)"
      >
        <div class="relative z-10">
          <div class="flex items-start justify-between">
            <div>
              <p class="mt-3 text-xs font-medium" :class="getCardTextMutedColor(card.color)">
                {{ card.title }}
              </p>
              <p class="mt-1 text-2xl font-bold text-white">
                {{ card.value }}
              </p>
            </div>
            <div
              class="flex h-10 w-10 items-center justify-center rounded-xl shadow-inner transition-transform group-hover:scale-110"
              :style="getCardIconStyle(card.color)"
            >
              <component
                :is="card.icon"
                class="h-5 w-5"
              />
            </div>
          </div>
          <div class="mt-3">
            <span class="text-xs text-white/70 flex items-center">
              查看详情
              <ArrowRight class="ml-1 h-3 w-3 transition-transform group-hover:translate-x-1" />
            </span>
          </div>
        </div>
        <!-- 背景装饰 -->
        <div
          class="absolute -right-4 -bottom-4 h-16 w-16 rounded-full blur-2xl transition-colors opacity-30"
          :style="getCardGlowStyle(card.color)"
        />
      </Card>
    </div>

    <!-- Today's schedule - 增强视觉层次 -->
    <Card class="border-white/15 bg-white/[0.06] p-5 shadow-xl shadow-black/20 mt-5">
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
