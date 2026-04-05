<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores'
import { useStudentProfile } from '@/composables/useStudentProfile'
import { useStudents, useStudentScoreLogs } from '@/composables'
import { Card } from '@/components/ui'
import { Star, TrendingUp, Users, Award, Loader2, AlertCircle, Trophy } from 'lucide-vue-next'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()
const { data: currentStudent, isPending, error } = useStudentProfile()
const { data: allStudents } = useStudents()

// 获取分数历史记录
const studentId = computed(() => currentStudent.value?.student_id || '')
const { data: scoreLogs, isPending: logsLoading } = useStudentScoreLogs(studentId)

const rank = computed(() => {
  if (!allStudents.value || !currentStudent.value) return '-'
  const sorted = [...allStudents.value].sort((a, b) => b.score - a.score)
  const index = sorted.findIndex(s => s.id === currentStudent.value!.id)
  return index >= 0 ? `第 ${index + 1} 名` : '-'
})

// 格式化日期
function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// 获取卡片样式 - 使用 CSS 变量
type CardColor = 'blue' | 'green' | 'purple'

const getCardStyle = (color: CardColor) => {
  const varPrefix = `--card-${color}`
  return {
    backgroundColor: `var(${varPrefix}-bg)`,
    borderColor: `var(${varPrefix}-border)`,
    '--tw-shadow-color': `var(${varPrefix}-shadow)`,
  } as Record<string, string>
}

const getCardIconStyle = (color: CardColor) => {
  const varPrefix = `--card-${color}`
  return {
    backgroundColor: `var(${varPrefix}-icon-bg)`,
    color: `var(${varPrefix}-icon-text)`,
  }
}

const getCardGlowStyle = (color: CardColor) => {
  const varPrefix = `--card-${color}`
  return {
    backgroundColor: `var(${varPrefix}-glow)`,
  }
}

const getCardTextMutedColor = (color: CardColor) => {
  const colors: Record<CardColor, string> = {
    blue: 'text-blue-200/80',
    green: 'text-green-200/80',
    purple: 'text-purple-200/80',
  }
  return colors[color]
}
</script>

