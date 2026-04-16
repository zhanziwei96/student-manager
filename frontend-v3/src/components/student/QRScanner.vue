<script setup lang="ts">
import { ref } from 'vue'
import { Scan, Camera, X, AlertCircle, Image } from 'lucide-vue-next'
import Button from '@/components/ui/Button.vue'
import { useQRScanner } from '@/composables/useQRScanner'

const emit = defineEmits<{
  (e: 'success', decodedText: string): void
}>()

const fileInputRef = ref<HTMLInputElement | null>(null)

const { isScanning, error, isCameraSupported, startScan, stopScan, scanFile, SCANNER_ELEMENT_ID } = useQRScanner((decodedText) => {
  emit('success', decodedText)
})

const handleFileChange = async (e: Event) => {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    await scanFile(file)
    target.value = ''
  }
}

const triggerFileInput = () => {
  fileInputRef.value?.click()
}
</script>

<template>
  <div class="flex flex-col items-center justify-center gap-4 p-6">
    <!-- 未扫码状态 -->
    <template v-if="!isScanning && !error">
      <div class="flex flex-col items-center gap-3">
        <div class="flex h-16 w-16 items-center justify-center rounded-full bg-[#e0e7ff]">
          <Scan class="h-8 w-8 text-[#6366f1]" />
        </div>
        <h3 class="text-lg font-semibold text-[#171717]">扫码签到</h3>
        <p class="text-sm text-[#737373]">请允许浏览器使用相机权限</p>
      </div>
      <Button v-if="isCameraSupported" variant="cta" class="w-full max-w-xs" @click="startScan">
        <Camera class="h-4 w-4" />
        打开相机
      </Button>
      <Button v-else variant="cta" class="w-full max-w-xs" @click="triggerFileInput">
        <Image class="h-4 w-4" />
        拍照签到
      </Button>
    </template>

    <!-- 扫码中状态 -->
    <template v-if="isScanning">
      <div class="relative w-full max-w-sm overflow-hidden rounded-xl bg-black">
        <div :id="SCANNER_ELEMENT_ID" class="w-full" />
        <!-- 扫描框叠加层 -->
        <div class="pointer-events-none absolute inset-0 flex items-center justify-center">
          <div class="relative h-[250px] w-[250px]">
            <!-- 左上角 -->
            <div class="absolute left-0 top-0 h-6 w-6 rounded-tl-lg border-l-4 border-t-4 border-[#6366f1]" />
            <!-- 右上角 -->
            <div class="absolute right-0 top-0 h-6 w-6 rounded-tr-lg border-r-4 border-t-4 border-[#6366f1]" />
            <!-- 左下角 -->
            <div class="absolute bottom-0 left-0 h-6 w-6 rounded-bl-lg border-b-4 border-l-4 border-[#6366f1]" />
            <!-- 右下角 -->
            <div class="absolute bottom-0 right-0 h-6 w-6 rounded-br-lg border-b-4 border-r-4 border-[#6366f1]" />
          </div>
        </div>
      </div>
      <p class="text-sm text-[#737373]">将二维码对准框内</p>
      <Button variant="outline" class="w-full max-w-xs" @click="stopScan">
        <X class="h-4 w-4" />
        取消
      </Button>
    </template>

    <!-- 错误状态 -->
    <template v-if="error">
      <div class="flex flex-col items-center gap-3">
        <div class="flex h-16 w-16 items-center justify-center rounded-full bg-[#fee2e2]">
          <AlertCircle class="h-8 w-8 text-[#ef4444]" />
        </div>
        <p class="text-sm text-[#737373]">{{ error }}</p>
      </div>
      <Button v-if="isCameraSupported" variant="cta" class="w-full max-w-xs" @click="startScan">
        <Camera class="h-4 w-4" />
        重试
      </Button>
      <Button v-else variant="cta" class="w-full max-w-xs" @click="triggerFileInput">
        <Image class="h-4 w-4" />
        重新拍照
      </Button>
    </template>

    <!-- 隐藏的拍照 input -->
    <input
      ref="fileInputRef"
      type="file"
      accept="image/*"
      capture="environment"
      class="hidden"
      @change="handleFileChange"
    />
    <!-- 用于 scanFile 的临时占位元素 -->
    <div id="qr-file-reader-dummy" class="hidden" />
  </div>
</template>
