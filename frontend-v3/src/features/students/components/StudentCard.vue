<script setup lang="ts">
import { Card, Badge } from '@/components/ui'
import { Plus, Minus, User } from 'lucide-vue-next'
import QuickScoreButton from './QuickScoreButton.vue'
import type { Student, QuickScoreOption } from '../types'

/**
 * 学生卡片组件
 *
 * 展示学生基本信息、分数和快速操作按钮
 */

interface Props {
  student: Student
  quickScoreOptions: QuickScoreOption[]
  isUpdating?: boolean
  updatingStudentId?: string
}

defineProps<Props>()

defineEmits<{
  'quick-score': [student: Student, score: number, reason: string]
  'open-score-dialog': [student: Student, defaultScore: number, defaultReason: string]
}>()

// 统一的 Indigo 卡片样式
const cardStyle = {
  backgroundColor: 'var(--card-indigo-bg)',
  borderColor: 'var(--card-indigo-border)',
  '--tw-shadow-color': 'var(--card-indigo-shadow)',
} as Record<string, string>

const cardIconStyle = {
  backgroundColor: 'var(--card-indigo-icon-bg)',
  color: 'var(--card-indigo-icon-text)',
}

const cardGlowStyle = {
  backgroundColor: 'var(--card-indigo-glow)',
}

const getScoreColorClass = (score: number): string => {
  if (score >= 80) return 'text-green-400'
  if (score >= 60) return 'text-blue-400'
  if (score >= 40) return 'text-yellow-400'
  return 'text-red-400'
}
</script>

<template>
  <Card
    class="group relative overflow-hidden p-4 shadow-lg transition-all duration-300 hover:scale-[1.02]"
    :style="cardStyle"
    :class="student.checkin_status === 'checked_in' ? 'ring-1 ring-green-500/50' : ''"
  >
    <!-- 背景装饰 -->
    <div
      class="absolute -right-4 -bottom-4 h-16 w-16 rounded-full blur-2xl transition-colors opacity-30"
      :style="cardGlowStyle"
    />

    <!-- 学生信息 -->
    <div class="relative z-10">
      <div class="flex items-start justify-between mb-4">
        <div class="flex items-center gap-3">
          <div
            class="flex h-11 w-11 items-center justify-center rounded-xl shadow-inner transition-transform group-hover:scale-110"
            :style="cardIconStyle"
          >
            <User class="h-5 w-5" />
          </div>
          <div class="min-w-0">
            <p class="font-medium text-white truncate">
              {{ student.name }}
            </p>
            <p class="text-xs text-white/60">
              {{ student.student_id }}
            </p>
            <p class="text-[10px] text-white/40 truncate">
              {{ student.class_name }}
            </p>
          </div>
        </div>
        <Badge
          :variant="student.checkin_status === 'checked_in' ? 'success' : 'secondary'"
          class="text-[10px] px-1.5 py-0.5"
        >
          {{ student.checkin_status === 'checked_in' ? '已签到' : '未签到' }}
        </Badge>
      </div>

      <!-- 分数显示 -->
      <div class="mb-4 flex items-baseline gap-2">
        <p class="text-xs text-white/50">
          当前分数
        </p>
        <p class="text-2xl font-bold" :class="getScoreColorClass(student.score)">
          {{ student.score }}
        </p>
      </div>

      <!-- 快速操作按钮 -->
      <div class="grid grid-cols-3 gap-2 mb-3">
        <QuickScoreButton
          v-for="option in quickScoreOptions"
          :key="option.label"
          :label="option.label"
          :score="option.score"
          :icon="option.icon"
          :disabled="isUpdating"
          @click="$emit('quick-score', student, option.score, option.label)"
        />
      </div>

      <!-- 自定义分数按钮 - 主题色统一 -->
      <div class="flex gap-2">
        <button
          class="flex-1 inline-flex items-center justify-center gap-1.5 rounded-lg py-2 px-3 text-xs font-medium transition-all duration-200 disabled:opacity-50 bg-blue-500/20 text-blue-300 hover:bg-blue-500/30 border border-blue-500/30"
          :disabled="isUpdating"
          @click="$emit('open-score-dialog', student, 10, '加分')"
        >
          <Plus class="h-3.5 w-3.5" />
          加分
        </button>
        <button
          class="flex-1 inline-flex items-center justify-center gap-1.5 rounded-lg py-2 px-3 text-xs font-medium transition-all duration-200 disabled:opacity-50 bg-orange-500/20 text-orange-300 hover:bg-orange-500/30 border border-orange-500/30"
          :disabled="isUpdating"
          @click="$emit('open-score-dialog', student, -10, '扣分')"
        >
          <Minus class="h-3.5 w-3.5" />
          扣分
        </button>
      </div>
    </div>
  </Card>
</template>
