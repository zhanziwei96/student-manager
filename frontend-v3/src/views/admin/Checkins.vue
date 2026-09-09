<script setup lang="ts">
import { Card } from '@/components/ui'
import { CheckCircle, Users, Clock, TrendingUp } from 'lucide-vue-next'
import { useSessionCheckinStats } from '@/composables/useCheckins'

// Data
const { data: stats } = useSessionCheckinStats()
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-5">
      <div>
        <h1 class="text-2xl font-medium text-black">
          签到统计
        </h1>
        <p class="text-[#737373]">
          查看当前活跃课堂的签到统计
        </p>
      </div>
    </div>

    <!-- Stats Cards - CSS变量主题色 -->
    <div class="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4 mb-5">
      <!-- 总学生数 -->
      <Card class="relative overflow-hidden p-4 border-[#e5e5e5] bg-[#fafafa]">
        <div class="relative z-10 flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-[#f5f5f5]">
            <Users class="h-5 w-5 text-[#525252]" />
          </div>
          <div>
            <p class="text-xs text-[#a3a3a3]">
              总学生数
            </p>
            <p class="text-xl font-medium text-black">
              {{ stats?.total || 0 }}
            </p>
          </div>
        </div>
      </Card>

      <!-- 已签到 -->
      <Card class="relative overflow-hidden p-4 border-[#e5e5e5] bg-[#fafafa]">
        <div class="relative z-10 flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-[#f5f5f5]">
            <CheckCircle class="h-5 w-5 text-[#525252]" />
          </div>
          <div>
            <p class="text-xs text-[#a3a3a3]">
              已签到
            </p>
            <p class="text-xl font-medium text-[#16a34a]">
              {{ stats?.checked_in || 0 }}
            </p>
          </div>
        </div>
      </Card>

      <!-- 未签到 -->
      <Card class="relative overflow-hidden p-4 border-[#e5e5e5] bg-[#fafafa]">
        <div class="relative z-10 flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-[#f5f5f5]">
            <Clock class="h-5 w-5 text-[#525252]" />
          </div>
          <div>
            <p class="text-xs text-[#a3a3a3]">
              未签到
            </p>
            <p class="text-xl font-medium text-[#dc2626]">
              {{ stats?.not_checked_in || 0 }}
            </p>
          </div>
        </div>
      </Card>

      <!-- 签到率 -->
      <Card class="relative overflow-hidden p-4 border-[#e5e5e5] bg-[#fafafa]">
        <div class="relative z-10 flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-[#f5f5f5]">
            <TrendingUp class="h-5 w-5 text-[#525252]" />
          </div>
          <div>
            <p class="text-xs text-[#a3a3a3]">
              签到率
            </p>
            <p class="text-xl font-medium text-[#3b82f6]">
              {{ stats?.rate || 0 }}%
            </p>
          </div>
        </div>
      </Card>
    </div>
  </div>
</template>
