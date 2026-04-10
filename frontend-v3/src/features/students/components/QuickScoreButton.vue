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
    class="group relative flex flex-col items-center gap-1 rounded-xl py-2.5 px-1 text-xs transition-colors disabled:opacity-50"
    :class="[
      isPositive
        ? 'bg-[rgba(34,197,94,0.15)] text-[#16a34a] hover:bg-[rgba(34,197,94,0.25)]'
        : 'bg-[rgba(239,68,68,0.15)] text-[#dc2626] hover:bg-[rgba(239,68,68,0.25)]'
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
  </button>
</template>
