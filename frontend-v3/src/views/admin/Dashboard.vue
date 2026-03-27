<script setup lang="ts">
import { computed } from 'vue'
import { useStats } from '@/composables'
import { Card, Badge } from '@/components/ui'
import { Users, GraduationCap, BookOpen, TrendingUp, Loader2 } from 'lucide-vue-next'

const { data: stats, isPending, error } = useStats()

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

    <!-- Recent activity -->
    <Card class="border-white/10 bg-white/[0.02] p-6">
      <h2 class="text-lg font-semibold text-white">
        最近活动
      </h2>
      <p class="text-sm text-white/60">
        课堂最新动态
      </p>
      
      <!-- TODO: 替换为真实的活动日志 API -->
      <div class="mt-6 space-y-4">
        <div
          v-for="i in 5"
          :key="i"
          class="flex items-center gap-4 border-b border-white/5 pb-4 last:border-0"
        >
          <div class="h-8 w-8 rounded-full bg-primary/20" />
          <div class="flex-1">
            <p class="text-sm text-white">
              学生 {{ i }} 签到成功
            </p>
            <p class="text-xs text-white/40">
              {{ i }} 分钟前
            </p>
          </div>
          <Badge variant="secondary">
            +10 分
          </Badge>
        </div>
      </div>
    </Card>
  </div>
</template>
