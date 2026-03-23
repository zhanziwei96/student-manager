<script setup lang="ts">
import { ref } from 'vue'
import { Card, Button, Badge } from '@/components/ui'
import { Plus, Search, Mail, Loader2 } from 'lucide-vue-next'
import type { User } from '@/types'

// Mock teachers data - replace with actual API call
const teachers = ref<User[]>([
  { id: 1, username: 'teacher1', name: 'John Smith', role: 'teacher' },
  { id: 2, username: 'teacher2', name: 'Jane Doe', role: 'teacher' },
])
const isPending = ref(false)
const searchQuery = ref('')
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold text-white">Teachers</h1>
        <p class="text-white/60">Manage teacher accounts</p>
      </div>
      <Button>
        <Plus class="mr-2 h-4 w-4" />
        Add Teacher
      </Button>
    </div>

    <!-- Search -->
    <div class="relative">
      <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/50" />
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Search teachers..."
        class="w-full rounded-lg border border-white/20 bg-transparent py-2 pl-10 pr-4 text-sm text-white placeholder:text-white/50 focus:border-primary focus:outline-none"
      />
    </div>

    <!-- Loading state -->
    <div v-if="isPending" class="flex h-64 items-center justify-center">
      <Loader2 class="h-8 w-8 animate-spin text-primary" />
    </div>

    <!-- Teachers grid -->
    <div v-else class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
      <Card
        v-for="teacher in teachers"
        :key="teacher.id"
        class="border-white/10 bg-white/[0.02] p-6"
      >
        <div class="flex items-start gap-4">
          <div class="flex h-12 w-12 items-center justify-center rounded-full bg-primary/20">
            <span class="text-lg font-medium text-primary">
              {{ teacher.name.charAt(0).toUpperCase() }}
            </span>
          </div>
          <div class="flex-1 min-w-0">
            <h3 class="truncate font-medium text-white">{{ teacher.name }}</h3>
            <p class="text-sm text-white/60">@{{ teacher.username }}</p>
            <div class="mt-2 flex items-center gap-2">
              <Badge variant="secondary">{{ teacher.role }}</Badge>
            </div>
          </div>
        </div>
        <div class="mt-4 flex gap-2">
          <Button variant="outline" size="sm" class="flex-1">
            <Mail class="mr-2 h-4 w-4" />
            Contact
          </Button>
          <Button variant="outline" size="sm" class="flex-1">Edit</Button>
        </div>
      </Card>
    </div>
  </div>
</template>
