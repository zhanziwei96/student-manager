<script setup lang="ts">
import { Card } from '@/components/ui'
import { CheckCircle, Users, Clock, TrendingUp } from 'lucide-vue-next'
import { useSessionCheckinStats } from '@/composables/useCheckins'
import { useClassStats } from '@/composables/useClasses'

// Data
const { data: stats } = useSessionCheckinStats()
useClassStats()
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-5">
      <div>
        <h1 class="text-2xl font-bold text-white">
          签到统计
        </h1>
        <p class="text-white/60">
          查看当前活跃课堂的签到统计
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
  </div>
</template>
