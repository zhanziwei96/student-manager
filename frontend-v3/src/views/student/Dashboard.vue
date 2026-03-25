<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores'
import { useStudentProfile } from '@/composables/useStudentProfile'
import { useStudents, useStudentScoreLogs } from '@/composables'
import { Card, Badge } from '@/components/ui'
import { Star, TrendingUp, Users, Award, Loader2, AlertCircle } from 'lucide-vue-next'

const authStore = useAuthStore()
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
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-white">学生仪表板</h1>
      <p class="text-white/60">欢迎回来，{{ authStore.user?.name }}</p>
    </div>

    <!-- Loading state -->
    <div v-if="isPending" class="flex h-64 items-center justify-center">
      <Loader2 class="h-8 w-8 animate-spin text-primary" />
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="rounded-lg border border-red-500/20 bg-red-500/10 p-4 text-red-400">
      <div class="flex items-center gap-2">
        <AlertCircle class="h-5 w-5" />
        <span>加载数据失败: {{ error.message }}</span>
      </div>
    </div>

    <!-- No data state -->
    <div v-else-if="!currentStudent" class="rounded-lg border border-white/10 bg-white/[0.02] p-8 text-center">
      <p class="text-white/60">未找到您的学生信息</p>
    </div>

    <template v-else>
      <!-- Score card -->
      <Card class="relative overflow-hidden border-white/10 bg-gradient-to-br from-primary/20 to-accent-cyan/20 p-8">
        <div class="relative z-10">
          <div class="flex items-center gap-3">
            <Star class="h-8 w-8 text-yellow-400" />
            <div>
              <p class="text-sm text-white/80">我的分数</p>
              <p class="text-5xl font-bold text-white">{{ currentStudent.score }}</p>
            </div>
          </div>
          <div class="mt-4 flex items-center gap-2">
            <Badge variant="secondary" class="bg-white/20">
              <TrendingUp class="mr-1 h-3 w-3" />
              排名 {{ rank }}
            </Badge>
          </div>
        </div>
        <!-- Background decoration -->
        <div class="absolute -right-10 -top-10 h-40 w-40 rounded-full bg-white/5 blur-2xl" />
        <div class="absolute -bottom-10 -left-10 h-40 w-40 rounded-full bg-white/5 blur-2xl" />
      </Card>

      <!-- Stats grid -->
      <div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <Card class="border-white/10 bg-white/[0.02] p-6">
          <div class="flex items-center gap-3">
            <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-500/20">
              <Users class="h-5 w-5 text-blue-400" />
            </div>
            <div>
              <p class="text-sm text-white/60">班级</p>
              <p class="font-medium text-white">{{ currentStudent.class_name }}</p>
            </div>
          </div>
        </Card>
        <Card class="border-white/10 bg-white/[0.02] p-6">
          <div class="flex items-center gap-3">
            <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-500/20">
              <Award class="h-5 w-5 text-purple-400" />
            </div>
            <div>
              <p class="text-sm text-white/60">学号</p>
              <p class="font-medium text-white">{{ currentStudent.student_id }}</p>
            </div>
          </div>
        </Card>
        <Card class="border-white/10 bg-white/[0.02] p-6">
          <div class="flex items-center gap-3">
            <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-green-500/20">
              <TrendingUp class="h-5 w-5 text-green-400" />
            </div>
            <div>
              <p class="text-sm text-white/60">状态</p>
              <Badge :variant="currentStudent.is_account_enabled ? 'success' : 'secondary'">
                {{ currentStudent.is_account_enabled ? '账户启用' : '账户禁用' }}
              </Badge>
            </div>
          </div>
        </Card>
      </div>

      <!-- Recent activity -->
      <Card class="border-white/10 bg-white/[0.02] p-6">
        <h2 class="text-lg font-semibold text-white">最近活动</h2>
        <p class="text-sm text-white/60">最新的分数变化</p>
        
        <!-- Loading state -->
        <div v-if="logsLoading" class="mt-6 flex h-32 items-center justify-center">
          <Loader2 class="h-6 w-6 animate-spin text-primary" />
        </div>
        
        <!-- Score logs list -->
        <div v-else-if="scoreLogs && scoreLogs.length > 0" class="mt-6 space-y-4">
          <div v-for="log in scoreLogs.slice(0, 5)" :key="log.id" 
               class="flex items-center justify-between rounded-lg border border-white/5 bg-white/[0.02] p-4">
            <div class="flex items-center gap-3">
              <div class="flex h-8 w-8 items-center justify-center rounded-full"
                   :class="log.delta >= 0 ? 'bg-green-500/20' : 'bg-red-500/20'">
                <TrendingUp class="h-4 w-4" 
                          :class="log.delta >= 0 ? 'text-green-400' : 'text-red-400'" />
              </div>
              <div>
                <p class="text-sm text-white">{{ log.reason || '分数变更' }}</p>
                <p class="text-xs text-white/40">{{ formatDate(log.created_at) }}</p>
              </div>
            </div>
            <Badge :variant="log.delta >= 0 ? 'success' : 'error'">
              {{ log.delta >= 0 ? '+' : '' }}{{ log.delta }}
            </Badge>
          </div>
        </div>
        
        <!-- Empty state -->
        <div v-else class="mt-6 text-center text-white/40">
          暂无分数变更记录
        </div>
      </Card>
    </template>
  </div>
</template>
