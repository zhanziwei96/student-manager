<script setup lang="ts">
import { MessageCircle, AlertTriangle, UserX, Plus, Minus, HelpCircle } from 'lucide-vue-next'
import type { Component } from 'vue'

/**
 * 快速分数按钮组件
 * 
 * 用于教师页面快速给学生加减分
 */

interface Props {
  label: string
  score: number
  icon: string
  disabled?: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  click: []
}>()

// 图标映射
const iconMap: Record<string, Component> = {
  MessageCircle,
  AlertTriangle,
  UserX,
  Plus,
  Minus,
  HelpCircle,
}

const iconComponent = iconMap[props.icon] || HelpCircle
const isPositive = props.score > 0
</script>

<template>
  <button
    class="group relative flex flex-col items-center gap-1 rounded-lg py-2.5 px-1 text-xs transition-all duration-200 disabled:opacity-50"
    :class="[
      isPositive 
        ? 'bg-success-soft-muted text-success-soft hover:bg-success-soft/25' 
        : 'bg-error-soft-muted text-error-soft hover:bg-error-soft/25'
    ]"
    :disabled="disabled"
    @click="emit('click')"
  >
    <component
      :is="iconComponent"
      class="h-4 w-4 opacity-80 group-hover:opacity-100"
    />
    <span class="font-medium">{{ label }}</span>
    <span class="text-[10px] opacity-70">
      {{ score > 0 ? '+' : '' }}{{ score }}
    </span>
    <!-- 光晕效果 -->
    <div 
      class="absolute inset-0 rounded-lg opacity-0 transition-opacity duration-200 group-hover:opacity-100 pointer-events-none"
      :class="isPositive ? 'shadow-[0_0_12px_rgba(115,191,105,0.25)]' : 'shadow-[0_0_12px_rgba(224,47,68,0.25)]'"
    />
  </button>
</template>
