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
    title: 'Student Management',
    description: 'Comprehensive student profiles, scores, and status tracking.',
  },
  {
    icon: BarChart3,
    title: 'Real-time Analytics',
    description: 'Live dashboard with key metrics and insights.',
  },
  {
    icon: CheckCircle,
    title: 'Class Sessions',
    description: 'Interactive check-in system for active learning.',
  },
]
</script>

<template>
  <div class="min-h-screen bg-background">
    <!-- Navigation -->
    <nav class="fixed left-0 right-0 top-0 z-50 border-b border-white/10 bg-background/80 backdrop-blur-md">
      <div class="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        <div class="flex items-center gap-2">
          <GraduationCap class="h-8 w-8 text-primary" />
          <span class="text-xl font-bold text-white">ClassHub</span>
        </div>
        <div class="flex items-center gap-4">
          <Button variant="ghost" class="text-white/70" @click="router.push('/login')">
            Sign In
          </Button>
          <Button @click="router.push('/login')">
            Get Started
            <ArrowRight class="ml-2 h-4 w-4" />
          </Button>
        </div>
      </div>
    </nav>

    <!-- Hero Section -->
    <section class="relative overflow-hidden px-6 pt-32">
      <!-- Background effects -->
      <div class="absolute inset-0 overflow-hidden">
        <div class="absolute -left-1/4 top-0 h-[600px] w-[600px] rounded-full bg-primary/10 blur-[120px]" />
        <div class="absolute -right-1/4 bottom-0 h-[600px] w-[600px] rounded-full bg-accent-cyan/10 blur-[120px]" />
      </div>

      <div class="relative mx-auto max-w-5xl text-center">
        <div class="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-sm text-white/80">
          <Sparkles class="h-4 w-4 text-primary" />
          Smart Student Management System
        </div>
        
        <h1 class="mt-6 text-4xl font-bold leading-tight text-white sm:text-6xl">
          Manage your classroom
          <span class="block text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent-cyan">
            with intelligence
          </span>
        </h1>
        
        <p class="mx-auto mt-6 max-w-2xl text-lg text-white/60">
          A modern platform for teachers and administrators to track student progress,
          manage class sessions, and gain real-time insights.
        </p>

        <div class="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Button size="lg" @click="router.push('/login')">
            Get Started
            <ArrowRight class="ml-2 h-5 w-5" />
          </Button>
          <Button size="lg" variant="outline">
            View Demo
          </Button>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section class="relative px-6 py-24">
      <div class="mx-auto max-w-6xl">
        <div class="grid gap-8 md:grid-cols-3">
          <div
            v-for="feature in features"
            :key="feature.title"
            class="group rounded-2xl border border-white/10 bg-white/[0.02] p-6 transition-colors hover:border-white/20 hover:bg-white/[0.04]"
          >
            <div class="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary transition-colors group-hover:bg-primary group-hover:text-white">
              <component :is="feature.icon" class="h-6 w-6" />
            </div>
            <h3 class="mt-4 text-lg font-semibold text-white">{{ feature.title }}</h3>
            <p class="mt-2 text-sm text-white/60">{{ feature.description }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="border-t border-white/10 px-6 py-8">
      <div class="mx-auto max-w-6xl text-center text-sm text-white/40">
        <p>&copy; 2024 ClassHub. All rights reserved.</p>
      </div>
    </footer>
  </div>
</template>
