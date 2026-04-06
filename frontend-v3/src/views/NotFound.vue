<script setup lang="ts">
import { useRouter } from 'vue-router'
import { Button, Card } from '@/components/ui'
import { ArrowLeft, AlertTriangle } from 'lucide-vue-next'

const router = useRouter()
</script>

<template>
  <div class="relative flex min-h-screen items-center justify-center bg-background p-4 overflow-hidden">
    <!-- 背景装饰 -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <!-- 渐变光晕 -->
      <div class="absolute -left-1/4 top-1/4 h-[400px] w-[400px] rounded-full bg-gradient-to-br from-orange-500/15 via-red-500/10 to-purple-500/10 blur-[100px]" />
      <div class="absolute -right-1/4 bottom-1/4 h-[400px] w-[400px] rounded-full bg-gradient-to-tl from-primary/15 via-purple-500/10 to-blue-500/10 blur-[100px]" />

      <!-- 装饰性数字 -->
      <div class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-[200px] sm:text-[300px] font-bold text-white/[0.02] select-none pointer-events-none">
        404
      </div>
    </div>

    <Card class="relative w-full max-w-md border-[var(--card-orange-border)] bg-[var(--card-orange-bg)] p-8 text-center backdrop-blur-sm">
      <!-- 404 插图区域 -->
      <div class="flex justify-center">
        <div class="relative flex h-24 w-24 items-center justify-center">
          <!-- 外圈光晕 -->
          <div class="absolute inset-0 rounded-full bg-[var(--card-orange-icon-bg)] animate-pulse" />
          <!-- 图标容器 -->
          <div class="relative flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-orange-500/20 to-red-500/20 border border-[var(--card-orange-border)]">
            <AlertTriangle class="h-10 w-10 text-[var(--card-orange-icon-text)]" />
          </div>
        </div>
      </div>

      <!-- 404 标题 -->
      <h1 class="mt-6 text-5xl font-bold bg-gradient-to-r from-orange-400 via-amber-400 to-orange-500 bg-clip-text text-transparent">
        404
      </h1>

      <p class="mt-2 text-lg text-white/80">
        页面未找到
      </p>
      <p class="mt-2 text-sm text-white/50">
        您访问的页面不存在或已被移除。
      </p>

      <!-- 返回按钮 - 主题色 -->
      <Button
        class="mt-6 bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-400 hover:to-amber-400 text-white border-0 shadow-lg shadow-orange-500/25 hover:shadow-orange-500/40 transition-all duration-300 hover:scale-[1.02]"
        @click="router.push('/')"
      >
        <ArrowLeft class="mr-2 h-4 w-4" />
        返回首页
      </Button>
    </Card>
  </div>
</template>
