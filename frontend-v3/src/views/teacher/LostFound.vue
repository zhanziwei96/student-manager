<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Card, Button, Badge, Select, DataContainer, Input } from '@/components/ui'
import { useTeacherLostFoundItems } from '@/composables/useLostFound'
import { Plus, MapPin, Search, ChevronLeft, ChevronRight } from 'lucide-vue-next'
import type { LostFoundStatus } from '@/types/lostFound'

const router = useRouter()

// 搜索与筛选
const keyword = ref('')
const statusFilter = ref('')
const page = ref(1)
const pageSize = 12

const statusOptions = [
  { value: '', label: '全部' },
  { value: 'open', label: '发布中' },
  { value: 'claiming', label: '认领中' },
  { value: 'closed', label: '已关闭' },
]

// 构建查询参数
const queryParams = computed(() => ({
  keyword: keyword.value || undefined,
  status: (statusFilter.value as LostFoundStatus) || undefined,
  page: page.value,
  page_size: pageSize,
}))

const { data, isPending } = useTeacherLostFoundItems(() => queryParams.value)

const items = computed(() => data.value?.items || [])
const total = computed(() => data.value?.total || 0)
const totalPages = computed(() => Math.ceil(total.value / pageSize))

// 搜索时重置页码
watch([keyword, statusFilter], () => {
  page.value = 1
})

function getStatusBadge(status: LostFoundStatus) {
  const map: Record<LostFoundStatus, { label: string; variant: 'success' | 'warning' | 'default' }> = {
    open: { label: '发布中', variant: 'success' },
    claiming: { label: '认领中', variant: 'warning' },
    closed: { label: '已关闭', variant: 'default' },
  }
  return map[status]
}

function truncate(text: string, max: number) {
  return text.length > max ? text.slice(0, max) + '...' : text
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('zh-CN')
}

function goToDetail(id: number) {
  router.push({ name: 'TeacherLostFoundDetail', params: { id } })
}

function goToCreate() {
  router.push({ name: 'TeacherLostFoundCreate' })
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
      <div>
        <h1 class="text-2xl font-medium text-black">
          失物招领
        </h1>
        <p class="text-[#737373] mt-1">
          管理和发布失物招领信息
        </p>
      </div>
      <Button variant="cta" @click="goToCreate">
        <Plus class="h-4 w-4" />
        发布新物品
      </Button>
    </div>

    <Card class="bg-white border-[#e5e5e5] p-5">
      <div class="flex flex-col sm:flex-row gap-3 mb-4">
        <div class="relative flex-1">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#a3a3a3]" />
          <Input
            v-model="keyword"
            placeholder="搜索物品标题或描述..."
            class="pl-9"
          />
        </div>
        <Select v-model="statusFilter" :options="statusOptions" class="w-full sm:w-36" />
      </div>

      <DataContainer
        :loading="isPending"
        :has-data="items.length > 0"
        empty-text="暂无失物招领信息"
      >
        <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div
            v-for="item in items"
            :key="item.id"
            class="rounded-xl border border-[#e5e5e5] bg-white overflow-hidden cursor-pointer transition-colors hover:bg-[#fafafa]"
            @click="goToDetail(item.id)"
          >
            <!-- 图片 -->
            <img
              v-if="item.image_url"
              :src="item.image_url"
              :alt="item.title"
              class="w-full max-h-48 object-contain bg-[#f5f5f5]"
            >
            <div class="p-4">
              <div class="flex items-start justify-between gap-2 mb-2">
                <h3 class="font-medium text-black truncate flex-1">
                  {{ item.title }}
                </h3>
                <Badge :variant="getStatusBadge(item.status).variant">
                  {{ getStatusBadge(item.status).label }}
                </Badge>
              </div>

              <p class="text-sm text-[#737373] mb-3 line-clamp-2">
                {{ truncate(item.description, 80) }}
              </p>

              <div class="flex items-center gap-4 text-xs text-[#a3a3a3]">
                <span v-if="item.location" class="flex items-center gap-1">
                  <MapPin class="h-3 w-3" />
                  {{ item.location }}
                </span>
                <span>{{ formatDate(item.created_at) }}</span>
              </div>

              <div class="mt-3 pt-3 border-t border-[#e5e5e5] flex items-center gap-3 text-xs text-[#737373]">
                <span>认领 {{ item.total_claims }} 条</span>
                <span v-if="item.pending_count > 0" class="text-[#f97316]">
                  待处理 {{ item.pending_count }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- 分页 -->
        <div
          v-if="totalPages > 1"
          class="flex items-center justify-center gap-2 mt-6"
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
            {{ page }} / {{ totalPages }}
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
    </Card>
  </div>
</template>
