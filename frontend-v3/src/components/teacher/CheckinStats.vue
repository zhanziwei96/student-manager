<script setup lang="ts">
/**
 * 签到统计卡片组件
 *
 * 展示班级签到统计数据 - 使用 blue/green/purple/orange 主题色
 */
import { computed } from 'vue'
import { Card } from '@/components/ui'
import { Users, CheckCircle, UserX, TrendingUp } from 'lucide-vue-next'

interface Stats {
  total: number
  checkedIn: number
  notCheckedIn: number
}

const props = defineProps<{
  stats: Stats
}>()

// 签到率
const checkinRate = computed(() => {
  if (props.stats.total === 0) return 0
  return Math.round((props.stats.checkedIn / props.stats.total) * 100)
})

// 获取签到率颜色主题
const rateTheme = computed(() => {
  const rate = checkinRate.value
  if (rate >= 90) return { color: 'text-[#16a34a]', bg: 'bg-[rgba(34,197,94,0.15)]', border: 'border-[rgba(34,197,94,0.3)]' }
  if (rate >= 70) return { color: 'text-[#3b82f6]', bg: 'bg-[rgba(59,130,246,0.15)]', border: 'border-[rgba(59,130,246,0.3)]' }
  if (rate >= 50) return { color: 'text-[#d97706]', bg: 'bg-[rgba(245,158,11,0.15)]', border: 'border-[rgba(245,158,11,0.3)]' }
  return { color: 'text-[#dc2626]', bg: 'bg-[rgba(239,68,68,0.15)]', border: 'border-[rgba(239,68,68,0.3)]' }
})
</script>

<template>
  <div class="grid gap-4 grid-cols-2 lg:grid-cols-4">
    <!-- 总人数 - Blue Theme -->
    <Card class="p-4 border-[rgba(59,130,246,0.3)] bg-[rgba(59,130,246,0.08)]">
      <div class="flex items-start justify-between">
        <div>
          <p class="text-xs font-medium text-[#3b82f6] uppercase tracking-wider">
            班级人数
          </p>
          <p class="text-2xl font-medium text-black mt-1">
            {{ stats.total }}
          </p>
          <p class="text-xs text-[#a3a3a3] mt-0.5">
            名学生
          </p>
        </div>
        <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-[rgba(59,130,246,0.15)]">
          <Users class="h-5 w-5 text-[#3b82f6]" />
        </div>
      </div>
    </Card>

    <!-- 已签到 - Green Theme -->
    <Card class="p-4 border-[rgba(34,197,94,0.3)] bg-[rgba(34,197,94,0.08)]">
      <div class="flex items-start justify-between">
        <div>
          <p class="text-xs font-medium text-[#16a34a] uppercase tracking-wider">
            已签到
          </p>
          <div class="flex items-baseline gap-2 mt-1">
            <p class="text-2xl font-medium text-[#16a34a]">
              {{ stats.checkedIn }}
            </p>
            <span
              v-if="stats.total > 0"
              class="text-xs font-medium px-1.5 py-0.5 rounded-full bg-[rgba(34,197,94,0.15)] text-[#16a34a]"
            >
              {{ checkinRate }}%
            </span>
          </div>
          <p class="text-xs text-[#a3a3a3] mt-0.5">
            已完成签到
          </p>
        </div>
        <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-[rgba(34,197,94,0.15)]">
          <CheckCircle class="h-5 w-5 text-[#16a34a]" />
        </div>
      </div>
    </Card>

    <!-- 未签到 - Orange/Red Theme -->
    <Card
      class="p-4 border-[rgba(245,158,11,0.3)] bg-[rgba(245,158,11,0.08)]"
      :class="stats.notCheckedIn === 0 ? 'opacity-60' : ''"
    >
      <div class="flex items-start justify-between">
        <div>
          <p class="text-xs font-medium text-[#d97706] uppercase tracking-wider">
            未签到
          </p>
          <p class="text-2xl font-medium text-[#d97706] mt-1">
            {{ stats.notCheckedIn }}
          </p>
          <p class="text-xs text-[#a3a3a3] mt-0.5">
            待签到学生
          </p>
        </div>
        <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-[rgba(245,158,11,0.15)]">
          <UserX class="h-5 w-5 text-[#d97706]" />
        </div>
      </div>
    </Card>

    <!-- 签到率 - Purple Theme (动态颜色) -->
    <Card
      :class="`p-4 bg-[rgba(147,51,234,0.08)] ${rateTheme.border} ${rateTheme.bg}`"
    >
      <div class="flex items-start justify-between">
        <div>
          <p class="text-xs font-medium text-[#9333ea] uppercase tracking-wider">
            签到率
          </p>
          <div class="flex items-baseline gap-1 mt-1">
            <p
              class="text-2xl font-medium"
              :class="rateTheme.color"
            >
              {{ checkinRate }}
            </p>
            <span
              class="text-lg font-medium"
              :class="rateTheme.color"
            >%</span>
          </div>
          <p class="text-xs text-[#a3a3a3] mt-0.5">
            整体出勤率
          </p>
        </div>
        <div
          class="flex h-10 w-10 items-center justify-center rounded-xl"
          :class="rateTheme.bg"
        >
          <TrendingUp class="h-5 w-5" :class="rateTheme.color" />
        </div>
      </div>

      <!-- 迷你进度条 -->
      <div class="mt-3 h-1.5 bg-[#f5f5f5] rounded-full overflow-hidden">
        <div
          class="h-full rounded-full transition-all duration-500"
          :class="rateTheme.bg"
          :style="{ width: `${checkinRate}%` }"
        />
      </div>
    </Card>
  </div>
</template>
