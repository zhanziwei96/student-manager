<script setup lang="ts">
/**
 * 签到统计卡片组件
 *
 * 展示班级签到统计数据
 */
import { computed } from 'vue'
import { Card } from '@/components/ui'
import { Users, CheckCircle, Clock } from 'lucide-vue-next'

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
</script>

<template>
  <div class="grid gap-4 sm:grid-cols-3">
    <!-- 总人数 -->
    <Card class="border-white/10 bg-white/[0.02] p-4">
      <div class="flex items-center gap-3">
        <Users class="h-5 w-5 text-white/60" />
        <div>
          <p class="text-xs text-white/50">班级人数</p>
          <p class="text-xl font-bold text-white">{{ stats.total }}</p>
        </div>
      </div>
    </Card>

    <!-- 已签到 -->
    <Card class="border-white/10 bg-white/[0.02] p-4">
      <div class="flex items-center gap-3">
        <div class="flex h-8 w-8 items-center justify-center rounded-full bg-green-500/20">
          <CheckCircle class="h-4 w-4 text-green-400" />
        </div>
        <div>
          <p class="text-xs text-white/50">已签到</p>
          <div class="flex items-baseline gap-1">
            <p class="text-xl font-bold text-green-400">{{ stats.checkedIn }}</p>
            <span v-if="stats.total > 0" class="text-xs text-green-400/70">{{ checkinRate }}%</span>
          </div>
        </div>
      </div>
    </Card>

    <!-- 未签到 -->
    <Card class="border-white/10 bg-white/[0.02] p-4">
      <div class="flex items-center gap-3">
        <div class="flex h-8 w-8 items-center justify-center rounded-full bg-red-500/20">
          <Clock class="h-4 w-4 text-red-400" />
        </div>
        <div>
          <p class="text-xs text-white/50">未签到</p>
          <p class="text-xl font-bold text-red-400">{{ stats.notCheckedIn }}</p>
        </div>
      </div>
    </Card>
  </div>
</template>
