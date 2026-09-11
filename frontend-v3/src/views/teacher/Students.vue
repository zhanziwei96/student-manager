<script setup lang="ts">
import { computed } from 'vue'
import { StudentFilters, usePaginatedStudents } from '@/features/students'
import { DataContainer, Card, Badge, Button } from '@/components/ui'
import { Users, GraduationCap, UserRound, ChevronLeft, ChevronRight } from 'lucide-vue-next'

/**
 * 教师学生名册页
 *
 * 只读视图：按班级筛选/搜索查看所授班级学生。
 * 成绩录入已迁移至「我的教学班 → 成绩录入」（教学班维度）。
 */

// === 数据获取（服务端分页） ===
const {
  page,
  searchQuery,
  classId,
  isSearching,
  classOptions,
  filteredStudents,
  total: totalStudents,
  totalPages,
  isPending,
  error,
  refetch,
  setSearchQuery,
  setClassFilter,
} = usePaginatedStudents()

// 统计信息（总数来自服务端 total；已签到基于当前展示列表）
const stats = computed(() => {
  const total = isSearching.value ? filteredStudents.value.length : totalStudents.value
  const checkedIn = filteredStudents.value.filter(s => s.checkin_status === 'checked_in').length

  return [
    { title: '学生总数', value: total, icon: Users },
    { title: '已签到', value: checkedIn, icon: GraduationCap },
  ]
})

// 学籍状态展示（与后端 Student.status 一致）
const STATUS_LABEL: Record<string, string> = {
  active: '在读',
  suspended: '休学',
  withdrawn: '退学',
  graduated: '毕业',
}
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-5">
      <div>
        <h1 class="text-2xl font-medium text-black">
          我的学生
        </h1>
        <p class="text-[#737373]">
          查看所授班级学生名册（成绩录入请前往我的教学班）
        </p>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-2 gap-3 sm:gap-4 mb-5">
      <Card
        v-for="stat in stats"
        :key="stat.title"
        class="group relative overflow-hidden p-3 sm:p-4 bg-white border-[#e5e5e5]"
      >
        <div class="relative z-10">
          <div class="flex items-center justify-between">
            <div class="flex h-8 w-8 sm:h-10 sm:w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <component
                :is="stat.icon"
                class="h-4 w-4 sm:h-5 sm:w-5"
              />
            </div>
            <p class="text-xl sm:text-2xl font-medium text-black">
              {{ stat.value }}
            </p>
          </div>
          <p class="mt-2 text-xs font-medium text-[#737373]">
            {{ stat.title }}
          </p>
        </div>
      </Card>
    </div>

    <!-- Filters -->
    <StudentFilters
      class="mb-5"
      v-model:search-query="searchQuery"
      v-model:selected-class="classId"
      :class-options="classOptions"
      @update:search-query="setSearchQuery"
      @update:selected-class="setClassFilter"
    />

    <!-- Data Container -->
    <DataContainer
      :loading="isPending"
      :error="error"
      :has-data="filteredStudents.length > 0"
      empty-text="未找到匹配的学生"
      @retry="refetch"
    >
      <!-- Students list -->
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        <Card
          v-for="student in filteredStudents"
          :key="student.student_id"
          class="bg-white border-[#e5e5e5] p-4"
        >
          <div class="flex items-start justify-between">
            <div class="flex items-center gap-3">
              <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <UserRound class="h-4 w-4" />
              </div>
              <div>
                <p class="text-sm font-medium text-black">
                  {{ student.name }}
                </p>
                <p class="font-mono text-xs text-[#a3a3a3]">
                  {{ student.student_id }}
                </p>
              </div>
            </div>
            <Badge :variant="student.checkin_status === 'checked_in' ? 'success' : 'secondary'">
              {{ student.checkin_status === 'checked_in' ? '已签到' : '未签到' }}
            </Badge>
          </div>
          <div class="mt-3 flex items-center justify-between text-xs text-[#737373]">
            <span>{{ student.class_name }}</span>
            <span>{{ STATUS_LABEL[student.status ?? 'active'] ?? student.status }}</span>
          </div>
        </Card>
      </div>

      <!-- 分页（搜索模式下显示匹配数量） -->
      <div
        v-if="isSearching"
        class="mt-4 text-center text-sm text-[#737373]"
      >
        找到 {{ filteredStudents.length }} 名匹配的学生
      </div>
      <div
        v-else-if="totalPages > 1"
        class="flex items-center justify-center gap-2 mt-4"
      >
        <Button
          variant="outline"
          size="sm"
          :disabled="page <= 1"
          @click="page--"
        >
          <ChevronLeft class="h-4 w-4" />
        </Button>
        <span class="text-sm text-[#737373]">
          {{ page }} / {{ totalPages }}（共 {{ totalStudents }} 人）
        </span>
        <Button
          variant="outline"
          size="sm"
          :disabled="page >= totalPages"
          @click="page++"
        >
          <ChevronRight class="h-4 w-4" />
        </Button>
      </div>
    </DataContainer>
  </div>
</template>
