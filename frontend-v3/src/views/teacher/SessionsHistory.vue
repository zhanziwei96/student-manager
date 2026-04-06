<script setup lang="ts">
import { ref } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { courseSessionApi } from '@/api'
import { Card, Badge, Button, DataContainer } from '@/components/ui'
import { History, Calendar, Clock, MapPin, BookOpen, Users, ChevronDown, ChevronUp } from 'lucide-vue-next'
import type { CourseSession } from '@/types'

const { data: historySessions, isPending, error, refetch } = useQuery({
  queryKey: ['courseSessions', 'history'],
  queryFn: () => courseSessionApi.getHistory(),
})

const expandedIds = ref<Set<number>>(new Set())

const toggleExpand = (id: number) => {
  const next = new Set(expandedIds.value)
  if (next.has(id)) {
    next.delete(id)
  } else {
    next.add(id)
  }
  expandedIds.value = next
}

const formatDateTime = (iso?: string) => {
  if (!iso) return '--'
  const d = new Date(iso)
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${mm}-${dd} ${hh}:${min}`
}

const statusBadge = (status: CourseSession['status']) => {
  switch (status) {
    case 'ended':
      return { label: '已结束', variant: 'secondary' as const }
    case 'cancelled':
      return { label: '已取消', variant: 'error' as const }
    default:
      return { label: status, variant: 'default' as const }
  }
}

const sourceBadge = (sourceType: CourseSession['source_type']) => {
  switch (sourceType) {
    case 'scheduled':
      return { label: '自动', variant: 'info' as const }
    case 'manual':
      return { label: '手动', variant: 'secondary' as const }
    case 'makeup':
      return { label: '补课', variant: 'primary' as const }
    default:
      return { label: sourceType, variant: 'default' as const }
  }
}
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-5">
      <div class="min-w-0">
        <h1 class="text-xl sm:text-2xl font-bold text-white flex items-center gap-2">
          <History class="h-6 w-6 text-primary" />
          课堂历史
        </h1>
        <p class="text-sm text-white/60 mt-1">
          查看已结束和已取消的课程记录
        </p>
      </div>
    </div>

    <!-- List -->
    <DataContainer
      :loading="isPending"
      :error="error"
      :has-data="(historySessions || []).length > 0"
      empty-text="暂无历史课堂记录"
      @retry="refetch"
    >
      <div class="space-y-3">
        <Card
          v-for="session in historySessions"
          :key="session.id"
          class="p-4 border-white/10 bg-white/[0.02] hover:bg-white/[0.04] transition-colors"
        >
          <div class="flex items-start justify-between">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-2">
                <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
                  <BookOpen class="h-4 w-4 text-primary" />
                </div>
                <h4 class="font-semibold text-base text-white truncate">
                  {{ session.course_name || '未命名课程' }}
                </h4>
              </div>

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm mb-3">
                <div class="flex items-center gap-2 text-white/60">
                  <Calendar class="h-3.5 w-3.5 text-white/40" />
                  <span>{{ session.class_name }}</span>
                </div>
                <div
                  v-if="session.classroom"
                  class="flex items-center gap-2 text-white/60"
                >
                  <MapPin class="h-3.5 w-3.5 text-white/40" />
                  <span>{{ session.classroom }}</span>
                </div>
                <div class="flex items-center gap-2 text-white/60">
                  <Clock class="h-3.5 w-3.5 text-white/40" />
                  <span>{{ formatDateTime(session.start_time) }} ~ {{ formatDateTime(session.end_time) }}</span>
                </div>
                <div
                  v-if="session.week_number != null"
                  class="flex items-center gap-2 text-white/60"
                >
                  <span class="text-xs px-1.5 py-0.5 rounded bg-white/5">第{{ session.week_number }}周</span>
                </div>
              </div>

              <div class="flex flex-wrap items-center gap-2">
                <Badge
                  :variant="statusBadge(session.status).variant"
                  class="text-xs"
                >
                  {{ statusBadge(session.status).label }}
                </Badge>
                <Badge
                  :variant="sourceBadge(session.source_type).variant"
                  class="text-xs"
                >
                  {{ sourceBadge(session.source_type).label }}
                </Badge>
                <span class="text-xs text-white/30">
                  课堂码: {{ session.session_code }}
                </span>
              </div>
            </div>

            <!-- 展开详情按钮 -->
            <Button
              variant="ghost"
              size="sm"
              class="h-8 px-2 text-white/40 hover:text-white flex-shrink-0"
              @click="toggleExpand(session.id)"
            >
              <Users class="h-4 w-4 mr-1" />
              <span class="hidden sm:inline">查看详情</span>
              <ChevronDown
                v-if="!expandedIds.has(session.id)"
                class="h-4 w-4 ml-1"
              />
              <ChevronUp
                v-else
                class="h-4 w-4 ml-1"
              />
            </Button>
          </div>

          <!-- 展开内容：签到人数（mock） -->
          <div
            v-if="expandedIds.has(session.id)"
            class="mt-3 pt-3 border-t border-white/10"
          >
            <div class="flex items-center gap-2 text-sm text-white/60">
              <Users class="h-4 w-4 text-white/40" />
              <span>已签到：--</span>
            </div>
          </div>
        </Card>
      </div>
    </DataContainer>
  </div>
</template>
