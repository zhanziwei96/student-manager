<script setup lang="ts">
import { computed } from 'vue'
import { useStats } from '@/composables'
import { Card, Badge } from '@/components/ui'
import { Users, GraduationCap, BookOpen, TrendingUp, Loader2 } from 'lucide-vue-next'

const { data: stats, isPending, error } = useStats()

const statCards = computed(() => [
  {
    title: 'Total Students',
    value: stats.value?.total_students ?? 0,
    icon: Users,
    trend: '+12%',
    color: 'text-blue-400',
  },
  {
    title: 'Active Students',
    value: stats.value?.active_students ?? 0,
    icon: GraduationCap,
    trend: '+5%',
    color: 'text-green-400',
  },
  {
    title: 'Total Classes',
    value: stats.value?.total_classes ?? 0,
    icon: BookOpen,
    trend: '0%',
    color: 'text-purple-400',
  },
  {
    title: 'Avg Score',
    value: Math.round(stats.value?.average_score ?? 0),
    icon: TrendingUp,
    trend: '+2%',
    color: 'text-orange-400',
  },
])
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-white">Dashboard</h1>
      <p class="text-white/60">Welcome back, Administrator</p>
    </div>

    <!-- Loading state -->
    <div v-if="isPending" class="flex h-64 items-center justify-center">
      <Loader2 class="h-8 w-8 animate-spin text-primary" />
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="rounded-lg border border-red-500/20 bg-red-500/10 p-4 text-red-400">
      Failed to load stats: {{ error.message }}
    </div>

    <!-- Stats grid -->
    <div v-else class="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
      <Card
        v-for="card in statCards"
        :key="card.title"
        class="border-white/10 bg-white/[0.02] p-6"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-white/60">{{ card.title }}</p>
            <p class="mt-1 text-3xl font-bold text-white">{{ card.value }}</p>
          </div>
          <div :class="['rounded-lg bg-white/5 p-3', card.color]">
            <component :is="card.icon" class="h-6 w-6" />
          </div>
        </div>
        <div class="mt-4 flex items-center gap-2">
          <Badge variant="secondary" class="text-xs">
            {{ card.trend }}
          </Badge>
          <span class="text-xs text-white/40">from last month</span>
        </div>
      </Card>
    </div>

    <!-- Recent activity -->
    <Card class="border-white/10 bg-white/[0.02] p-6">
      <h2 class="text-lg font-semibold text-white">Recent Activity</h2>
      <p class="text-sm text-white/60">Latest updates from your classroom</p>
      
      <div class="mt-6 space-y-4">
        <div
          v-for="i in 5"
          :key="i"
          class="flex items-center gap-4 border-b border-white/5 pb-4 last:border-0"
        >
          <div class="h-8 w-8 rounded-full bg-primary/20" />
          <div class="flex-1">
            <p class="text-sm text-white">Student {{ i }} checked in</p>
            <p class="text-xs text-white/40">{{ i }} minutes ago</p>
          </div>
          <Badge variant="secondary">+10 points</Badge>
        </div>
      </div>
    </Card>
  </div>
</template>