<template>
  <div class="space-y-5 px-4">
    <!-- Header -->
    <div class="px-1">
      <h1 class="text-2xl font-bold text-white tracking-tight">
        学生仪表板
      </h1>
      <p class="text-white/50 text-sm mt-1">
        欢迎回来，{{ authStore.user?.name }}
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
      <div class="flex items-center gap-2">
        <AlertCircle class="h-5 w-5" />
        <span>加载数据失败: {{ error.message }}</span>
      </div>
    </div>

    <!-- No data state -->
    <div
      v-else-if="!currentStudent"
      class="rounded-xl border border-white/10 bg-white/[0.03] p-8 text-center"
    >
      <p class="text-white/60">
        未找到您的学生信息
      </p>
    </div>

    <template v-else>
      <!-- Score card -->
      <Card class="relative overflow-hidden border-primary/30 bg-gradient-to-br from-primary/25 via-primary/15 to-accent-cyan/20 p-6 shadow-xl shadow-primary/10 mb-5">
        <div class="relative z-10">
          <div class="flex items-start justify-between">
            <div>
              <p class="text-sm text-white/70 font-medium">
                我的分数
              </p>
              <p class="text-5xl font-bold text-white mt-1 tracking-tight">
                {{ currentStudent.score }}
              </p>
            </div>
            <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-yellow-400/20 shadow-inner shadow-yellow-400/30">
              <Star class="h-6 w-6 text-yellow-300 fill-yellow-300" />
            </div>
          </div>
          <div class="mt-5 flex items-center gap-2">
            <button
              class="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1.5 text-xs font-medium text-white backdrop-blur-sm transition-all hover:bg-white/25 active:scale-95"
              @click="router.push('/student/leaderboard')"
            >
              <TrendingUp class="h-3.5 w-3.5" />
              排名 {{ rank }}
            </button>
            <button
              class="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1.5 text-xs font-medium text-white backdrop-blur-sm transition-all hover:bg-white/25 active:scale-95"
              @click="router.push('/student/leaderboard')"
            >
              <Trophy class="h-3.5 w-3.5" />
              查看排行榜
            </button>
          </div>
        </div>
        <!-- 动态背景装饰 -->
        <div class="absolute -right-6 -top-6 h-32 w-32 rounded-full bg-primary/30 blur-3xl" />
        <div class="absolute -bottom-8 -left-4 h-28 w-28 rounded-full bg-accent-cyan/20 blur-3xl" />
      </Card>

      <!-- Stats grid -->
      <div class="grid grid-cols-2 gap-3 sm:gap-4 mb-5">
        <!-- 班级卡片 -->
        <Card
          class="group relative overflow-hidden p-4 shadow-lg transition-all duration-300 hover:scale-[1.02]"
          :style="getCardStyle('blue')"
        >
          <div class="relative z-10">
            <div
              class="flex h-10 w-10 items-center justify-center rounded-xl shadow-inner transition-transform group-hover:scale-110"
              :style="getCardIconStyle('blue')"
            >
              <Users class="h-5 w-5" />
            </div>
            <p class="mt-3 text-xs font-medium" :class="getCardTextMutedColor('blue')">
              班级
            </p>
            <p class="text-sm font-semibold text-white mt-0.5 truncate">
              {{ currentStudent.class_name }}
            </p>
          </div>
          <div
            class="absolute -right-4 -bottom-4 h-16 w-16 rounded-full blur-2xl transition-colors group-hover:opacity-30"
            :style="getCardGlowStyle('blue')"
          />
        </Card>

        <!-- 学号卡片 -->
        <Card
          class="group relative overflow-hidden p-4 shadow-lg transition-all duration-300 hover:scale-[1.02]"
          :style="getCardStyle('purple')"
        >
          <div class="relative z-10">
            <div
              class="flex h-10 w-10 items-center justify-center rounded-xl shadow-inner transition-transform group-hover:scale-110"
              :style="getCardIconStyle('purple')"
            >
              <Award class="h-5 w-5" />
            </div>
            <p class="mt-3 text-xs font-medium" :class="getCardTextMutedColor('purple')">
              学号
            </p>
            <p class="text-sm font-semibold text-white mt-0.5 font-mono tracking-wide">
              {{ currentStudent.student_id }}
            </p>
          </div>
          <div
            class="absolute -right-4 -bottom-4 h-16 w-16 rounded-full blur-2xl transition-colors group-hover:opacity-30"
            :style="getCardGlowStyle('purple')"
          />
        </Card>

        <!-- 状态卡片 - 跨两列 -->
        <Card
          class="group col-span-2 relative overflow-hidden p-4 shadow-lg transition-all duration-300"
          :style="getCardStyle('green')"
        >
          <div class="relative z-10 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div
                class="flex h-10 w-10 items-center justify-center rounded-xl shadow-inner transition-transform group-hover:scale-110"
                :style="getCardIconStyle('green')"
              >
                <TrendingUp class="h-5 w-5" />
              </div>
              <div>
                <p class="text-xs font-medium" :class="getCardTextMutedColor('green')">
                  账户状态
                </p>
                <p class="text-sm font-semibold text-white mt-0.5">
                  {{ currentStudent.is_account_enabled ? '账户启用' : '账户禁用' }}
                </p>
              </div>
            </div>
            <div
              class="h-2.5 w-2.5 rounded-full shadow-lg transition-all"
              :class="currentStudent.is_account_enabled ? 'bg-green-400 shadow-green-400/50' : 'bg-gray-400 shadow-gray-400/50'"
            />
          </div>
          <div
            class="absolute right-0 bottom-0 h-20 w-20 rounded-full blur-2xl transition-colors group-hover:opacity-30"
            :style="getCardGlowStyle('green')"
          />
        </Card>
      </div>

      <!-- Recent activity -->
      <Card class="border-white/15 bg-white/[0.06] p-5 shadow-xl shadow-black/20 mt-5">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-lg font-semibold text-white">
              最近活动
            </h2>
            <p class="text-xs text-white/50 mt-0.5">
              最新的分数变化记录
            </p>
          </div>
          <div class="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center">
            <TrendingUp class="h-4 w-4 text-primary" />
          </div>
        </div>

        <!-- Loading state -->
        <div
          v-if="logsLoading"
          class="mt-6 flex h-32 items-center justify-center"
        >
          <Loader2 class="h-6 w-6 animate-spin text-primary" />
        </div>

        <!-- Score logs list -->
        <div
          v-else-if="scoreLogs && scoreLogs.length > 0"
          class="mt-5 space-y-2.5"
        >
          <div
            v-for="(log, index) in scoreLogs.slice(0, 5)"
            :key="log.id"
            class="group flex items-center justify-between rounded-xl border border-white/5 bg-white/[0.03] p-3.5 transition-all duration-200 hover:bg-white/[0.06] hover:border-white/10"
            :style="{ animationDelay: `${index * 50}ms` }"
          >
            <div class="flex items-center gap-3">
              <div
                class="flex h-8 w-8 items-center justify-center rounded-lg shadow-inner transition-transform group-hover:scale-110"
                :class="log.delta >= 0 ? 'bg-emerald-500/25 shadow-emerald-400/20' : 'bg-rose-500/25 shadow-rose-400/20'"
              >
                <TrendingUp
                  class="h-4 w-4 transition-colors"
                  :class="log.delta >= 0 ? 'text-emerald-300' : 'text-rose-300'"
                />
              </div>
              <div>
                <p class="text-sm text-white/90 line-clamp-1">
                  {{ log.reason || '分数变更' }}
                </p>
                <p class="text-[11px] text-white/40 mt-0.5">
                  {{ formatDate(log.created_at) }}
                </p>
              </div>
            </div>
            <span
              class="text-sm font-bold tabular-nums"
              :class="log.delta >= 0 ? 'text-emerald-400' : 'text-rose-400'"
            >
              {{ log.delta >= 0 ? '+' : '' }}{{ log.delta }}
            </span>
          </div>
        </div>

        <!-- Empty state -->
        <div
          v-else
          class="mt-8 flex flex-col items-center justify-center py-6 text-white/40"
        >
          <div class="h-12 w-12 rounded-full bg-white/5 flex items-center justify-center mb-3">
            <TrendingUp class="h-5 w-5 opacity-50" />
          </div>
          <p class="text-sm">暂无分数变更记录</p>
        </div>
      </Card>
    </template>
  </div>
</template>
