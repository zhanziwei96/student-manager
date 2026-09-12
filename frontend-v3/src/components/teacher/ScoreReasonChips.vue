<script setup lang="ts">
import { SCORE_REASON_PRESETS, type ScoreReasonPreset } from '@/lib/scoreReasons'

/**
 * 加减分常用原因快捷标签
 *
 * 点选后由父组件填入「原因 + 建议分值」；加分为绿色、减分为红色，
 * 与成绩日志里的涨跌色保持一致。
 */
const emit = defineEmits<{
  (e: 'pick', preset: ScoreReasonPreset): void
}>()
</script>

<template>
  <div class="flex flex-wrap gap-1.5">
    <button
      v-for="preset in SCORE_REASON_PRESETS"
      :key="preset.label"
      type="button"
      :data-testid="`score-preset-${preset.label}`"
      class="rounded-full border px-2.5 py-0.5 text-xs transition-colors"
      :class="preset.delta >= 0
        ? 'border-[#16a34a]/30 text-[#16a34a] hover:bg-[#16a34a]/10'
        : 'border-[#dc2626]/30 text-[#dc2626] hover:bg-[#dc2626]/10'"
      @click="emit('pick', preset)"
    >
      {{ preset.label }} {{ preset.delta > 0 ? '+' : '' }}{{ preset.delta }}
    </button>
  </div>
</template>
