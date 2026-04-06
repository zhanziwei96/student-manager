<script setup lang="ts">
import { ref, computed } from 'vue'
import { Card, Badge, Input, Select } from '@/components/ui'
import { CheckCircle, Search, Loader2, Users, Clock, TrendingUp, Calendar } from 'lucide-vue-next'
import { useCheckinStats, useTodayCheckins } from '@/composables/useCheckins'
import { useClassStats } from '@/composables/useClasses'

// Data
const { data: stats } = useCheckinStats()
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

// 获取签到记录主题色（基于索引循环使用）
const getCheckinTheme = (index: number) => {
  const themes = ['green', 'blue', 'purple', 'orange'] as const
  return themes[index % themes.length]
}

// 主题色配置
const themeColors = {
  blue: {
    border: 'border-[var(--card-blue-border)]',
    bg: 'bg-[var(--card-blue-bg)]',
    iconBg: 'bg-[var(--card-blue-icon-bg)]',
    iconText: 'text-[var(--card-blue-icon-text)]',
    glow: 'bg-[var(--card-blue-glow)]'
  },
  purple: {
    border: 'border-[var(--card-purple-border)]',
    bg: 'bg-[var(--card-purple-bg)]',
    iconBg: 'bg-[var(--card-purple-icon-bg)]',
    iconText: 'text-[var(--card-purple-icon-text)]',
    glow: 'bg-[var(--card-purple-glow)]'
  },
  green: {
    border: 'border-[var(--card-green-border)]',
    bg: 'bg-[var(--card-green-bg)]',
    iconBg: 'bg-[var(--card-green-icon-bg)]',
    iconText: 'text-[var(--card-green-icon-text)]',
    glow: 'bg-[var(--card-green-glow)]'
  },
  orange: {
    border: 'border-[var(--card-orange-border)]',
    bg: 'bg-[var(--card-orange-bg)]',
    iconBg: 'bg-[var(--card-orange-icon-bg)]',
    iconText: 'text-[var(--card-orange-icon-text)]',
    glow: 'bg-[var(--card-orange-glow)]'
  }
} as const
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-5">
      <div>
        <h1 class="text-2xl font-bold text-white">
          签到管理
        </h1>
        <p class="text-white/60">
          查看今日签到记录和统计
        </p>
      </div>
    </div>

    <!-- Stats Cards - CSS变量主题色 -->
    <div class="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4 mb-5">
      <!-- 总学生数 - purple主题 -->
      <Card class="relative overflow-hidden p-4 border-[var(--card-purple-border)] bg-[var(--card-purple-bg)]">
        <div class="relative z-10 flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--card-purple-icon-bg)]">
            <Users class="h-5 w-5 text-[var(--card-purple-icon-text)]" />
          </div>
          <div>
            <p class="text-xs text-[var(--color-text-tertiary)]">
              总学生数
            </p>
            <p class="text-xl font-bold text-white">
              {{ stats?.total || 0 }}
            </p>
          </div>
        </div>
        <div class="absolute -right-4 -bottom-4 h-16 w-16 rounded-full bg-[var(--card-purple-glow)] blur-2xl" />
      </Card>

      <!-- 已签到 - green主题 -->
      <Card class="relative overflow-hidden p-4 border-[var(--card-green-border)] bg-[var(--card-green-bg)]">
        <div class="relative z-10 flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--card-green-icon-bg)]">
            <CheckCircle class="h-5 w-5 text-[var(--card-green-icon-text)]" />
          </div>
          <div>
            <p class="text-xs text-[var(--color-text-tertiary)]">
              已签到
            </p>
            <p class="text-xl font-bold text-[var(--color-green-400)]">
              {{ stats?.checked_in || 0 }}
            </p>
          </div>
        </div>
        <div class="absolute -right-4 -bottom-4 h-16 w-16 rounded-full bg-[var(--card-green-glow)] blur-2xl" />
      </Card>

      <!-- 未签到 - red主题 -->
      <Card class="relative overflow-hidden p-4 border-[var(--color-error-muted)] bg-[var(--color-error-muted)]">
        <div class="relative z-10 flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--color-error-muted)]">
            <Clock class="h-5 w-5 text-[var(--color-error)]" />
          </div>
          <div>
            <p class="text-xs text-[var(--color-text-tertiary)]">
              未签到
            </p>
            <p class="text-xl font-bold text-[var(--color-error)]">
              {{ stats?.not_checked_in || 0 }}
            </p>
          </div>
        </div>
        <div class="absolute -right-4 -bottom-4 h-16 w-16 rounded-full bg-[var(--color-error-muted)] blur-2xl" />
      </Card>

      <!-- 签到率 - blue主题 -->
      <Card class="relative overflow-hidden p-4 border-[var(--card-blue-border)] bg-[var(--card-blue-bg)]">
        <div class="relative z-10 flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--card-blue-icon-bg)]">
            <TrendingUp class="h-5 w-5 text-[var(--card-blue-icon-text)]" />
          </div>
          <div>
            <p class="text-xs text-[var(--color-text-tertiary)]">
              签到率
            </p>
            <p class="text-xl font-bold text-[var(--color-blue-400)]">
              {{ stats?.rate || 0 }}%
            </p>
          </div>
        </div>
        <div class="absolute -right-4 -bottom-4 h-16 w-16 rounded-full bg-[var(--card-blue-glow)] blur-2xl" />
      </Card>
    </div>

    <!-- Filters -->
    <div class="flex flex-col gap-4 sm:flex-row mb-5">
      <div class="relative flex-1">
        <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/50" />
        <Input
          v-model="searchQuery"
          placeholder="搜索学生姓名或学号..."
          class="pl-10"
        />
      </div>
      <Select
        v-model="selectedClass"
        class="w-full sm:w-48"
      >
        <option value="">
          所有班级
        </option>
        <option
          v-for="cls in classes"
          :key="cls.name"
          :value="cls.name"
        >
          {{ cls.name }}
        </option>
      </Select>
    </div>

    <!-- Checkin List -->
    <Card class="border-[var(--color-border)] overflow-hidden">
      <div class="p-4 border-b border-[var(--color-divider)]">
        <h3 class="font-medium text-white">
          今日签到记录
        </h3>
        <p class="text-sm text-[var(--color-text-muted)]">
          共 {{ filteredCheckins.length }} 条记录
        </p>
      </div>

      <div
        v-if="isLoadingCheckins"
        class="flex h-64 items-center justify-center"
      >
        <Loader2 class="h-8 w-8 animate-spin text-[var(--color-primary)]" />
      </div>

      <div
        v-else-if="filteredCheckins.length > 0"
        class="divide-y divide-[var(--color-divider)]"
      >
        <!-- Mobile: 卡片视图 -->
        <div class="lg:hidden">
          <div
            v-for="(checkin, index) in filteredCheckins"
            :key="checkin.id"
            class="flex items-center justify-between p-4 hover:bg-[var(--color-background-hover)] transition-colors"
          >
            <div class="flex items-center gap-3 min-w-0">
              <div
                class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full"
                :class="themeColors[getCheckinTheme(index)].iconBg"
              >
                <CheckCircle
                  class="h-5 w-5"
                  :class="themeColors[getCheckinTheme(index)].iconText"
                />
              </div>
              <div class="min-w-0">
                <p class="font-medium text-white truncate">
                  {{ checkin.student_name }}
                </p>
                <p class="text-sm text-[var(--color-text-tertiary)]">
                  {{ checkin.student_id }}
                </p>
                <p class="text-xs text-[var(--color-text-muted)] mt-0.5">
                  {{ checkin.class_name }} · {{ formatTime(checkin.checkin_time) }}
                </p>
              </div>
            </div>

            <Badge
              variant="success"
              class="ml-2 flex-shrink-0"
            >
              已签到
            </Badge>
          </div>
        </div>

        <!-- Desktop: 表格视图 -->
        <div class="hidden lg:block">
          <div
            v-for="(checkin, index) in filteredCheckins"
            :key="checkin.id"
            class="flex items-center justify-between p-4 hover:bg-[var(--color-background-hover)] transition-colors"
          >
            <div class="flex items-center gap-4">
              <div
                class="flex h-10 w-10 items-center justify-center rounded-full"
                :class="themeColors[getCheckinTheme(index)].iconBg"
              >
                <CheckCircle
                  class="h-5 w-5"
                  :class="themeColors[getCheckinTheme(index)].iconText"
                />
              </div>
              <div>
                <p class="font-medium text-white">
                  {{ checkin.student_name }}
                </p>
                <p class="text-sm text-[var(--color-text-tertiary)]">
                  {{ checkin.student_id }}
                </p>
              </div>
            </div>

            <div class="flex items-center gap-6">
              <div class="text-right">
                <p class="text-sm text-[var(--color-text-secondary)]">
                  {{ checkin.class_name }}
                </p>
                <p class="text-xs text-[var(--color-text-muted)]">
                  {{ formatTime(checkin.checkin_time) }}
                </p>
              </div>
              <Badge
                variant="success"
                class="min-w-[60px] justify-center"
              >
                已签到
              </Badge>
            </div>
          </div>
        </div>
      </div>

      <div
        v-else
        class="flex h-64 flex-col items-center justify-center text-[var(--color-text-tertiary)]"
      >
        <Calendar class="mb-4 h-12 w-12 opacity-50" />
        <p>暂无签到记录</p>
        <p class="mt-1 text-sm text-[var(--color-text-muted)]">
          今日还没有学生签到
        </p>
      </div>
    </Card>
  </div>
</template>
