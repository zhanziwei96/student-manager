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
  if (rate >= 90) return { color: 'text-green-400', bg: 'bg-green-500/20', border: 'border-green-500/30' }
  if (rate >= 70) return { color: 'text-blue-400', bg: 'bg-blue-500/20', border: 'border-blue-500/30' }
  if (rate >= 50) return { color: 'text-orange-400', bg: 'bg-orange-500/20', border: 'border-orange-500/30' }
  return { color: 'text-red-400', bg: 'bg-red-500/20', border: 'border-red-500/30' }
})
</script>

<template>
  <div class="grid gap-4 grid-cols-2 lg:grid-cols-4">
    <!-- 总人数 - Blue Theme -->
    <Card class="p-4 border-blue-500/20 bg-gradient-to-br from-blue-500/10 to-blue-500/5">
      <div class="flex items-start justify-between">
        <div>
          <p class="text-xs font-medium text-blue-400/80 uppercase tracking-wider">
            班级人数
          </p>
          <p class="text-2xl font-bold text-white mt-1">
            {{ stats.total }}
          </p>
          <p class="text-xs text-white/50 mt-0.5">
            名学生
          </p>
        </div>
        <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-500/20">
          <Users class="h-5 w-5 text-blue-400" />
        </div>
      </div>
    </Card>

    <!-- 已签到 - Green Theme -->
    <Card class="p-4 border-green-500/20 bg-gradient-to-br from-green-500/10 to-green-500/5">
      <div class="flex items-start justify-between">
        <div>
          <p class="text-xs font-medium text-green-400/80 uppercase tracking-wider">
            已签到
          </p>
          <div class="flex items-baseline gap-2 mt-1">
            <p class="text-2xl font-bold text-green-400">
              {{ stats.checkedIn }}
            </p>
            <span
              v-if="stats.total > 0"
              class="text-xs font-medium px-1.5 py-0.5 rounded-full bg-green-500/20 text-green-400"
            >
              {{ checkinRate }}%
            </span>
          </div>
          <p class="text-xs text-white/50 mt-0.5">
            已完成签到
          </p>
        </div>
        <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-green-500/20">
          <CheckCircle class="h-5 w-5 text-green-400" />
        </div>
      </div>
    </Card>

    <!-- 未签到 - Orange/Red Theme -->
    <Card
      class="p-4 border-orange-500/20 bg-gradient-to-br from-orange-500/10 to-orange-500/5"
      :class="stats.notCheckedIn === 0 ? 'opacity-60' : ''"
    >
      <div class="flex items-start justify-between">
        <div>
          <p class="text-xs font-medium text-orange-400/80 uppercase tracking-wider">
            未签到
          </p>
          <p class="text-2xl font-bold text-orange-400 mt-1">
            {{ stats.notCheckedIn }}
          </p>
          <p class="text-xs text-white/50 mt-0.5">
            待签到学生
          </p>
        </div>
        <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-orange-500/20">
          <UserX class="h-5 w-5 text-orange-400" />
        </div>
      </div>
    </Card>

    <!-- 签到率 - Purple Theme (动态颜色) -->
    <Card
      :class="`p-4 bg-gradient-to-br from-purple-500/10 to-purple-500/5 ${rateTheme.border} ${rateTheme.bg.replace('/20', '/10')}`"
    >
      <div class="flex items-start justify-between">
        <div>
          <p class="text-xs font-medium text-purple-400/80 uppercase tracking-wider">
            签到率
          </p>
          <div class="flex items-baseline gap-1 mt-1">
            <p
              class="text-2xl font-bold"
              :class="rateTheme.color"
            >
              {{ checkinRate }}
            </p>
            <span
              class="text-lg font-semibold"
              :class="rateTheme.color"
            >%</span>
          </div>
          <p class="text-xs text-white/50 mt-0.5">
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
      <div class="mt-3 h-1.5 bg-white/10 rounded-full overflow-hidden">
        <div
          class="h-full rounded-full transition-all duration-500"
          :class="rateTheme.bg.replace('/20', '')"
          :style="{ width: `${checkinRate}%` }"
        />
      </div>
    </Card>
  </div>
</template>
