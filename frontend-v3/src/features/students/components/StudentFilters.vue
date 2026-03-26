<script setup lang="ts">
import { SearchableSelect, Input } from '@/components/ui'
import { Search } from 'lucide-vue-next'
import type { ClassOption } from '../types'

/**
 * 学生筛选组件
 * 
 * 提供班级筛选和搜索功能
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
  <div class="flex flex-col gap-4 sm:flex-row sm:items-center">
    <!-- Class Filter -->
    <div class="w-full sm:w-64">
      <SearchableSelect
        :model-value="selectedClass"
        :options="classOptions"
        placeholder="选择班级筛选..."
        search-placeholder="搜索班级..."
        @update:model-value="handleClassUpdate"
      />
    </div>

    <!-- Search -->
    <div class="relative flex-1">
      <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/50" />
      <Input
        :model-value="searchQuery"
        placeholder="搜索学生..."
        class="pl-10"
        @update:model-value="handleSearchUpdate"
      />
    </div>
  </div>
</template>
