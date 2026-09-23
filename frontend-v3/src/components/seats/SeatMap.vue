<script setup lang="ts">
import { computed } from 'vue'
import SeatUnit from './SeatUnit.vue'
import type { ClassroomInfo, SeatCell } from '@/types/seats'

const props = defineProps<{
  classroom: ClassroomInfo
  seats: SeatCell[]
  mode: 'student' | 'teacher'
  selectedSeatId?: number | null
}>()
const emit = defineEmits<{ (e: 'seat-click', seat: SeatCell): void }>()

/** 网格列：座位列 + 每 2 列一条走廊（走廊是空列） */
const gridStyle = computed(() => {
  const tracks: string[] = []
  for (let c = 1; c <= props.classroom.cols; c++) {
    tracks.push('1fr')
    if (c % 2 === 0 && c < props.classroom.cols) tracks.push('0.35fr') // 走廊
  }
  return { gridTemplateColumns: tracks.join(' ') }
})

function gridPos(seat: SeatCell) {
  // 走廊占列：col 3 的网格列 = 3 + floor((3-1)/2) = 4
  // 网格第 1 行留作讲台前的过道，座位行从第 2 行起
  return { gridRow: seat.row + 1, gridColumn: seat.col + Math.floor((seat.col - 1) / 2) }
}

function selectable(seat: SeatCell) {
  // 教师模式全可点：故障位也要能点（弹层里执行「取消故障」）
  if (props.mode === 'teacher') return true
  if (seat.is_broken) return false
  return seat.state === 'empty' || seat.state === 'mine'
}
</script>

<template>
  <div class="seat-map-dark">
    <div class="seat-podium">
      讲台
    </div>
    <div
      class="seat-grid"
      :style="gridStyle"
    >
      <SeatUnit
        v-for="seat in seats"
        :key="seat.seat_id"
        :seat="seat"
        :selectable="selectable(seat)"
        :allow-broken-click="mode === 'teacher'"
        :style="gridPos(seat)"
        :class="{ 'seat-selected': seat.seat_id === selectedSeatId }"
        @click="emit('seat-click', seat)"
      />
    </div>
    <div
      class="seat-door seat-door-1"
      aria-hidden="true"
    >
      门1
    </div>
    <div
      class="seat-door seat-door-2"
      aria-hidden="true"
    >
      门2
    </div>
  </div>
</template>

<style scoped>
/* 深色科技风只活在这个作用域，不动全局令牌 */
.seat-map-dark {
  --seat-bg: #0b1220;
  --seat-empty: #1e293b;
  --seat-assigned: #334155;
  --seat-occupied: #f59e0b;
  --seat-mine: #22d3ee;
  --seat-broken: #ef4444;
  background: var(--seat-bg);
  position: relative;
  border-radius: 12px;
  padding: 16px 56px 16px 16px; /* 右侧留门的位置 */
}

/* 讲台：顶部横条 */
.seat-podium {
  margin-bottom: 14px;
  padding: 8px 0;
  border: 1px solid #334155;
  border-radius: 8px;
  background: linear-gradient(180deg, #16202f 0%, #101827 100%);
  color: #94a3b8;
  font-size: 13px;
  letter-spacing: 0.5em;
  text-align: center;
}

.seat-grid {
  display: grid;
  gap: 10px;
}

/*
 * SeatUnit 的 --seat-* 变量声明在元素自身（.seat-unit）上，
 * 必须用更高优先级的深作用域选择器才能压过它。
 */
.seat-map-dark :deep(.seat-unit) {
  --seat-desk-bg: var(--seat-empty);
  --seat-desk-border: var(--seat-assigned);
  --seat-chair-bg: var(--seat-assigned);
  --seat-label-color: #cbd5e1;
  --seat-occupied-desk-bg: rgba(245, 158, 11, 0.16);
  --seat-occupied-desk-border: var(--seat-occupied);
  --seat-occupied-chair-bg: var(--seat-occupied);
  --seat-assigned-desk-bg: var(--seat-assigned);
  --seat-assigned-desk-border: #475569;
  --seat-assigned-chair-bg: #475569;
  --seat-mine-desk-bg: rgba(34, 211, 238, 0.14);
  --seat-mine-desk-border: var(--seat-mine);
  --seat-mine-chair-bg: var(--seat-mine);
  --seat-mine-glow: rgba(34, 211, 238, 0.55);
  --seat-broken-mark-color: var(--seat-broken);
  --seat-hover-border: var(--seat-mine);
}

/* 四态发光（mine 的发光由 SeatUnit 内部走 --seat-mine-glow，此处补 occupied） */
.seat-map-dark :deep(.seat-unit[data-state='occupied']) .seat-desk {
  box-shadow: 0 0 12px rgba(245, 158, 11, 0.45);
}

/* 选中位：青色描边 */
.seat-map-dark :deep(.seat-unit.seat-selected) {
  box-shadow: 0 0 0 2px var(--seat-mine);
  border-radius: 8px;
}

/* 右墙门标记 */
.seat-door {
  position: absolute;
  right: 12px;
  width: 32px;
  padding: 6px 0;
  border: 1px solid #475569;
  border-radius: 6px;
  background: #16202f;
  color: #94a3b8;
  font-size: 12px;
  line-height: 1.2;
  text-align: center;
  box-shadow: 0 0 8px rgba(34, 211, 238, 0.15);
}
.seat-door-1 {
  top: 18%;
}
.seat-door-2 {
  bottom: 18%;
}

@media (prefers-reduced-motion: reduce) {
  .seat-map-dark :deep(.seat-unit),
  .seat-map-dark :deep(.seat-unit) * {
    transition: none;
  }
}
</style>
