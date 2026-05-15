<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useStudentLostFoundItems } from '@/composables/useLostFound'
import { Card, Button, Badge, DataContainer, Select } from '@/components/ui'
import { Search, MapPin, User, ChevronLeft, ChevronRight } from 'lucide-vue-next'
import type { LostFoundStatus } from '@/types/lostFound'

const router = useRouter()

// 搜索和筛选
const keyword = ref('')
const statusFilter = ref<LostFoundStatus | ''>('')
const currentPage = ref(1)
const pageSize = 12

const statusOptions = [
  { value: '', label: '全部状态' },
  { value: 'open', label: '待认领' },
  { value: 'claiming', label: '认领中' },
  { value: 'closed', label: '已关闭' },
]

const queryParams = computed(() => ({
  keyword: keyword.value || undefined,
  status: statusFilter.value || undefined,
  page: currentPage.value,
  page_size: pageSize,
}))

const { data, isPending, error, refetch } = useStudentLostFoundItems(() => queryParams.value)

const items = computed(() => data.value?.items ?? [])
const total = computed(() => data.value?.total ?? 0)
const totalPages = computed(() => Math.ceil(total.value / pageSize))

function handleSearch() {
  currentPage.value = 1
}

function handleStatusChange(val: string | number) {
  statusFilter.value = String(val) as LostFoundStatus | ''
  currentPage.value = 1
}

function goToPage(page: number) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
}

function goToDetail(id: number) {
  router.push({ name: 'StudentLostFoundDetail', params: { id } })
}

function truncate(text: string, max: number) {
  if (!text) return ''
  return text.length > max ? text.slice(0, max) + '...' : text
}

const statusLabel: Record<string, string> = {
  open: '待认领',
  claiming: '认领中',
  closed: '已关闭',
}

const statusVariant: Record<string, string> = {
  open: 'bg-green-500/15 text-green-600 border-green-500/30',
  claiming: 'bg-yellow-500/15 text-yellow-600 border-yellow-500/30',
  closed: 'bg-gray-200 text-gray-500 border-gray-300',
}
</script>

<template>
  <div class="space-y-5">
    <div>
      <h1 class="text-2xl font-medium text-black">
        失物招领
      </h1>
      <p class="text-[#737373] mt-1">
        浏览失物招领信息
      </p>
    </div>

    <!-- 搜索和筛选 -->
    <Card class="bg-white border-[#e5e5e5] p-4">
      <div class="flex flex-col sm:flex-row gap-3">
        <div class="relative flex-1">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#a3a3a3]" />
          <input
            v-model="keyword"
            type="text"
            placeholder="搜索标题或描述..."
            class="w-full rounded-full border border-[#e5e5e5] bg-white pl-10 pr-4 py-2 text-sm text-black placeholder:text-[#a3a3a3] focus:outline-none focus:ring-2 focus:ring-[#3b82f6]/50"
            @keyup.enter="handleSearch"
          >
        </div>
        <div class="flex gap-2">
          <Select
            :model-value="statusFilter"
            :options="statusOptions"
            class="w-full sm:w-36"
            @update:model-value="handleStatusChange"
          />
          <Button @click="handleSearch">
            搜索
          </Button>
        </div>
      </div>
    </Card>

    <!-- 列表 -->
    <DataContainer
      :loading="isPending"
      :error="error"
      :has-data="items.length > 0"
      empty-text="暂无失物招领信息"
      @retry="refetch"
    >
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div
          v-for="item in items"
          :key="item.id"
          class="rounded-xl border border-[#e5e5e5] bg-white p-4 cursor-pointer transition-colors hover:bg-[#fafafa]"
          @click="goToDetail(item.id)"
        >
          <div class="flex items-start justify-between gap-2 mb-2">
            <h3 class="font-medium text-black text-sm truncate flex-1">
              {{ item.title }}
            </h3>
            <Badge
              :class="statusVariant[item.status]"
              class="flex-shrink-0"
            >
              {{ statusLabel[item.status] }}
            </Badge>
          </div>
          <p class="text-sm text-[#737373] mb-3 line-clamp-2">
            {{ truncate(item.description, 80) }}
          </p>
          <div class="flex items-center gap-3 text-xs text-[#a3a3a3]">
            <span v-if="item.location" class="flex items-center gap-1">
              <MapPin class="h-3 w-3" />
              {{ item.location }}
            </span>
            <span v-if="item.publisher_name" class="flex items-center gap-1">
              <User class="h-3 w-3" />
              {{ item.publisher_name }}
            </span>
          </div>
        </div>
      </div>
    </DataContainer>

    <!-- 分页 -->
    <div
      v-if="totalPages > 1"
      class="flex items-center justify-center gap-2"
    >
      <Button
        variant="outline"
        size="sm"
        :disabled="currentPage <= 1"
        @click="goToPage(currentPage - 1)"
      >
        <ChevronLeft class="h-4 w-4" />
      </Button>
      <span class="text-sm text-[#737373]">
        {{ currentPage }} / {{ totalPages }}
      </span>
      <Button
        variant="outline"
        size="sm"
        :disabled="currentPage >= totalPages"
        @click="goToPage(currentPage + 1)"
      >
        <ChevronRight class="h-4 w-4" />
      </Button>
    </div>
  </div>
</template>
