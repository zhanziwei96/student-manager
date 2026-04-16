<script setup lang="ts">
/**
 * 教师端二维码显示组件
 *
 * 展示课程签到二维码，支持自动刷新倒计时、加载和错误状态
 */
import { computed } from 'vue'
import QRCode from 'qrcode.vue'
import { Loader2, RefreshCw } from 'lucide-vue-next'
import { Card, Button } from '@/components/ui'
import { useQRCode } from '@/composables/useQRCode'

const props = defineProps<{
  sessionId: number
}>()

const { qrContent, expiresIn, progressPercent, isLoading, error, refetch } = useQRCode(props.sessionId)

const isRefreshingSoon = computed(() => expiresIn.value <= 2)
</script>

<template>
  <Card class="relative flex flex-col items-center gap-4 bg-[#030307] border-[#1f1f28] p-6 md:p-8">
    <!-- 标题 -->
    <div class="text-center">
      <h3 class="text-lg font-medium text-white">
        扫码签到
      </h3>
      <p class="text-sm text-[#a1a1aa] mt-1">
        学生使用微信扫码完成签到
      </p>
    </div>

    <!-- 二维码容器 -->
    <div class="relative">
      <!-- 加载状态 -->
      <div
        v-if="isLoading"
        class="flex h-[200px] w-[200px] items-center justify-center rounded-xl bg-white shadow-lg"
      >
        <Loader2 class="h-8 w-8 animate-spin text-[#6366f1]" />
      </div>

      <!-- 二维码 -->
      <div
        v-else-if="qrContent"
        class="relative h-[200px] w-[200px] rounded-xl bg-white p-3 shadow-lg"
      >
        <QRCode
          :value="qrContent"
          :size="174"
          level="M"
          class="rounded-lg"
        />

        <!-- 即将刷新遮罩 -->
        <div
          v-if="isRefreshingSoon"
          class="absolute inset-0 flex items-center justify-center rounded-xl bg-black/60 backdrop-blur-sm"
        >
          <span class="text-sm font-medium text-white">即将刷新</span>
        </div>
      </div>

      <!-- 错误状态 -->
      <div
        v-else-if="error"
        class="flex h-[200px] w-[200px] flex-col items-center justify-center gap-3 rounded-xl bg-white shadow-lg"
      >
        <p class="text-sm text-[#737373]">
          加载失败
        </p>
        <Button
          variant="outline"
          size="sm"
          class="rounded-full"
          @click="refetch"
        >
          <RefreshCw class="h-4 w-4 mr-1" />
          重试
        </Button>
      </div>
    </div>

    <!-- 倒计时进度条 -->
    <div class="w-[200px]">
      <div class="flex items-center justify-between text-xs text-[#a1a1aa] mb-1.5">
        <span>自动刷新</span>
        <span>{{ expiresIn }}s</span>
      </div>
      <div class="h-1.5 w-full rounded-full bg-[#1f1f28] overflow-hidden">
        <div
          class="h-full rounded-full transition-all duration-1000 ease-linear"
          :class="isRefreshingSoon ? 'bg-[#f59e0b]' : 'bg-[#6366f1]'"
          :style="{ width: `${progressPercent}%` }"
        />
      </div>
    </div>
  </Card>
</template>
