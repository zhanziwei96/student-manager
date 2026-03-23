<script setup lang="ts">
import { ref } from 'vue'
import { Card, Button, Badge } from '@/components/ui'
import { Plus, Users, Calendar, Loader2 } from 'lucide-vue-next'

interface ClassInfo {
  id: number
  name: string
  teacher: string
  students: number
  schedule: string
  status: 'active' | 'inactive'
}

// Mock classes data - replace with actual API call
const classes = ref<ClassInfo[]>([
  { id: 1, name: 'Computer Science 101', teacher: 'John Smith', students: 35, schedule: 'Mon/Wed 10:00', status: 'active' },
  { id: 2, name: 'Data Structures', teacher: 'Jane Doe', students: 28, schedule: 'Tue/Thu 14:00', status: 'active' },
  { id: 3, name: 'Algorithms', teacher: 'Bob Johnson', students: 22, schedule: 'Mon/Fri 09:00', status: 'inactive' },
])
const isPending = ref(false)
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold text-white">Classes</h1>
        <p class="text-white/60">Manage class schedules and assignments</p>
      </div>
      <Button>
        <Plus class="mr-2 h-4 w-4" />
        Add Class
      </Button>
    </div>

    <!-- Loading state -->
    <div v-if="isPending" class="flex h-64 items-center justify-center">
      <Loader2 class="h-8 w-8 animate-spin text-primary" />
    </div>

    <!-- Classes grid -->
    <div v-else class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
      <Card
        v-for="cls in classes"
        :key="cls.id"
        class="border-white/10 bg-white/[0.02] p-6"
      >
        <div class="flex items-start justify-between">
          <div>
            <h3 class="font-medium text-white">{{ cls.name }}</h3>
            <p class="text-sm text-white/60">Teacher: {{ cls.teacher }}</p>
          </div>
          <Badge :variant="cls.status === 'active' ? 'success' : 'secondary'">
            {{ cls.status }}
          </Badge>
        </div>
        
        <div class="mt-4 space-y-2">
          <div class="flex items-center gap-2 text-sm text-white/60">
            <Users class="h-4 w-4" />
            {{ cls.students }} students
          </div>
          <div class="flex items-center gap-2 text-sm text-white/60">
            <Calendar class="h-4 w-4" />
            {{ cls.schedule }}
          </div>
        </div>
        
        <div class="mt-4 flex gap-2">
          <Button variant="outline" size="sm" class="flex-1">View</Button>
          <Button variant="outline" size="sm" class="flex-1">Edit</Button>
        </div>
      </Card>
    </div>
  </div>
</template>
