<script setup lang="ts">
import { computed } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { useStats } from '@/composables'
import { Card, Badge } from '@/components/ui'
import { Users, GraduationCap, BookOpen, TrendingUp, Loader2, Clock } from 'lucide-vue-next'
import { checkinApi } from '@/api/checkin'
import { formatDistanceToNow } from '@/lib/date'

const { data: stats, isPending, error } = useStats()

// 获取正在上课的课堂列表
const { data: activeSessions, isPending: isLoadingSessions } = useQuery({
  queryKey: ['active-sessions'],
  queryFn: () => checkinApi.getActiveSessions(),
})

const statCards = computed(() => [
  {
    title: '学生总数',
    value: stats.value?.total_students ?? 0,
    icon: Users,
    trend: '+12%', // TODO: 从 API 获取真实趋势数据
    color: 'text-blue-400',
  },
  {
    title: '活跃学生',
    value: stats.value?.active_students ?? 0,
    icon: GraduationCap,
    trend: '+5%', // TODO: 从 API 获取真实趋势数据
    color: 'text-green-400',
  },
  {
    title: '班级总数',
    value: stats.value?.total_classes ?? 0,
    icon: BookOpen,
    trend: '0%', // TODO: 从 API 获取真实趋势数据
    color: 'text-purple-400',
  },
  {
    title: '平均分数',
    value: Math.round(stats.value?.average_score ?? 0),
    icon: TrendingUp,
    trend: '+2%', // TODO: 从 API 获取真实趋势数据
    color: 'text-orange-400',
  },
])
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-white">
        仪表板
      </h1>
      <p class="text-white/60">
        欢迎回来，管理员
      </p>
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
      class="rounded-lg border border-red-500/20 bg-red-500/10 p-4 text-red-400"
    >
      加载统计数据失败: {{ error.message }}
    </div>

    <!-- Stats grid -->
    <div
      v-else
      class="grid gap-6 sm:grid-cols-2 lg:grid-cols-4"
    >
      <Card
        v-for="card in statCards"
        :key="card.title"
        class="border-white/10 bg-white/[0.02] p-6"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-white/60">
              {{ card.title }}
            </p>
            <p class="mt-1 text-3xl font-bold text-white">
              {{ card.value }}
            </p>
          </div>
          <div :class="['rounded-lg bg-white/5 p-3', card.color]">
            <component
              :is="card.icon"
              class="h-6 w-6"
            />
          </div>
        </div>
        <div class="mt-4 flex items-center gap-2">
          <Badge
            variant="secondary"
            class="text-xs"
          >
            {{ card.trend }}
          </Badge>
          <span class="text-xs text-white/40">较上月</span>
        </div>
      </Card>
    </div>

    <!-- Active Classes -->
    <Card class="border-white/10 bg-white/[0.02] p-6">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-lg font-semibold text-white">
            正在上课
          </h2>
          <p class="text-sm text-white/60">
            当前活跃课堂
          </p>
        </div>
        <Badge variant="primary" class="text-xs">
          {{ activeSessions?.length || 0 }} 个课堂
        </Badge>
      </div>
      
      <!-- Loading state -->
      <div v-if="isLoadingSessions" class="mt-6 flex h-32 items-center justify-center">
        <Loader2 class="h-6 w-6 animate-spin text-primary" />
      </div>
      
      <!-- Empty state -->
      <div v-else-if="!activeSessions?.length" class="mt-6 flex h-32 flex-col items-center justify-center text-white/40">
        <Clock class="mb-2 h-8 w-8" />
        <p class="text-sm">暂无正在上课的课堂</p>
      </div>
      
      <!-- Active sessions list -->
      <div v-else class="mt-6 space-y-3">
        <div
          v-for="session in activeSessions"
          :key="session.class_name + session.teacher_name"
          class="flex items-center gap-3 rounded-lg border border-white/5 bg-white/[0.02] p-4"
        >
          <div class="flex h-10 w-10 items-center justify-center rounded-full bg-primary/20">
            <BookOpen class="h-5 w-5 text-primary" />
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-white truncate">
              <span class="text-primary">【{{ session.course_name || '未知课程' }}】</span>
              {{ session.class_name }}
              <span class="text-white/60">| {{ session.teacher_name }}</span>
            </p>
            <p class="text-xs text-white/40 mt-0.5">
              开始于 {{ formatDistanceToNow(session.start_time) }}
            </p>
          </div>
          <div class="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
        </div>
      </div>
    </Card>
  </div>
</template>
