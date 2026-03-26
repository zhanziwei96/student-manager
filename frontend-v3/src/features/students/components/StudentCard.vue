<script setup lang="ts">
import { Card, Badge } from '@/components/ui'
import { Plus, Minus } from 'lucide-vue-next'
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
</script>

<template>
  <Card
    class="border-white/10 bg-white/[0.02] p-4 hover:bg-white/[0.04] transition-colors"
    :class="student.checkin_status === 'checked_in' ? 'border-green-500/30' : ''"
  >
    <!-- 学生信息 -->
    <div class="flex items-start justify-between mb-3">
      <div class="flex items-center gap-3">
        <div class="flex h-10 w-10 items-center justify-center rounded-full bg-primary/20">
          <span class="text-sm font-medium text-primary">
            {{ student.name.charAt(0).toUpperCase() }}
          </span>
        </div>
        <div>
          <p class="font-medium text-white">{{ student.name }}</p>
          <p class="text-xs text-white/60">{{ student.student_id }}</p>
          <p class="text-xs text-white/40">{{ student.class_name }}</p>
        </div>
      </div>
      <Badge :variant="student.checkin_status === 'checked_in' ? 'success' : 'secondary'" class="text-xs">
        {{ student.checkin_status === 'checked_in' ? '已签到' : '未签到' }}
      </Badge>
    </div>
    
    <!-- 分数显示 -->
    <div class="mb-3">
      <p class="text-xs text-white/40 mb-1">当前分数</p>
      <p class="text-xl font-bold text-primary">{{ student.score }}</p>
    </div>
    
    <!-- 快速操作按钮 -->
    <div class="grid grid-cols-3 gap-2">
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
    
    <!-- 自定义分数按钮 -->
    <div class="mt-3 flex gap-2">
      <button
        class="ch-button ch-button--sm ch-button--success-soft flex-1"
        :disabled="isUpdating"
        @click="$emit('open-score-dialog', student, 10, '加分')"
      >
        <Plus class="h-3.5 w-3.5" />
        加分
      </button>
      <button
        class="ch-button ch-button--sm ch-button--error-soft flex-1"
        :disabled="isUpdating"
        @click="$emit('open-score-dialog', student, -10, '扣分')"
      >
        <Minus class="h-3.5 w-3.5" />
        扣分
      </button>
    </div>
  </Card>
</template>
