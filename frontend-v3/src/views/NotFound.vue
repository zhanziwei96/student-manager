<script setup lang="ts">
import { useRouter } from 'vue-router'
import { Button, Card } from '@/components/ui'
import { ArrowLeft, AlertTriangle } from 'lucide-vue-next'

const router = useRouter()
</script>

<template>
  <div class="relative flex min-h-screen items-center justify-center bg-white p-4 overflow-hidden">
    <!-- 装饰性数字 -->
    <div class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-[200px] sm:text-[300px] font-medium text-[#f5f5f5] select-none pointer-events-none">
      404
    </div>

    <Card class="relative w-full max-w-md border-[#e5e5e5] p-8 text-center">
      <!-- 404 插图区域 -->
      <div class="flex justify-center">
        <div class="relative flex h-20 w-20 items-center justify-center rounded-full bg-[#fafafa] border border-[#e5e5e5]">
          <AlertTriangle class="h-10 w-10 text-black" />
        </div>
      </div>

      <!-- 404 标题 -->
      <h1 class="mt-6 text-5xl font-medium text-black">
        404
      </h1>

      <p class="mt-2 text-lg text-black">
        页面未找到
      </p>
      <p class="mt-2 text-sm text-[#737373]">
        您访问的页面不存在或已被移除。
      </p>

      <!-- 返回按钮 -->
      <Button
        variant="cta"
        class="mt-6"
        @click="router.push('/')"
      >
        <ArrowLeft class="mr-2 h-4 w-4" />
        返回首页
      </Button>
    </Card>
  </div>
</template>
