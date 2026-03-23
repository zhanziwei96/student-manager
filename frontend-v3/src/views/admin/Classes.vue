<script setup lang="ts">
import { ref } from 'vue'
import { Card, Button, Badge } from '@/components/ui'
import { Plus, Users, Calendar, Loader2 } from 'lucide-vue-next'
import type { ClassInfo } from '@/types'

// TODO: 替换为真实的班级管理 API
const classes = ref<ClassInfo[]>([
  { id: 1, name: '计算机科学 101', teacher: '张老师', students: 35, schedule: '周一/周三 10:00', status: 'active' },
  { id: 2, name: '数据结构', teacher: '李老师', students: 28, schedule: '周二/周四 14:00', status: 'active' },
  { id: 3, name: '算法设计', teacher: '王老师', students: 22, schedule: '周一/周五 09:00', status: 'inactive' },
])
const isPending = ref(false)
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold text-white">班级管理</h1>
        <p class="text-white/60">管理班级安排和分配</p>
      </div>
      <Button>
        <Plus class="mr-2 h-4 w-4" />
        添加班级
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
            <p class="text-sm text-white/60">教师: {{ cls.teacher }}</p>
          </div>
          <Badge :variant="cls.status === 'active' ? 'success' : 'secondary'">
            {{ cls.status === 'active' ? '活跃' : '非活跃' }}
          </Badge>
        </div>
        
        <div class="mt-4 space-y-2">
          <div class="flex items-center gap-2 text-sm text-white/60">
            <Users class="h-4 w-4" />
            {{ cls.students }} 名学生
          </div>
          <div class="flex items-center gap-2 text-sm text-white/60">
            <Calendar class="h-4 w-4" />
            {{ cls.schedule }}
          </div>
        </div>
        
        <div class="mt-4 flex gap-2">
          <Button variant="outline" size="sm" class="flex-1">查看</Button>
          <Button variant="outline" size="sm" class="flex-1">编辑</Button>
        </div>
      </Card>
    </div>
  </div>
</template>
