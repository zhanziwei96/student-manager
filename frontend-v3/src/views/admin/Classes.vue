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

// Score color helper - 使用CSS变量主题色
const getScoreColor = (score: number) => {
  if (score >= 90) return 'text-[var(--color-green-400)]'
  if (score >= 70) return 'text-[var(--color-amber-400)]'
  return 'text-[var(--color-error)]'
}

</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-5">
      <div>
        <h1 class="text-2xl font-medium text-black">
          班级管理
        </h1>
        <p class="text-[#737373]">
          管理班级信息和查看班级学生
        </p>
      </div>
    </div>

    <!-- Search -->
    <div class="relative mb-5">
      <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#a3a3a3]" />
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
        v-for="(cls) in filteredClasses"
        :key="cls.name"
        class="relative overflow-hidden p-6"
        :class="'bg-white border-[#e5e5e5]'"
      >
        <!-- 背景光晕效果 -->

        <div class="relative z-10 flex items-start justify-between">
          <div class="flex items-center gap-3">
            <div
              class="flex h-10 w-10 items-center justify-center rounded-xl"
              :class="'bg-primary/10 text-primary'"
            >
              <GraduationCap
                class="h-5 w-5"
                :style="{ color: 'var(--card-indigo-icon-text)' }"
              />
            </div>
            <div>
              <h3 class="font-medium text-black">
                {{ cls.name }}
              </h3>
              <p class="text-xs text-[var(--color-text-tertiary)]">
                {{ cls.student_count }} 名学生
              </p>
            </div>
          </div>
          <Badge :variant="cls.status === 'active' ? 'success' : 'secondary'">
            {{ cls.status === 'active' ? '活跃' : '非活跃' }}
          </Badge>
        </div>

        <div class="relative z-10 mt-4 grid grid-cols-2 gap-4">
          <div class="rounded-xl bg-[var(--color-background-card)] p-3 border border-[var(--color-divider)]">
            <p class="text-xs text-[var(--color-text-tertiary)]">
              平均分
            </p>
            <p
              class="text-lg font-medium"
              :class="getScoreColor(cls.average_score)"
            >
              {{ cls.average_score }}
            </p>
          </div>
          <div class="rounded-xl bg-[var(--color-background-card)] p-3 border border-[var(--color-divider)]">
            <p class="text-xs text-[var(--color-text-tertiary)]">
              学生数
            </p>
            <p class="text-lg font-medium text-black">
              {{ cls.student_count }}
            </p>
          </div>
        </div>

        <div class="relative z-10 mt-4 flex gap-2">
          <Button
            variant="outline"
            size="sm"
            class="flex-1 hover:bg-[#fafafa]"
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
      class="flex h-64 flex-col items-center justify-center text-[#737373]"
    >
      <GraduationCap class="mb-4 h-12 w-12 opacity-50" />
      <p>暂无班级数据</p>
      <p class="mt-1 text-sm text-[#a3a3a3]">
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
        <!-- 移动端：卡片列表 -->
        <div class="lg:hidden space-y-2">
          <div
            v-for="student in classStudents"
            :key="student.id"
            class="flex items-center justify-between rounded-xl border border-[var(--color-divider)] bg-[var(--color-background-card)] p-3"
          >
            <div class="flex items-center gap-3">
              <div
                class="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--card-indigo-icon-bg)]"
              >
                <span
                  class="text-sm font-medium text-[var(--card-indigo-icon-text)]"
                >
                  {{ student.name.charAt(0) }}
                </span>
              </div>
              <div>
                <p class="font-medium text-black">{{ student.name }}</p>
                <p class="font-mono text-xs text-[var(--color-text-tertiary)]">{{ student.student_id }}</p>
              </div>
            </div>
            <span
              class="text-lg font-medium"
              :class="getScoreColor(student.score)"
            >
              {{ student.score }}
            </span>
          </div>
        </div>

        <!-- 桌面端：表格 -->
        <table class="hidden lg:table w-full text-sm">
          <thead class="bg-[var(--color-background-card)] text-[var(--color-text-secondary)] border-b border-[var(--color-divider)]">
            <tr>
              <th class="px-4 py-3 text-left font-medium">
                学号
              </th>
              <th class="px-4 py-3 text-left font-medium">
                姓名
              </th>
              <th class="px-4 py-3 text-right font-medium">
                分数
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[var(--color-divider)]">
            <tr
              v-for="student in classStudents"
              :key="student.id"
              class="text-[var(--color-text-secondary)] hover:bg-[var(--color-background-hover)] transition-colors"
            >
              <td class="px-4 py-3 font-mono text-xs">
                {{ student.student_id }}
              </td>
              <td class="px-4 py-3 font-medium text-black">
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
        class="flex h-32 flex-col items-center justify-center text-[#a3a3a3]"
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
