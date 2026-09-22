<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import StickFigure from './StickFigure.vue'

type AnimatorState = 'idle' | 'walking' | 'sitting' | 'success' | 'fail'
type Pose = 'stand' | 'walk' | 'carry' | 'sit' | 'scratch' | 'cheer'

interface Step {
  pose: Pose
  duration: number
}

/** success：搬椅 → 坐下 → 欢呼（约 1.6s）；fail：挠头 0.8s → 走路退回 */
const SEQUENCES: Partial<Record<AnimatorState, Step[]>> = {
  success: [
    { pose: 'carry', duration: 500 },
    { pose: 'sit', duration: 500 },
    { pose: 'cheer', duration: 600 },
  ],
  fail: [
    { pose: 'scratch', duration: 800 },
    { pose: 'walk', duration: 600 },
  ],
}

const props = defineProps<{ state: AnimatorState }>()
const emit = defineEmits<{ (e: 'finished'): void }>()

/** success/fail 序列当前播到第几步；walking/sitting 时恒为 null */
const stepIndex = ref<number | null>(null)
let timer: ReturnType<typeof setTimeout> | null = null

const reducedMotion = () =>
  typeof window.matchMedia === 'function' &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches

const currentPose = computed<Pose | null>(() => {
  if (props.state === 'idle') return null
  const seq = SEQUENCES[props.state]
  if (seq) return seq[stepIndex.value ?? 0].pose
  return props.state === 'walking' ? 'walk' : 'sit'
})

/** fail 序列的退回阶段（最后一个 walk 步）向左滑出 */
const exiting = computed(
  () => props.state === 'fail' && stepIndex.value === SEQUENCES.fail!.length - 1,
)

function clearTimer() {
  if (timer !== null) {
    clearTimeout(timer)
    timer = null
  }
}

function runSequence(seq: Step[], i: number) {
  stepIndex.value = i
  timer = setTimeout(() => {
    if (i + 1 < seq.length) {
      runSequence(seq, i + 1)
    } else {
      timer = null
      emit('finished')
    }
  }, seq[i].duration)
}

watch(
  () => props.state,
  (s) => {
    clearTimer()
    stepIndex.value = null
    const seq = SEQUENCES[s]
    if (!seq) return
    if (reducedMotion()) {
      emit('finished')
      return
    }
    runSequence(seq, 0)
  },
  { immediate: true },
)

onUnmounted(clearTimer)
</script>

<template>
  <div
    v-if="currentPose"
    class="seat-animator"
    aria-hidden="true"
  >
    <StickFigure
      :pose="currentPose"
      class="anim-figure"
      :class="{ 'anim-enter': state === 'walking', 'anim-exit': exiting }"
    />
  </div>
</template>

<style scoped>
.seat-animator {
  display: inline-block;
  color: #e2e8f0;
}

.anim-figure {
  width: 48px;
  height: auto;
}

/* 从左侧走入 */
.anim-enter {
  animation: seat-anim-walk-in 0.6s ease-out;
}

/* 向左退回并淡出 */
.anim-exit {
  animation: seat-anim-walk-out 0.6s ease-in forwards;
}

@keyframes seat-anim-walk-in {
  from {
    transform: translateX(-120%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes seat-anim-walk-out {
  from {
    transform: translateX(0);
    opacity: 1;
  }
  to {
    transform: translateX(-120%);
    opacity: 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .anim-enter,
  .anim-exit {
    animation: none;
  }
}
</style>
