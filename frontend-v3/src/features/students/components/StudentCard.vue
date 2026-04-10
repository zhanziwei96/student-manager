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

const getScoreColorClass = (score: number): string => {
  if (score >= 80) return 'text-[#16a34a]'
  if (score >= 60) return 'text-[#3b82f6]'
  if (score >= 40) return 'text-[#ca8a04]'
  return 'text-[#dc2626]'
}
</script>

<template>
  <Card
    class="group relative overflow-hidden p-4 border-[#e5e5e5] bg-white"
    :class="student.checkin_status === 'checked_in' ? 'ring-1 ring-green-500/50' : ''"
  >
    <!-- 学生信息 -->
    <div class="relative z-10">
      <div class="flex items-start justify-between mb-4">
        <div class="flex items-center gap-3">
          <div
            class="flex h-11 w-11 items-center justify-center rounded-xl bg-[#f5f5f5] text-[#525252]"
          >
            <User class="h-5 w-5" />
          </div>
          <div class="min-w-0">
            <p class="font-medium text-black truncate">
              {{ student.name }}
            </p>
            <p class="text-xs text-[#737373]">
              {{ student.student_id }}
            </p>
            <p class="text-[10px] text-[#a3a3a3] truncate">
              {{ student.class_name }}
            </p>
          </div>
        </div>
        <Badge
          :variant="student.checkin_status === 'checked_in' ? 'success' : 'outline'"
          class="text-[10px] px-1.5 py-0.5"
        >
          {{ student.checkin_status === 'checked_in' ? '已签到' : '未签到' }}
        </Badge>
      </div>

      <!-- 分数显示 -->
      <div class="mb-4 flex items-baseline gap-2">
        <p class="text-xs text-[#a3a3a3]">
          当前分数
        </p>
        <p class="text-2xl font-medium" :class="getScoreColorClass(student.score)">
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
          class="flex-1 inline-flex items-center justify-center gap-1.5 rounded-lg py-2 px-3 text-xs font-medium transition-colors disabled:opacity-50 bg-[#e5e5e5] text-[#262626] hover:bg-[#d4d4d4] border border-[#d4d4d4]"
          :disabled="isUpdating"
          @click="$emit('open-score-dialog', student, 10, '加分')"
        >
          <Plus class="h-3.5 w-3.5" />
          加分
        </button>
        <button
          class="flex-1 inline-flex items-center justify-center gap-1.5 rounded-lg py-2 px-3 text-xs font-medium transition-colors disabled:opacity-50 bg-[rgba(245,158,11,0.15)] text-[#92400e] hover:bg-[rgba(245,158,11,0.25)] border border-[rgba(245,158,11,0.3)]"
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
