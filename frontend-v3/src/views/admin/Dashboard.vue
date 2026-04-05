<script setup lang="ts">
import { computed } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { useStats } from '@/composables'
import { Card, Badge } from '@/components/ui'
import { Users, GraduationCap, BookOpen, TrendingUp, Loader2, Clock } from 'lucide-vue-next'
import { checkinApi } from '@/api/checkin'
import { formatDistanceToNow } from '@/lib/date'
const { data: stats, isPending, error } = useStats()

// 获取正在上课的课堂列表 - 优化: 30秒刷新一次，窗口聚焦时不自动刷新
const { data: activeSessions, isPending: isLoadingSessions } = useQuery({
  queryKey: ['active-sessions'],
  queryFn: () => checkinApi.getActiveSessions(),
  staleTime: 30 * 1000, // 30秒内不重复请求
  refetchInterval: 30 * 1000, // 每30秒自动刷新一次
  refetchOnWindowFocus: false, // 窗口聚焦时不自动刷新
})

const statCards = computed(() => [
  {
    title: '学生总数',
    value: stats.value?.total_students ?? 0,
    icon: Users,
    trend: '+12%',
    color: 'blue',
  },
  {
    title: '活跃学生',
    value: stats.value?.active_students ?? 0,
    icon: GraduationCap,
    trend: '+5%',
    color: 'green',
  },
  {
    title: '班级总数',
    value: stats.value?.total_classes ?? 0,
    icon: BookOpen,
    trend: '0%',
    color: 'purple',
  },
  {
    title: '平均分数',
    value: Math.round(stats.value?.average_score ?? 0),
    icon: TrendingUp,
    trend: '+2%',
    color: 'orange',
  },
])

// 获取卡片颜色配置
const getCardColors = (color: string) => {
  const colors: Record<string, { border: string; bg: string; iconBg: string; iconText: string; shadow: string; trendBg: string; trendText: string }> = {
    blue: {
      border: 'border-blue-500/40',
      bg: 'bg-blue-500/15',
      iconBg: 'bg-blue-400/30',
      iconText: 'text-blue-200',
      shadow: 'shadow-blue-900/30',
      trendBg: 'bg-blue-400/20',
      trendText: 'text-blue-300',
    },
    green: {
      border: 'border-green-500/40',
      bg: 'bg-green-500/15',
      iconBg: 'bg-green-400/30',
      iconText: 'text-green-200',
      shadow: 'shadow-green-900/30',
      trendBg: 'bg-green-400/20',
      trendText: 'text-green-300',
    },
    purple: {
      border: 'border-purple-500/40',
      bg: 'bg-purple-500/15',
      iconBg: 'bg-purple-400/30',
      iconText: 'text-purple-200',
      shadow: 'shadow-purple-900/30',
      trendBg: 'bg-purple-400/20',
      trendText: 'text-purple-300',
    },
    orange: {
      border: 'border-orange-500/40',
      bg: 'bg-orange-500/15',
      iconBg: 'bg-orange-400/30',
      iconText: 'text-orange-200',
      shadow: 'shadow-orange-900/30',
      trendBg: 'bg-orange-400/20',
      trendText: 'text-orange-300',
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
        仪表板
      </h1>
      <p class="text-white/50 text-sm mt-1">
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
      class="rounded-xl border border-red-500/30 bg-red-500/15 p-4 text-red-400"
    >
      加载统计数据失败: {{ error.message }}
    </div>

    <!-- Stats grid - 移动端2列，桌面4列 -->
    <div
      v-else
      class="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4"
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
          <div class="mt-3 flex items-center gap-2">
            <Badge
              class="text-xs px-2 py-0.5 border-0"
              :class="getCardColors(card.color).trendBg + ' ' + getCardColors(card.color).trendText"
            >
              {{ card.trend }}
            </Badge>
            <span class="text-xs text-white/40">较上月</span>
          </div>
        </div>
        <!-- 背景装饰 -->
        <div :class="['absolute -right-4 -bottom-4 h-16 w-16 rounded-full blur-2xl transition-colors opacity-30', getCardColors(card.color).iconBg]" />
      </Card>
    </div>

    <!-- Active Classes - 增强视觉层次 -->
    <Card class="border-white/15 bg-white/[0.06] p-5 shadow-xl shadow-black/20">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h2 class="text-lg font-semibold text-white">
            正在上课
          </h2>
          <p class="text-xs text-white/50 mt-0.5">
            当前活跃的课堂
          </p>
        </div>
        <Badge
          variant="primary"
          class="text-xs bg-primary/20 text-primary border-primary/30"
        >
          {{ activeSessions?.length || 0 }} 个课堂
        </Badge>
      </div>

      <!-- Loading state -->
      <div
        v-if="isLoadingSessions"
        class="flex h-32 items-center justify-center"
      >
        <Loader2 class="h-6 w-6 animate-spin text-primary" />
      </div>

      <!-- Empty state -->
      <div
        v-else-if="!activeSessions?.length"
        class="flex flex-col items-center justify-center py-8 text-white/40"
      >
        <div class="h-12 w-12 rounded-full bg-white/5 flex items-center justify-center mb-3">
          <Clock class="h-5 w-5 opacity-50" />
        </div>
        <p class="text-sm">
          暂无正在上课的课堂
        </p>
      </div>

      <!-- Active sessions list -->
      <div
        v-else
        class="space-y-2.5"
      >
        <div
          v-for="session in activeSessions"
          :key="session.class_name + session.teacher_name"
          class="group flex items-center gap-3 rounded-xl border border-white/5 bg-white/[0.03] p-3.5 transition-all duration-200 hover:bg-white/[0.06] hover:border-white/10"
        >
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/20 shadow-inner">
            <BookOpen class="h-5 w-5 text-primary" />
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-white truncate">
              <span class="text-primary">【{{ session.course_name || '未知课程' }}】</span>
              {{ session.class_name }}
            </p>
            <p class="text-xs text-white/50 flex items-center gap-2">
              <span>{{ session.teacher_name }}</span>
              <span class="text-white/30">•</span>
              <span>开始于 {{ formatDistanceToNow(session.start_time) }}</span>
            </p>
          </div>
          <div class="flex items-center gap-2">
            <div class="h-2 w-2 rounded-full bg-green-500 shadow-lg shadow-green-500/50 animate-pulse" />
            <span class="text-xs text-green-400 hidden sm:inline">进行中</span>
          </div>
        </div>
      </div>
    </Card>
  </div>
</template>
