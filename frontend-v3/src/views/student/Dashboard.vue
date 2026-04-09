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
const { data: scoreLogs, isPending: logsLoading } = useStudentScoreLogs(studentId, { limit: 0 })

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

// 统一的 Indigo 卡片样式
const getCardStyle = () => ({
  backgroundColor: 'var(--card-indigo-bg)',
  borderColor: 'var(--card-indigo-border)',
  '--tw-shadow-color': 'var(--card-indigo-shadow)',
})

const getCardIconStyle = () => ({
  backgroundColor: 'var(--card-indigo-icon-bg)',
  color: 'var(--card-indigo-icon-text)',
})

const getCardTextMutedColor = () => 'text-[#737373]'
</script>

<template>
  <div class="space-y-5 px-4">
    <!-- Header -->
    <div class="px-1">
      <h1 class="text-2xl font-medium text-black tracking-tight">
        学生仪表板
      </h1>
      <p class="text-[#a3a3a3] text-sm mt-1">
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
      class="rounded-xl border border-[#e5e5e5] bg-white p-8 text-center"
    >
      <p class="text-[#737373]">
        未找到您的学生信息
      </p>
    </div>

    <template v-else>
      <!-- Score card -->
      <Card class="relative overflow-hidden border-[#e5e5e5] p-6 mb-5">
        <div class="relative z-10">
          <div class="flex items-start justify-between">
            <div>
              <p class="text-sm text-[#737373] font-medium">
                我的分数
              </p>
              <p class="text-5xl font-medium text-black mt-1 tracking-tight">
                {{ currentStudent.score }}
              </p>
            </div>
            <div class="flex h-12 w-12 items-center justify-center rounded-xl bg-yellow-400/20">
              <Star class="h-6 w-6 text-yellow-300 fill-yellow-300" />
            </div>
          </div>
          <div class="mt-5 flex items-center gap-2">
            <button
              class="inline-flex items-center gap-1.5 rounded-full bg-[#f5f5f5] px-3 py-1.5 text-xs font-medium text-black transition-colors hover:bg-[#e5e5e5]"
              @click="router.push('/student/leaderboard')"
            >
              <TrendingUp class="h-3.5 w-3.5" />
              排名 {{ rank }}
            </button>
            <button
              class="inline-flex items-center gap-1.5 rounded-full bg-[#f5f5f5] px-3 py-1.5 text-xs font-medium text-black transition-colors hover:bg-[#e5e5e5]"
              @click="router.push('/student/leaderboard')"
            >
              <Trophy class="h-3.5 w-3.5" />
              查看排行榜
            </button>
          </div>
        </div>
      </Card>

      <!-- Stats grid -->
      <div class="grid grid-cols-2 gap-3 sm:gap-4 mb-5">
        <!-- 班级卡片 -->
        <Card
          class="group relative overflow-hidden p-4"
          :style="getCardStyle()"
        >
          <div class="relative z-10">
            <div
              class="flex h-10 w-10 items-center justify-center rounded-xl transition-transform group-hover:scale-110"
              :style="getCardIconStyle()"
            >
              <Users class="h-5 w-5" />
            </div>
            <p class="mt-3 text-xs font-medium" :class="getCardTextMutedColor()">
              班级
            </p>
            <p class="text-sm font-medium text-black mt-0.5 truncate">
              {{ currentStudent.class_name }}
            </p>
          </div>
        </Card>

        <!-- 学号卡片 -->
        <Card
          class="group relative overflow-hidden p-4"
          :style="getCardStyle()"
        >
          <div class="relative z-10">
            <div
              class="flex h-10 w-10 items-center justify-center rounded-xl transition-transform group-hover:scale-110"
              :style="getCardIconStyle()"
            >
              <Award class="h-5 w-5" />
            </div>
            <p class="mt-3 text-xs font-medium" :class="getCardTextMutedColor()">
              学号
            </p>
            <p class="text-sm font-medium text-black mt-0.5 font-mono tracking-wide">
              {{ currentStudent.student_id }}
            </p>
          </div>
        </Card>

        <!-- 状态卡片 - 跨两列 -->
        <Card
          class="group col-span-2 relative overflow-hidden p-4"
          :style="getCardStyle()"
        >
          <div class="relative z-10 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div
                class="flex h-10 w-10 items-center justify-center rounded-xl transition-transform group-hover:scale-110"
                :style="getCardIconStyle()"
              >
                <TrendingUp class="h-5 w-5" />
              </div>
              <div>
                <p class="text-xs font-medium" :class="getCardTextMutedColor()">
                  账户状态
                </p>
                <p class="text-sm font-medium text-black mt-0.5">
                  {{ currentStudent.is_account_enabled ? '账户启用' : '账户禁用' }}
                </p>
              </div>
            </div>
            <div
              class="h-2.5 w-2.5 rounded-full transition-all"
              :class="currentStudent.is_account_enabled ? 'bg-green-400' : 'bg-gray-400'"
            />
          </div>
        </Card>
      </div>

      <!-- Recent activity -->
      <Card class="border-[#e5e5e5] bg-white p-5 mt-5">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-lg font-medium text-black">
              最近活动
            </h2>
            <p class="text-xs text-[#a3a3a3] mt-0.5">
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
          class="mt-5 space-y-2.5 max-h-96 overflow-y-auto pr-1"
        >
          <div
            v-for="(log, index) in scoreLogs"
            :key="log.id"
            class="group flex items-center justify-between rounded-xl border border-[#e5e5e5] bg-[#fafafa] p-3.5 transition-colors hover:bg-[#f5f5f5] hover:border-[#d5d5d5]"
            :style="{ animationDelay: `${index * 50}ms` }"
          >
            <div class="flex items-center gap-3">
              <div
                class="flex h-8 w-8 items-center justify-center rounded-lg transition-transform group-hover:scale-110"
                :class="log.delta >= 0 ? 'bg-emerald-500/25' : 'bg-rose-500/25'"
              >
                <TrendingUp
                  class="h-4 w-4 transition-colors"
                  :class="log.delta >= 0 ? 'text-emerald-300' : 'text-rose-300'"
                />
              </div>
              <div>
                <p class="text-sm text-black/90 line-clamp-1">
                  {{ log.reason || '分数变更' }}
                </p>
                <p class="text-[11px] text-[#a3a3a3] mt-0.5">
                  {{ formatDate(log.created_at) }}
                </p>
              </div>
            </div>
            <span
              class="text-sm font-medium tabular-nums"
              :class="log.delta >= 0 ? 'text-emerald-400' : 'text-rose-400'"
            >
              {{ log.delta >= 0 ? '+' : '' }}{{ log.delta }}
            </span>
          </div>
        </div>

        <!-- Empty state -->
        <div
          v-else
          class="mt-8 flex flex-col items-center justify-center py-6 text-[#a3a3a3]"
        >
          <div class="h-12 w-12 rounded-full bg-[#f5f5f5] flex items-center justify-center mb-3">
            <TrendingUp class="h-5 w-5 opacity-50" />
          </div>
          <p class="text-sm">暂无分数变更记录</p>
        </div>
      </Card>
    </template>
  </div>
</template>
