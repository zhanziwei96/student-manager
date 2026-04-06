<script setup lang="ts">
import { useRouter } from 'vue-router'
import { Button } from '@/components/ui'
import {
  GraduationCap,
  Users,
  BarChart3,
  CheckCircle,
  ArrowRight,
  Sparkles,
} from 'lucide-vue-next'

const router = useRouter()

const features = [
  {
    icon: Users,
    title: '学生管理',
    description: '全面的学生档案、成绩和状态追踪。',
    theme: 'blue',
  },
  {
    icon: BarChart3,
    title: '实时分析',
    description: '实时仪表板，关键指标和洞察一目了然。',
    theme: 'purple',
  },
  {
    icon: CheckCircle,
    title: '课堂签到',
    description: '互动式签到系统，促进积极学习。',
    theme: 'green',
  },
]
</script>

<template>
  <div class="min-h-screen bg-background">
    <!-- Navigation -->
    <nav class="fixed left-0 right-0 top-0 z-50 border-b border-white/10 bg-background/80 backdrop-blur-md">
      <div class="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6">
        <div class="flex items-center gap-2">
          <GraduationCap class="h-7 w-7 sm:h-8 sm:w-8 text-primary flex-shrink-0" />
          <span class="text-lg sm:text-xl font-bold text-white whitespace-nowrap">智慧课堂</span>
        </div>
        <div class="flex items-center gap-2 sm:gap-4">
          <Button
            variant="ghost"
            size="sm"
            class="text-white/70 hidden sm:inline-flex"
            @click="router.push('/login')"
          >
            登录
          </Button>
          <Button
            size="sm"
            class="sm:size-default"
            @click="router.push('/login')"
          >
            <span class="hidden sm:inline">开始使用</span>
            <span class="sm:hidden">开始使用</span>
            <ArrowRight class="ml-1.5 sm:ml-2 h-4 w-4" />
          </Button>
        </div>
      </div>
    </nav>

    <!-- Hero Section -->
    <section class="relative overflow-hidden px-4 sm:px-6 pt-24 sm:pt-32 pb-12">
      <!-- Background effects - 渐变背景 -->
      <div class="absolute inset-0 overflow-hidden">
        <!-- 主渐变光晕 -->
        <div class="absolute -left-1/4 top-0 h-[300px] w-[300px] sm:h-[600px] sm:w-[600px] rounded-full bg-gradient-to-br from-primary/20 via-purple-500/15 to-blue-500/10 blur-[80px] sm:blur-[120px] animate-pulse" />
        <div class="absolute -right-1/4 bottom-0 h-[300px] w-[300px] sm:h-[600px] sm:w-[600px] rounded-full bg-gradient-to-tl from-accent-cyan/20 via-blue-500/15 to-purple-500/10 blur-[80px] sm:blur-[120px] animate-pulse" style="animation-delay: 1s;" />
        <!-- 额外装饰光晕 -->
        <div class="absolute left-1/2 top-1/3 -translate-x-1/2 h-[200px] w-[200px] sm:h-[400px] sm:w-[400px] rounded-full bg-gradient-to-r from-orange-500/10 to-pink-500/10 blur-[60px] sm:blur-[100px]" />
      </div>

      <div class="relative mx-auto max-w-5xl text-center">
        <div class="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 sm:px-4 py-1.5 text-xs sm:text-sm text-white/80">
          <Sparkles class="h-3.5 w-3.5 sm:h-4 sm:w-4 text-primary" />
          智能学生管理系统
        </div>

        <h1 class="mt-4 sm:mt-6 text-2xl sm:text-5xl md:text-6xl font-bold leading-tight text-white">
          智慧管理课堂
          <span class="block mt-1 sm:mt-2 text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent-cyan">
            提升教学效率
          </span>
        </h1>

        <p class="mx-auto mt-4 sm:mt-6 max-w-2xl text-base sm:text-lg text-white/60 px-2 sm:px-0">
          一个现代化的平台，帮助教师和管理员追踪学生进度、管理课堂签到，并获取实时洞察。
        </p>

        <div class="mt-8 sm:mt-10 flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4">
          <Button
            size="lg"
            class="w-full sm:w-auto min-h-[48px] bg-gradient-to-r from-primary to-primary-hover hover:from-primary-hover hover:to-primary shadow-lg shadow-primary/25 hover:shadow-primary/40 transition-all duration-300 hover:scale-[1.02]"
            @click="router.push('/login')"
          >
            开始使用
            <ArrowRight class="ml-2 h-5 w-5" />
          </Button>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section class="relative px-4 sm:px-6 py-16 sm:py-24">
      <div class="mx-auto max-w-6xl">
        <div class="grid gap-8 md:grid-cols-3">
          <div
            v-for="feature in features"
            :key="feature.title"
            :class="[
              'group rounded-2xl border p-6 transition-all duration-300 hover:scale-[1.02]',
              feature.theme === 'blue' && 'border-[var(--card-blue-border)] bg-[var(--card-blue-bg)] hover:shadow-[0_0_30px_var(--card-blue-glow)]',
              feature.theme === 'purple' && 'border-[var(--card-purple-border)] bg-[var(--card-purple-bg)] hover:shadow-[0_0_30px_var(--card-purple-glow)]',
              feature.theme === 'green' && 'border-[var(--card-green-border)] bg-[var(--card-green-bg)] hover:shadow-[0_0_30px_var(--card-green-glow)]',
            ]"
          >
            <div
              :class="[
                'flex h-12 w-12 items-center justify-center rounded-xl transition-all duration-300 group-hover:scale-110',
                feature.theme === 'blue' && 'bg-[var(--card-blue-icon-bg)] text-[var(--card-blue-icon-text)]',
                feature.theme === 'purple' && 'bg-[var(--card-purple-icon-bg)] text-[var(--card-purple-icon-text)]',
                feature.theme === 'green' && 'bg-[var(--card-green-icon-bg)] text-[var(--card-green-icon-text)]',
              ]"
            >
              <component
                :is="feature.icon"
                class="h-6 w-6"
              />
            </div>
            <h3 class="mt-4 text-lg font-semibold text-white">
              {{ feature.title }}
            </h3>
            <p class="mt-2 text-sm text-white/60">
              {{ feature.description }}
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="border-t border-white/10 px-6 py-8">
      <div class="mx-auto max-w-6xl text-center text-sm text-white/40">
        <p>&copy; 2026 智慧课堂. 保留所有权利。</p>
      </div>
    </footer>
  </div>
</template>
