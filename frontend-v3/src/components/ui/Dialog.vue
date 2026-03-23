<script setup lang="ts">
import { computed, watch } from 'vue'
import { cn } from '@/lib/utils'
import { X } from 'lucide-vue-next'

interface Props {
  open?: boolean
  class?: string
  title?: string
  description?: string
}

const props = withDefaults(defineProps<Props>(), {
  open: false,
})

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
}>()

// Lock body scroll when open
watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
  }
)

const overlayClasses = computed(() =>
  cn(
    'fixed inset-0 z-50 bg-black/80 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0',
    !props.open && 'hidden'
  )
)

const contentClasses = computed(() =>
  cn(
    'fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border border-white/10 bg-[#13131f] p-6 shadow-lg duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%] sm:rounded-lg',
    props.class,
    !props.open && 'hidden'
  )
)

const close = () => {
  emit('update:open', false)
}
</script>

<template>
  <Teleport to="body">
    <!-- Overlay -->
    <div :class="overlayClasses" @click="close" data-state="open">
      <!-- Content -->
      <div :class="contentClasses" @click.stop data-state="open">
        <!-- Header -->
        <div v-if="title || $slots.title" class="flex flex-col space-y-1.5 text-center sm:text-left">
          <h3 class="text-lg font-semibold leading-none tracking-tight text-white">
            <slot name="title">{{ title }}</slot>
          </h3>
          <p v-if="description || $slots.description" class="text-sm text-white/60">
            <slot name="description">{{ description }}</slot>
          </p>
        </div>

        <!-- Body -->
        <div class="text-white/80">
          <slot />
        </div>

        <!-- Footer -->
        <div v-if="$slots.footer" class="flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2">
          <slot name="footer" />
        </div>

        <!-- Close button -->
        <button
          class="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none"
          @click="close"
        >
          <X class="h-4 w-4 text-white" />
          <span class="sr-only">Close</span>
        </button>
      </div>
    </div>
  </Teleport>
</template>
