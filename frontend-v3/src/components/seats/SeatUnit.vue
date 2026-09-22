<script setup lang="ts">
import type { SeatCell } from '@/types/seats'

const props = defineProps<{ seat: SeatCell; selectable: boolean }>()
const emit = defineEmits<{ (e: 'click'): void }>()

function onClick() {
  if (!props.selectable || props.seat.is_broken) return
  emit('click')
}
</script>

<template>
  <button
    type="button"
    class="seat-unit"
    :data-state="seat.state"
    :data-broken="seat.is_broken || undefined"
    :aria-disabled="!selectable || seat.is_broken || undefined"
    :aria-label="`${seat.seat_no}${seat.student_name ? ' ' + seat.student_name : ''}${seat.is_broken ? ' 电脑故障' : ''}`"
    @click="onClick"
  >
    <span class="seat-desk" aria-hidden="true" />
    <span class="seat-chair" aria-hidden="true" />
    <span class="seat-label">{{ seat.student_name ?? seat.seat_no }}</span>
    <span v-if="seat.is_broken" class="seat-broken-mark" aria-hidden="true">✕</span>
  </button>
</template>

<style scoped>
/*
 * 布局（俯视+侧视混合，讲台在上方，门在右）：
 *   desk  —— 纵向桌面（长边垂直于讲台方向）
 *   chair —— 桌面右侧的侧视椅子（面向桌子朝左，椅背朝右=朝门）
 *   label —— 编号/姓名
 * 四态颜色走 --seat-* 自定义属性，此处给浅色兜底；
 * 深色主题由 SeatMap 的 .seat-map-dark 作用域覆盖同组变量。
 */
.seat-unit {
  --seat-desk-bg: #ffffff;
  --seat-desk-border: #cbd5e1;
  --seat-chair-bg: #cbd5e1;
  --seat-label-color: #334155;
  --seat-occupied-desk-bg: #dbeafe;
  --seat-occupied-desk-border: #60a5fa;
  --seat-occupied-chair-bg: #60a5fa;
  --seat-assigned-desk-bg: #fef3c7;
  --seat-assigned-desk-border: #fbbf24;
  --seat-assigned-chair-bg: #fbbf24;
  --seat-mine-desk-bg: #dcfce7;
  --seat-mine-desk-border: #22c55e;
  --seat-mine-chair-bg: #22c55e;
  --seat-mine-glow: rgba(34, 197, 94, 0.45);
  --seat-broken-mark-color: #ef4444;
  --seat-hover-border: #3b82f6;

  position: relative;
  display: grid;
  grid-template-columns: auto auto;
  grid-template-rows: auto auto;
  grid-template-areas:
    'desk chair'
    'label label';
  column-gap: 3px;
  row-gap: 2px;
  align-items: center;
  justify-items: center;
  padding: 4px;
  border: none;
  border-radius: 6px;
  background: transparent;
  font: inherit;
  cursor: pointer;
  transition: opacity 0.15s ease;
}

.seat-desk {
  grid-area: desk;
  width: 28px;
  height: 42px;
  border: 2px solid var(--seat-desk-border);
  border-radius: 4px;
  background: var(--seat-desk-bg);
  transition: background 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

/* 侧视椅子：座面（横）+ 椅背（竖，靠门一侧=右侧） */
.seat-chair {
  grid-area: chair;
  position: relative;
  width: 12px;
  height: 24px;
}

.seat-chair::before {
  content: '';
  position: absolute;
  left: 0;
  bottom: 4px;
  width: 10px;
  height: 4px;
  border-radius: 2px;
  background: var(--seat-chair-bg);
  transition: background 0.2s ease;
}

.seat-chair::after {
  content: '';
  position: absolute;
  right: 0;
  top: 2px;
  width: 4px;
  height: 20px;
  border-radius: 2px;
  background: var(--seat-chair-bg);
  transition: background 0.2s ease;
}

.seat-label {
  grid-area: label;
  max-width: 56px;
  overflow: hidden;
  font-size: 11px;
  line-height: 1.3;
  color: var(--seat-label-color);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.seat-broken-mark {
  position: absolute;
  top: 0;
  right: 0;
  font-size: 13px;
  font-weight: 700;
  line-height: 1;
  color: var(--seat-broken-mark-color);
}

/* 四态 */
.seat-unit[data-state='occupied'] .seat-desk {
  border-color: var(--seat-occupied-desk-border);
  background: var(--seat-occupied-desk-bg);
}
.seat-unit[data-state='occupied'] .seat-chair::before,
.seat-unit[data-state='occupied'] .seat-chair::after {
  background: var(--seat-occupied-chair-bg);
}

.seat-unit[data-state='assigned'] .seat-desk {
  border-color: var(--seat-assigned-desk-border);
  background: var(--seat-assigned-desk-bg);
}
.seat-unit[data-state='assigned'] .seat-chair::before,
.seat-unit[data-state='assigned'] .seat-chair::after {
  background: var(--seat-assigned-chair-bg);
}

.seat-unit[data-state='mine'] .seat-desk {
  border-color: var(--seat-mine-desk-border);
  background: var(--seat-mine-desk-bg);
  box-shadow: 0 0 8px var(--seat-mine-glow);
}
.seat-unit[data-state='mine'] .seat-chair::before,
.seat-unit[data-state='mine'] .seat-chair::after {
  background: var(--seat-mine-chair-bg);
}

/* 故障：不可选，整体降饱和 */
.seat-unit[data-broken] .seat-desk,
.seat-unit[data-broken] .seat-chair::before,
.seat-unit[data-broken] .seat-chair::after {
  opacity: 0.55;
}

/* 交互态 */
.seat-unit[aria-disabled] {
  cursor: not-allowed;
}

.seat-unit:not([aria-disabled]):hover .seat-desk {
  border-color: var(--seat-hover-border);
}

.seat-unit:focus-visible {
  outline: 2px solid var(--seat-hover-border);
  outline-offset: 2px;
}
</style>
