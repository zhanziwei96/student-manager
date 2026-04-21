<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  placeholder?: string
  submitLabel?: string
  showAnonymous?: boolean
}

withDefaults(defineProps<Props>(), {
  placeholder: '请输入你的回答...',
  submitLabel: '提交',
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
  <div class="bg-white rounded-lg border border-gray-200 p-4">
    <textarea
      v-model="content"
      :placeholder="placeholder"
      rows="3"
      class="w-full px-3 py-2 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
    />

    <div class="flex justify-between items-center mt-3">
      <label v-if="showAnonymous" class="flex items-center gap-2 cursor-pointer">
        <input
          v-model="isAnonymous"
          type="checkbox"
          class="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        />
        <span class="text-sm text-gray-600">匿名回答</span>
      </label>
      <div v-else />

      <button
        class="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        :disabled="!content.trim()"
        @click="handleSubmit"
      >
        {{ submitLabel }}
      </button>
    </div>
  </div>
</template>
