<script setup lang="ts">
import { ref, computed } from 'vue'
import { Card, Button, Badge, Dialog, Input } from '@/components/ui'
import { Search, Loader2, Eye, GraduationCap } from 'lucide-vue-next'
import { useClassStats, useClassStudents } from '@/composables/useClasses'

// Data
const { data: classes, isPending } = useClassStats()

// Search
const searchQuery = ref('')
const filteredClasses = computed(() => {
  if (!classes.value) return []
  if (!searchQuery.value.trim()) return classes.value
  const query = searchQuery.value.toLowerCase()
  return classes.value.filter(c => c.name.toLowerCase().includes(query))
})

// View Class Students Dialog
const showViewDialog = ref(false)
const viewingClass = ref<string>('')
const { data: classStudents, isPending: isLoadingStudents } = useClassStudents(computed(() => viewingClass.value))

const openViewDialog = (className: string) => {
  viewingClass.value = className
  showViewDialog.value = true
}

// Score color helper
const getScoreColor = (score: number) => {
  if (score >= 90) return 'text-green-400'
  if (score >= 70) return 'text-yellow-400'
  return 'text-red-400'
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold text-white">
          班级管理
        </h1>
        <p class="text-white/60">
          管理班级信息和查看班级学生
        </p>
      </div>
    </div>

    <!-- Search -->
    <div class="relative">
      <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/50" />
      <Input
        v-model="searchQuery"
        placeholder="搜索班级..."
        class="pl-10"
      />
    </div>

    <!-- Loading state -->
    <div
      v-if="isPending"
      class="flex h-64 items-center justify-center"
    >
      <Loader2 class="h-8 w-8 animate-spin text-primary" />
    </div>

    <!-- Classes grid -->
    <div
      v-else-if="filteredClasses.length > 0"
      class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3"
    >
      <Card
        v-for="cls in filteredClasses"
        :key="cls.name"
        class="border-white/10 bg-white/[0.02] p-6"
      >
        <div class="flex items-start justify-between">
          <div class="flex items-center gap-3">
            <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/20">
              <GraduationCap class="h-5 w-5 text-primary" />
            </div>
            <div>
              <h3 class="font-medium text-white">
                {{ cls.name }}
              </h3>
              <p class="text-xs text-white/50">
                {{ cls.student_count }} 名学生
              </p>
            </div>
          </div>
          <Badge :variant="cls.status === 'active' ? 'success' : 'secondary'">
            {{ cls.status === 'active' ? '活跃' : '非活跃' }}
          </Badge>
        </div>
        
        <div class="mt-4 grid grid-cols-2 gap-4">
          <div class="rounded-lg bg-white/5 p-3">
            <p class="text-xs text-white/50">
              平均分
            </p>
            <p
              class="text-lg font-semibold"
              :class="getScoreColor(cls.average_score)"
            >
              {{ cls.average_score }}
            </p>
          </div>
          <div class="rounded-lg bg-white/5 p-3">
            <p class="text-xs text-white/50">
              学生数
            </p>
            <p class="text-lg font-semibold text-white">
              {{ cls.student_count }}
            </p>
          </div>
        </div>
        
        <div class="mt-4 flex gap-2">
          <Button
            variant="outline"
            size="sm"
            class="flex-1"
            @click="openViewDialog(cls.name)"
          >
            <Eye class="mr-2 h-4 w-4" />
            查看学生
          </Button>
        </div>
      </Card>
    </div>

    <!-- Empty state -->
    <div
      v-else
      class="flex h-64 flex-col items-center justify-center text-white/60"
    >
      <GraduationCap class="mb-4 h-12 w-12 opacity-50" />
      <p>暂无班级数据</p>
      <p class="mt-1 text-sm text-white/40">
        请先在学生管理中添加学生并分配班级
      </p>
    </div>

    <!-- View Students Dialog -->
    <Dialog
      v-model:open="showViewDialog"
      :title="`${viewingClass} - 学生列表`"
      description="查看班级学生详细信息"
    >
      <div
        v-if="isLoadingStudents"
        class="flex h-32 items-center justify-center"
      >
        <Loader2 class="h-6 w-6 animate-spin text-primary" />
      </div>
      
      <div
        v-else-if="classStudents && classStudents.length > 0"
        class="max-h-[60vh] overflow-y-auto"
      >
        <table class="w-full text-sm">
          <thead class="bg-white/5 text-white/70">
            <tr>
              <th class="px-4 py-2 text-left">
                学号
              </th>
              <th class="px-4 py-2 text-left">
                姓名
              </th>
              <th class="px-4 py-2 text-right">
                分数
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-white/5">
            <tr
              v-for="student in classStudents"
              :key="student.id"
              class="text-white/80"
            >
              <td class="px-4 py-3 font-mono text-xs">
                {{ student.student_id }}
              </td>
              <td class="px-4 py-3">
                {{ student.name }}
              </td>
              <td class="px-4 py-3 text-right">
                <span :class="getScoreColor(student.score)">{{ student.score }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <div
        v-else
        class="flex h-32 flex-col items-center justify-center text-white/50"
      >
        <p>该班级暂无学生</p>
      </div>
      
      <template #footer>
        <Button
          variant="outline"
          @click="showViewDialog = false"
        >
          关闭
        </Button>
      </template>
    </Dialog>
  </div>
</template>
