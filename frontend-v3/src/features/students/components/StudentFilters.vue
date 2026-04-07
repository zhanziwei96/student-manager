<script setup lang="ts">
import { SearchableSelect, Input, Card } from '@/components/ui'
import { Search, GraduationCap } from 'lucide-vue-next'
import type { ClassOption } from '../types'

/**
 * 学生筛选组件
 *
 * 提供班级筛选和搜索功能 - 视觉优化版本
 */

interface Props {
  searchQuery: string
  selectedClass: string
  classOptions: ClassOption[]
}

defineProps<Props>()

const emit = defineEmits<{
  'update:searchQuery': [value: string]
  'update:selectedClass': [value: string]
}>()

const handleSearchUpdate = (value: string | number) => {
  emit('update:searchQuery', String(value))
}

const handleClassUpdate = (value: string | number) => {
  emit('update:selectedClass', String(value))
}
</script>

<template>
  <Card class="relative border-white/10 bg-white/[0.03] p-4 shadow-lg">
    <!-- 背景装饰 -->
    <div class="absolute -right-8 -top-8 h-24 w-24 rounded-full bg-primary/5 blur-2xl" />

    <div class="relative z-10 flex flex-col gap-4 sm:flex-row sm:items-center">
      <!-- Class Filter -->
      <div class="w-full sm:w-64">
        <label class="mb-1.5 flex items-center gap-1.5 text-xs font-medium text-white/60">
          <GraduationCap class="h-3.5 w-3.5" />
          班级筛选
        </label>
        <SearchableSelect
          :model-value="selectedClass"
          :options="classOptions"
          placeholder="选择班级..."
          search-placeholder="搜索班级..."
          @update:model-value="handleClassUpdate"
        />
      </div>

      <!-- Search -->
      <div class="relative flex-1">
        <label class="mb-1.5 flex items-center gap-1.5 text-xs font-medium text-white/60">
          <Search class="h-3.5 w-3.5" />
          搜索学生
        </label>
        <div class="relative">
          <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/40" />
          <Input
            :model-value="searchQuery"
            placeholder="输入姓名或学号搜索..."
            class="pl-10 bg-white/[0.05] border-white/10 focus:border-primary/50 focus:ring-primary/20"
            @update:model-value="handleSearchUpdate"
          />
        </div>
      </div>
    </div>
  </Card>
</template>
