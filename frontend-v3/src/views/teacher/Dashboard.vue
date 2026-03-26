<script setup lang="ts">
import { computed } from 'vue'
import { useStats, useTodaySchedules } from '@/composables'
import { Card, Button, Badge, DataContainer } from '@/components/ui'
import { Users, Calendar, Clock, Loader2, ArrowRight, MapPin } from 'lucide-vue-next'
import { useRouter } from 'vue-router'

const router = useRouter()
const { data: stats, isPending, error } = useStats()
const { data: todaySchedules, isPending: isLoadingSchedules } = useTodaySchedules()

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
    color: 'text-blue-400',
    link: '/teacher/students',
  },
  {
    title: '活跃课堂',
    value: '2', // TODO: 从 API 获取真实数据
    icon: Calendar,
    color: 'text-green-400',
    link: '/teacher/session',
  },
  {
    title: '授课时长',
    value: '24小时', // TODO: 从 API 获取真实数据
    icon: Clock,
    color: 'text-purple-400',
    link: '/teacher',
  },
])
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-white">教师仪表板</h1>
      <p class="text-white/60">欢迎回来，教师</p>
    </div>

    <!-- Quick actions -->
    <div class="flex gap-4">
      <Button @click="router.push('/teacher/session')">
        <Calendar class="mr-2 h-4 w-4" />
        开始上课
      </Button>
      <Button variant="outline" @click="router.push('/teacher/students')">
        <Users class="mr-2 h-4 w-4" />
        查看学生
      </Button>
    </div>

    <!-- Loading state -->
    <div v-if="isPending" class="flex h-64 items-center justify-center">
      <Loader2 class="h-8 w-8 animate-spin text-primary" />
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="rounded-lg border border-red-500/20 bg-red-500/10 p-4 text-red-400">
      加载统计数据失败: {{ error.message }}
    </div>

    <!-- Stats grid -->
    <div v-else class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
      <Card
        v-for="card in statCards"
        :key="card.title"
        class="group border-white/10 bg-white/[0.02] p-6 transition-colors hover:border-white/20"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-white/60">{{ card.title }}</p>
            <p class="mt-1 text-3xl font-bold text-white">{{ card.value }}</p>
          </div>
          <div :class="['rounded-lg bg-white/5 p-3 transition-colors group-hover:bg-white/10', card.color]">
            <component :is="card.icon" class="h-6 w-6" />
          </div>
        </div>
        <div class="mt-4">
          <Button variant="ghost" size="sm" class="p-0 text-primary hover:text-primary/80" @click="router.push(card.link)">
            查看详情
            <ArrowRight class="ml-1 h-4 w-4" />
          </Button>
        </div>
      </Card>
    </div>

    <!-- Today's schedule -->
    <Card class="border-white/10 bg-white/[0.02] p-6">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-lg font-semibold text-white">今日课表</h2>
          <p class="text-sm text-white/60">{{ todayWeekDay }}的课程安排</p>
        </div>
        <Button variant="outline" size="sm" @click="router.push('/teacher/schedules')">
          管理课表
        </Button>
      </div>
      
      <DataContainer
        :loading="isLoadingSchedules"
        :has-data="todaySchedules.length > 0"
        empty-text="今天没有课程安排"
        class="mt-4"
      >
        <div class="space-y-3">
          <div
            v-for="schedule in todaySchedules"
            :key="schedule.id"
            class="flex items-center gap-4 rounded-lg border border-white/5 bg-white/[0.02] p-4"
          >
            <div class="flex h-12 w-12 flex-col items-center justify-center rounded-lg bg-primary/10 text-primary">
              <span class="text-xs font-medium">{{ schedule.start_time }}</span>
            </div>
            <div class="flex-1">
              <p class="font-medium text-white">{{ schedule.course_name }}</p>
              <p class="text-sm text-white/60">
                {{ schedule.class_name }}
                <span v-if="schedule.classroom" class="inline-flex items-center gap-1 ml-2">
                  <MapPin class="h-3 w-3" />
                  {{ schedule.classroom }}
                </span>
              </p>
            </div>
            <Button
              size="sm"
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
