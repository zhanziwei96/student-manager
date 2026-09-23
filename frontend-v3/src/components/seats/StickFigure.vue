<script setup lang="ts">
import { computed } from 'vue'

type Pose = 'stand' | 'walk' | 'carry' | 'sit' | 'scratch' | 'cheer'

interface Seg { x1: number; y1: number; x2: number; y2: number }
interface Pt { cx: number; cy: number }

interface PoseCoords {
  head: Pt & { r: number }
  eyeL: Pt
  eyeR: Pt
  smile: string
  headTransform?: string
  body: Seg
  armL: Seg
  armR: Seg
  thighL: Seg
  calfL: Seg
  thighR: Seg
  calfR: Seg
}

/**
 * 六姿势坐标集（viewBox 0 0 40 64，面向右）。
 * 腿分大腿/小腿两段，站姿两段共线，坐姿才有"弯腿"。
 */
const POSES: Record<Pose, PoseCoords> = {
  stand: {
    head: { cx: 20, cy: 10, r: 7 },
    eyeL: { cx: 17.5, cy: 9 },
    eyeR: { cx: 22.5, cy: 9 },
    smile: 'M 17 12 Q 20 14.5 23 12',
    body: { x1: 20, y1: 17, x2: 20, y2: 38 },
    armL: { x1: 20, y1: 22, x2: 13, y2: 32 },
    armR: { x1: 20, y1: 22, x2: 27, y2: 32 },
    thighL: { x1: 20, y1: 38, x2: 17, y2: 47 },
    calfL: { x1: 17, y1: 47, x2: 14, y2: 56 },
    thighR: { x1: 20, y1: 38, x2: 23, y2: 47 },
    calfR: { x1: 23, y1: 47, x2: 26, y2: 56 },
  },
  walk: {
    // 迈步：左腿前跨、右腿后蹬，双臂反向摆动，头微前倾
    head: { cx: 21, cy: 10, r: 7 },
    eyeL: { cx: 18.5, cy: 9 },
    eyeR: { cx: 23.5, cy: 9 },
    smile: 'M 18 12 Q 21 14.5 24 12',
    body: { x1: 21, y1: 17, x2: 20, y2: 38 },
    armL: { x1: 20.5, y1: 22, x2: 13, y2: 29 },
    armR: { x1: 20.5, y1: 22, x2: 28, y2: 29 },
    thighL: { x1: 20, y1: 38, x2: 25, y2: 46 },
    calfL: { x1: 25, y1: 46, x2: 29, y2: 55 },
    thighR: { x1: 20, y1: 38, x2: 15, y2: 46 },
    calfR: { x1: 15, y1: 46, x2: 10, y2: 55 },
  },
  carry: {
    // 搬椅子：双臂前伸平举，步伐略错开
    head: { cx: 20, cy: 10, r: 7 },
    eyeL: { cx: 17.5, cy: 9 },
    eyeR: { cx: 22.5, cy: 9 },
    smile: 'M 17 12 Q 20 14.5 23 12',
    body: { x1: 20, y1: 17, x2: 20, y2: 38 },
    armL: { x1: 20, y1: 22, x2: 33, y2: 21 },
    armR: { x1: 20, y1: 25, x2: 33, y2: 25 },
    thighL: { x1: 20, y1: 38, x2: 24, y2: 46 },
    calfL: { x1: 24, y1: 46, x2: 27, y2: 55 },
    thighR: { x1: 20, y1: 38, x2: 16, y2: 46 },
    calfR: { x1: 16, y1: 46, x2: 13, y2: 55 },
  },
  sit: {
    // 坐姿：髋部下沉，大腿前伸水平、小腿垂直向下（腿弯），双臂前搭桌面
    head: { cx: 20, cy: 9, r: 7 },
    eyeL: { cx: 17.5, cy: 8 },
    eyeR: { cx: 22.5, cy: 8 },
    smile: 'M 17 11 Q 20 13.5 23 11',
    body: { x1: 20, y1: 16, x2: 20, y2: 33 },
    armL: { x1: 20, y1: 21, x2: 29, y2: 26 },
    armR: { x1: 20, y1: 23, x2: 30, y2: 29 },
    thighL: { x1: 20, y1: 33, x2: 29, y2: 34 },
    calfL: { x1: 29, y1: 34, x2: 29, y2: 46 },
    thighR: { x1: 20, y1: 33, x2: 28, y2: 36 },
    calfR: { x1: 28, y1: 36, x2: 28, y2: 47 },
  },
  scratch: {
    // 挠头：右手举到头顶，头向手侧微倾
    head: { cx: 20, cy: 10, r: 7 },
    eyeL: { cx: 17.5, cy: 9 },
    eyeR: { cx: 22.5, cy: 9 },
    smile: 'M 17.5 12.5 Q 20 14 22.5 12.5',
    headTransform: 'rotate(8 20 10)',
    body: { x1: 20, y1: 17, x2: 20, y2: 38 },
    armL: { x1: 20, y1: 22, x2: 13, y2: 32 },
    armR: { x1: 20, y1: 22, x2: 27, y2: 5 },
    thighL: { x1: 20, y1: 38, x2: 17, y2: 47 },
    calfL: { x1: 17, y1: 47, x2: 14, y2: 56 },
    thighR: { x1: 20, y1: 38, x2: 23, y2: 47 },
    calfR: { x1: 23, y1: 47, x2: 26, y2: 56 },
  },
  cheer: {
    // 欢呼：双臂上举成 V 字，双腿分立，笑容加大
    head: { cx: 20, cy: 10, r: 7 },
    eyeL: { cx: 17.5, cy: 9 },
    eyeR: { cx: 22.5, cy: 9 },
    smile: 'M 16.5 12 Q 20 15.5 23.5 12',
    body: { x1: 20, y1: 17, x2: 20, y2: 38 },
    armL: { x1: 20, y1: 22, x2: 9, y2: 7 },
    armR: { x1: 20, y1: 22, x2: 31, y2: 7 },
    thighL: { x1: 20, y1: 38, x2: 16, y2: 47 },
    calfL: { x1: 16, y1: 47, x2: 12, y2: 56 },
    thighR: { x1: 20, y1: 38, x2: 24, y2: 47 },
    calfR: { x1: 24, y1: 47, x2: 28, y2: 56 },
  },
}

