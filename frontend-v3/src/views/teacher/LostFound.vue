<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Card, Button, Badge, Select, DataContainer, Input, ResponsiveDialog, PullToRefreshIndicator } from '@/components/ui'
import { useTeacherLostFoundItems, useDeleteLostFoundItem } from '@/composables/useLostFound'
import { usePullToRefresh } from '@/composables/usePullToRefresh'
import { useSwipeActions } from '@/composables/useSwipeActions'
import { Plus, MapPin, Search, ChevronLeft, ChevronRight, Trash2 } from 'lucide-vue-next'
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

const { data, isPending, refetch } = useTeacherLostFoundItems(() => queryParams.value)

// 下拉刷新：页面由 window 滚动（布局无局部滚动容器），以 documentElement 为容器
const pageRef = ref<HTMLElement | null>(null)
const { pulling, pullDistance, refreshing } = usePullToRefresh(pageRef, async () => {
  await refetch()
})

onMounted(() => {
  pageRef.value = document.documentElement
  // 抑制 Chrome Android 原生下拉刷新，避免与手势冲突
  document.documentElement.classList.add('overscroll-y-contain')
})

onUnmounted(() => {
  document.documentElement.classList.remove('overscroll-y-contain')
})

// 行左滑操作（HIG 手势）：露出「删除」按钮
const { bindRow, openRowId, activeRowId, rowOffset, closeRow } = useSwipeActions()

/** 行位移：手势中跟手，展开行驻留在 -64（threshold），其余归位 */
function rowTransform(id: number) {
  if (activeRowId.value === id) return rowOffset.value
  return openRowId.value === id ? -64 : 0
}

// 删除确认
const { mutateAsync: deleteItem, isPending: deleting } = useDeleteLostFoundItem()
const showDeleteDialog = ref(false)
const pendingDeleteId = ref<number | null>(null)

function askDelete(id: number) {
  pendingDeleteId.value = id
  showDeleteDialog.value = true
  closeRow()
}

async function handleDelete() {
  if (pendingDeleteId.value === null) return
  await deleteItem(pendingDeleteId.value)
  showDeleteDialog.value = false
  pendingDeleteId.value = null
}

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
  // 行已展开时点击仅收起，不跳转
  if (openRowId.value === id) {
    closeRow()
    return
  }
  router.push({ name: 'TeacherLostFoundDetail', params: { id } })
}

function goToCreate() {
  router.push({ name: 'TeacherLostFoundCreate' })
}
</script>

<template>
  <div class="overscroll-y-contain space-y-6">
    <PullToRefreshIndicator :pulling="pulling" :pull-distance="pullDistance" :refreshing="refreshing" />

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
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#525252]" />
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
            class="relative overflow-hidden rounded-xl"
          >
            <!-- 滑动操作层（行左滑露出） -->
            <div class="absolute inset-y-0 right-0 w-16">
              <button
                type="button"
                class="flex h-full w-full flex-col items-center justify-center gap-1 bg-red-500 text-xs text-white"
                @click.stop="askDelete(item.id)"
              >
                <Trash2 class="h-4 w-4" />
                删除
              </button>
            </div>
            <!-- 行内容层（跟手左移） -->
            <div
              class="relative"
              :class="{ 'transition-transform duration-200': activeRowId !== item.id }"
              :style="{ transform: `translateX(${rowTransform(item.id)}px)` }"
              v-on="bindRow(item.id)"
            >
              <div
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

                  <div class="flex items-center gap-4 text-xs text-[#525252]">
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

    <!-- 删除确认 -->
    <ResponsiveDialog v-model:open="showDeleteDialog" title="确认删除" description="删除后不可恢复，确定要删除此物品吗？">
      <div class="flex justify-end gap-2 mt-4">
        <Button variant="outline" @click="showDeleteDialog = false">取消</Button>
        <Button variant="destructive" class="max-md:border-transparent max-md:bg-transparent max-md:text-[#ef4444]" :loading="deleting" @click="handleDelete">确认删除</Button>
      </div>
    </ResponsiveDialog>
  </div>
</template>
