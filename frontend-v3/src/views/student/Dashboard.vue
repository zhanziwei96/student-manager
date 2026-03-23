<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores'
import { useStudents } from '@/composables'
import { Card, Badge } from '@/components/ui'
import { Star, TrendingUp, Users, Award, Loader2 } from 'lucide-vue-next'

const authStore = useAuthStore()
const { data: students, isPending } = useStudents()

const currentStudent = computed(() => {
  if (!students.value) return null
  return students.value.find(s => s.name === authStore.user?.name) || null
})

const rank = computed(() => {
  if (!students.value || !currentStudent.value) return '-'
  const sorted = [...students.value].sort((a, b) => b.score - a.score)
  const index = sorted.findIndex(s => s.id === currentStudent.value!.id)
  return index >= 0 ? `#${index + 1}` : '-'
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-white">Student Dashboard</h1>
      <p class="text-white/60">Welcome back, {{ authStore.user?.name }}</p>
    </div>

    <!-- Loading state -->
    <div v-if="isPending" class="flex h-64 items-center justify-center">
      <Loader2 class="h-8 w-8 animate-spin text-primary" />
    </div>

    <template v-else-if="currentStudent">
      <!-- Score card -->
      <Card class="relative overflow-hidden border-white/10 bg-gradient-to-br from-primary/20 to-accent-cyan/20 p-8">
        <div class="relative z-10">
          <div class="flex items-center gap-3">
            <Star class="h-8 w-8 text-yellow-400" />
            <div>
              <p class="text-sm text-white/80">Your Score</p>
              <p class="text-5xl font-bold text-white">{{ currentStudent.score }}</p>
            </div>
          </div>
          <div class="mt-4 flex items-center gap-2">
            <Badge variant="secondary" class="bg-white/20">
              <TrendingUp class="mr-1 h-3 w-3" />
              +10 this week
            </Badge>
            <Badge variant="secondary" class="bg-white/20">
              Rank {{ rank }}
            </Badge>
          </div>
        </div>
        <!-- Background decoration -->
        <div class="absolute -right-10 -top-10 h-40 w-40 rounded-full bg-white/5 blur-2xl" />
        <div class="absolute -bottom-10 -left-10 h-40 w-40 rounded-full bg-white/5 blur-2xl" />
      </Card>

      <!-- Stats grid -->
      <div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <Card class="border-white/10 bg-white/[0.02] p-6">
          <div class="flex items-center gap-3">
            <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-500/20">
              <Users class="h-5 w-5 text-blue-400" />
            </div>
            <div>
              <p class="text-sm text-white/60">Class</p>
              <p class="font-medium text-white">{{ currentStudent.class_name }}</p>
            </div>
          </div>
        </Card>
        <Card class="border-white/10 bg-white/[0.02] p-6">
          <div class="flex items-center gap-3">
            <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-500/20">
              <Award class="h-5 w-5 text-purple-400" />
            </div>
            <div>
              <p class="text-sm text-white/60">Student ID</p>
              <p class="font-medium text-white">{{ currentStudent.student_id }}</p>
            </div>
          </div>
        </Card>
        <Card class="border-white/10 bg-white/[0.02] p-6">
          <div class="flex items-center gap-3">
            <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-green-500/20">
              <TrendingUp class="h-5 w-5 text-green-400" />
            </div>
            <div>
              <p class="text-sm text-white/60">Status</p>
              <Badge :variant="currentStudent.status === 'active' ? 'success' : 'secondary'">
                {{ currentStudent.status }}
              </Badge>
            </div>
          </div>
        </Card>
      </div>

      <!-- Recent activity -->
      <Card class="border-white/10 bg-white/[0.02] p-6">
        <h2 class="text-lg font-semibold text-white">Recent Activity</h2>
        <p class="text-sm text-white/60">Your latest score changes</p>
        <div class="mt-6 space-y-4">
          <div class="flex items-center justify-between rounded-lg border border-white/5 bg-white/[0.02] p-4">
            <div class="flex items-center gap-3">
              <div class="flex h-8 w-8 items-center justify-center rounded-full bg-green-500/20">
                <TrendingUp class="h-4 w-4 text-green-400" />
              </div>
              <div>
                <p class="text-sm text-white">Class participation</p>
                <p class="text-xs text-white/40">2 days ago</p>
              </div>
            </div>
            <Badge variant="success">+10</Badge>
          </div>
          <div class="flex items-center justify-between rounded-lg border border-white/5 bg-white/[0.02] p-4">
            <div class="flex items-center gap-3">
              <div class="flex h-8 w-8 items-center justify-center rounded-full bg-green-500/20">
                <TrendingUp class="h-4 w-4 text-green-400" />
              </div>
              <div>
                <p class="text-sm text-white">Assignment completed</p>
                <p class="text-xs text-white/40">1 week ago</p>
              </div>
            </div>
            <Badge variant="success">+15</Badge>
          </div>
        </div>
      </Card>
    </template>
  </div>
</template>