const props = defineProps<{ pose: Pose }>()
const p = computed(() => POSES[props.pose])
</script>

<template>
  <svg
    class="stick-figure"
    viewBox="0 0 40 64"
    :data-pose="pose"
    aria-hidden="true"
    stroke="currentColor"
    stroke-width="2.5"
    stroke-linecap="round"
    fill="none"
  >
    <g class="stick-head-group" :transform="p.headTransform">
      <circle class="stick-head" :cx="p.head.cx" :cy="p.head.cy" :r="p.head.r" />
      <circle class="stick-eye" :cx="p.eyeL.cx" :cy="p.eyeL.cy" r="0.9" />
      <circle class="stick-eye" :cx="p.eyeR.cx" :cy="p.eyeR.cy" r="0.9" />
      <path class="stick-smile" :d="p.smile" />
    </g>
    <line class="stick-body" v-bind="p.body" />
    <line class="stick-arm" v-bind="p.armL" />
    <line class="stick-arm" v-bind="p.armR" />
    <line class="stick-leg" v-bind="p.thighL" />
    <line class="stick-leg" v-bind="p.calfL" />
    <line class="stick-leg" v-bind="p.thighR" />
    <line class="stick-leg" v-bind="p.calfR" />
  </svg>
</template>

<style scoped>
.stick-figure {
  display: block;
  overflow: visible;
}

/* 眼睛用实心点，其余描边 */
.stick-eye {
  fill: currentColor;
  stroke: none;
}

/* 姿势切换平滑过渡（几何属性 + 头部倾斜 transform） */
.stick-figure line,
.stick-figure circle,
.stick-figure path,
.stick-head-group {
  transition: all 0.3s ease;
}

@media (prefers-reduced-motion: reduce) {
  .stick-figure line,
  .stick-figure circle,
  .stick-figure path,
  .stick-head-group {
    transition: none;
  }
}
</style>
