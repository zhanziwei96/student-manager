<script setup lang="ts">
import { Scan, Camera, X, AlertCircle } from 'lucide-vue-next'
import Button from '@/components/ui/Button.vue'
import { useQRScanner } from '@/composables/useQRScanner'

const emit = defineEmits<{
  (e: 'success', decodedText: string): void
}>()

const { isScanning, error, startScan, stopScan, SCANNER_ELEMENT_ID } = useQRScanner((decodedText) => {
  emit('success', decodedText)
})
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
      <Button variant="cta" class="w-full max-w-xs" @click="startScan">
        <Camera class="h-4 w-4" />
        打开相机
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
      <Button variant="cta" class="w-full max-w-xs" @click="startScan">
        <Camera class="h-4 w-4" />
        重试
      </Button>
    </template>
  </div>
</template>
