<script setup lang="ts">
import { ref, computed } from 'vue'
import { Card, Button, Badge, Input, Select } from '@/components/ui'
import { CheckCircle, Search, Users, Clock, Calendar, Loader2, TrendingUp } from 'lucide-vue-next'
import { useCheckinStats, useTodayCheckins } from '@/composables/useCheckins'
import { useClassStats } from '@/composables/useClasses'

// Data
const { data: stats, isPending: isLoadingStats } = useCheckinStats()
const { data: checkins, isPending: isLoadingCheckins } = useTodayCheckins()
const { data: classes } = useClassStats()

// Filter
const selectedClass = ref('')
const searchQuery = ref('')

const filteredCheckins = computed(() => {
  if (!checkins.value) return []
  let result = checkins.value
  
  if (selectedClass.value) {
    result = result.filter(c => c.class_name === selectedClass.value)
  }
  
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(c => 
      c.student_id.toLowerCase().includes(query) ||
      c.student_name.toLowerCase().includes(query)
    )
  }
  
  return result
})

// Format time
const formatTime = (timeStr: string) => {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// Score color
const getScoreColor = (points: number) => {
  if (points >= 10) return 'text-green-400'
  if (points >= 5) return 'text-yellow-400'
  return 'text-white/60'
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold text-white">签到管理</h1>
        <p class="text-white/60">查看今日签到记录和统计</p>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <Card class="border-white/10 bg-white/[0.02] p-4">
        <div class="flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/20">
            <Users class="h-5 w-5 text-primary" />
          </div>
          <div>
            <p class="text-xs text-white/50">总学生数</p>
            <p class="text-xl font-bold text-white">{{ stats?.total || 0 }}</p>
          </div>
        </div>
      </Card>
      
      <Card class="border-white/10 bg-white/[0.02] p-4">
        <div class="flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-green-500/20">
            <CheckCircle class="h-5 w-5 text-green-400" />
          </div>
          <div>
            <p class="text-xs text-white/50">已签到</p>
            <p class="text-xl font-bold text-green-400">{{ stats?.checked_in || 0 }}</p>
          </div>
        </div>
      </Card>
      
      <Card class="border-white/10 bg-white/[0.02] p-4">
        <div class="flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-red-500/20">
            <Clock class="h-5 w-5 text-red-400" />
          </div>
          <div>
            <p class="text-xs text-white/50">未签到</p>
            <p class="text-xl font-bold text-red-400">{{ stats?.not_checked_in || 0 }}</p>
          </div>
        </div>
      </Card>
      
      <Card class="border-white/10 bg-white/[0.02] p-4">
        <div class="flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-500/20">
            <TrendingUp class="h-5 w-5 text-blue-400" />
          </div>
          <div>
            <p class="text-xs text-white/50">签到率</p>
            <p class="text-xl font-bold text-blue-400">{{ stats?.rate || 0 }}%</p>
          </div>
        </div>
      </Card>
    </div>

    <!-- Filters -->
    <div class="flex flex-col gap-4 sm:flex-row">
      <div class="relative flex-1">
        <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/50" />
        <Input
          v-model="searchQuery"
          placeholder="搜索学生姓名或学号..."
          class="pl-10"
        />
      </div>
      <Select v-model="selectedClass" class="w-full sm:w-48">
        <option value="">所有班级</option>
        <option v-for="cls in classes" :key="cls.name" :value="cls.name">
          {{ cls.name }}
        </option>
      </Select>
    </div>

    <!-- Checkin List -->
    <Card class="border-white/10 bg-white/[0.02]">
      <div class="p-4 border-b border-white/10">
        <h3 class="font-medium text-white">今日签到记录</h3>
        <p class="text-sm text-white/50">共 {{ filteredCheckins.length }} 条记录</p>
      </div>
      
      <div v-if="isLoadingCheckins" class="flex h-64 items-center justify-center">
        <Loader2 class="h-8 w-8 animate-spin text-primary" />
      </div>
      
      <div v-else-if="filteredCheckins.length > 0" class="divide-y divide-white/5">
        <div
          v-for="checkin in filteredCheckins"
          :key="checkin.id"
          class="flex items-center justify-between p-4 hover:bg-white/5"
        >
          <div class="flex items-center gap-4">
            <div class="flex h-10 w-10 items-center justify-center rounded-full bg-green-500/20">
              <CheckCircle class="h-5 w-5 text-green-400" />
            </div>
            <div>
              <p class="font-medium text-white">{{ checkin.student_name }}</p>
              <p class="text-sm text-white/50">{{ checkin.student_id }}</p>
            </div>
          </div>
          
          <div class="flex items-center gap-6">
            <div class="text-right">
              <p class="text-sm text-white/70">{{ checkin.class_name }}</p>
              <p class="text-xs text-white/40">{{ formatTime(checkin.check_in_time) }}</p>
            </div>
            <Badge :variant="checkin.points_earned > 0 ? 'success' : 'secondary'" class="min-w-[60px] justify-center">
              +{{ checkin.points_earned }} 分
            </Badge>
          </div>
        </div>
      </div>
      
      <div v-else class="flex h-64 flex-col items-center justify-center text-white/60">
        <Calendar class="mb-4 h-12 w-12 opacity-50" />
        <p>暂无签到记录</p>
        <p class="mt-1 text-sm text-white/40">今日还没有学生签到</p>
      </div>
    </Card>
  </div>
</template>
