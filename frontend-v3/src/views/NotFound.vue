<script setup lang="ts">
import { useRouter } from 'vue-router'
import { Button, Card } from '@/components/ui'
import { ArrowLeft, Search } from 'lucide-vue-next'

const router = useRouter()
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-background p-4">
    <Card class="w-full max-w-md border-white/10 p-8 text-center">
      <div class="flex justify-center">
        <div class="flex h-20 w-20 items-center justify-center rounded-full bg-white/5">
          <Search class="h-10 w-10 text-white/40" />
        </div>
      </div>
      
      <h1 class="mt-6 text-4xl font-bold text-white">
        404
      </h1>
      <p class="mt-2 text-lg text-white/60">
        页面未找到
      </p>
      <p class="mt-2 text-sm text-white/40">
        您访问的页面不存在或已被移除。
      </p>
      
      <Button
        class="mt-6"
        variant="outline"
        @click="router.push('/')"
      >
        <ArrowLeft class="mr-2 h-4 w-4" />
        返回首页
      </Button>
    </Card>
  </div>
</template>
