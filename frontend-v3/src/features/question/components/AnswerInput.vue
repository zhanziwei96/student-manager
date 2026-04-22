<script setup lang="ts">
import { ref } from 'vue'
import { Send } from 'lucide-vue-next'

interface Props {
  placeholder?: string
  submitLabel?: string
  showAnonymous?: boolean
}

withDefaults(defineProps<Props>(), {
  placeholder: '说说你的想法...',
  submitLabel: '发送',
  showAnonymous: false,
})

const emit = defineEmits<{
  submit: [content: string, isAnonymous: boolean]
}>()

const content = ref('')
const isAnonymous = ref(false)

function handleSubmit() {
  const trimmed = content.value.trim()
  if (!trimmed) return
  emit('submit', trimmed, isAnonymous.value)
  content.value = ''
  isAnonymous.value = false
}
</script>

<template>
  <div class="bg-white rounded-xl border border-[#e5e5e5] p-4">
    <textarea
      v-model="content"
      :placeholder="placeholder"
      rows="3"
      class="w-full px-3 py-2 border-0 resize-none focus:outline-none text-sm text-black placeholder:text-[#a3a3a3] bg-transparent"
    />

    <div class="flex justify-between items-center pt-2 border-t border-[#f5f5f5]">
      <label v-if="showAnonymous" class="flex items-center gap-2 cursor-pointer select-none">
        <input
          v-model="isAnonymous"
          type="checkbox"
          class="w-4 h-4 rounded border-[#d4d4d4] text-black focus:ring-black"
        />
        <span class="text-xs text-[#737373]">匿名发送</span>
      </label>
      <div v-else />

      <button
        :class="[
          'flex items-center gap-1.5 px-4 py-2 text-sm rounded-full font-medium transition-all',
          content.trim()
            ? 'bg-black text-white hover:bg-[#262626]'
            : 'bg-[#f5f5f5] text-[#a3a3a3] cursor-not-allowed',
        ]"
        :disabled="!content.trim()"
        @click="handleSubmit"
      >
        <Send class="h-3.5 w-3.5" />
        {{ submitLabel }}
      </button>
    </div>
  </div>
</template>
