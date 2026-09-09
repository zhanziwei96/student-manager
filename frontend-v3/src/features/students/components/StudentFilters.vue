<script setup lang="ts">
import { SearchableSelect, Select, Input, Card } from '@/components/ui'
import { Search, GraduationCap, Layers } from 'lucide-vue-next'
import type { ClassOption } from '../types'

/**
 * 学生筛选组件
 *
 * 提供班级筛选和搜索功能 - 视觉优化版本
 * 传入 cohortOptions 时显示届筛选（届 → 班级联动，admin 使用）
 */

interface Props {
  searchQuery: string
  selectedClass: string
  classOptions: ClassOption[]
  selectedCohort?: string
  cohortOptions?: ClassOption[]
}

defineProps<Props>()

const emit = defineEmits<{
  'update:searchQuery': [value: string]
  'update:selectedClass': [value: string]
  'update:selectedCohort': [value: string]
}>()

const handleSearchUpdate = (value: string | number) => {
  emit('update:searchQuery', String(value))
}

const handleClassUpdate = (value: string | number) => {
  emit('update:selectedClass', String(value))
}

const handleCohortUpdate = (value: string | number) => {
  emit('update:selectedCohort', String(value))
}
</script>

<template>
  <Card class="relative border-[#e5e5e5] bg-white p-4">
    <div class="relative z-10 flex flex-col gap-4 sm:flex-row sm:items-center">
      <!-- Cohort Filter（可选，届 → 班级联动） -->
      <div
        v-if="cohortOptions"
        class="w-full sm:w-44"
      >
        <label class="mb-1.5 flex items-center gap-1.5 text-xs font-medium text-[#737373]">
          <Layers class="h-3.5 w-3.5" />
          届筛选
        </label>
        <Select
          :model-value="selectedCohort"
          :options="cohortOptions"
          placeholder="全部届"
          @update:model-value="handleCohortUpdate"
        />
      </div>

      <!-- Class Filter -->
      <div class="w-full sm:w-64">
        <label class="mb-1.5 flex items-center gap-1.5 text-xs font-medium text-[#737373]">
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
        <label class="mb-1.5 flex items-center gap-1.5 text-xs font-medium text-[#737373]">
          <Search class="h-3.5 w-3.5" />
          搜索学生
        </label>
        <div class="relative">
          <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#a3a3a3]" />
          <Input
            :model-value="searchQuery"
            placeholder="输入姓名或学号搜索..."
            class="pl-10 bg-[#fafafa] border-[#e5e5e5] focus:border-black focus:ring-[#3b82f6]/50"
            @update:model-value="handleSearchUpdate"
          />
        </div>
      </div>
    </div>
  </Card>
</template>
