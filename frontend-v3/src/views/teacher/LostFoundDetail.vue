<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Card, Button, Badge, DataContainer, Dialog } from '@/components/ui'
import {
  useTeacherLostFoundDetail,
  useConfirmClaim,
  useRejectClaim,
  useDeleteLostFoundItem,
} from '@/composables/useLostFound'
import {
  ArrowLeft,
  Edit,
  Trash2,
  MapPin,
  Calendar,
  User,
  MessageSquare,
  CheckCircle,
  XCircle,
  Clock,
  Phone,
} from 'lucide-vue-next'
import type { LostFoundStatus, ClaimStatus } from '@/types/lostFound'

const route = useRoute()
const router = useRouter()

const itemId = computed(() => Number(route.params.id))

const { data: item, isPending, error } = useTeacherLostFoundDetail(() => itemId.value)

const { mutateAsync: confirmClaim, isPending: confirming } = useConfirmClaim()
const { mutateAsync: rejectClaim, isPending: rejecting } = useRejectClaim()
const { mutateAsync: deleteItem, isPending: deleting } = useDeleteLostFoundItem()

// 删除确认
const showDeleteDialog = ref(false)

async function handleDelete() {
  await deleteItem(itemId.value)
  showDeleteDialog.value = false
  router.push({ name: 'TeacherLostFound' })
}

async function handleConfirmClaim(claimId: number) {
  await confirmClaim({ itemId: itemId.value, claimId })
}

async function handleRejectClaim(claimId: number) {
  await rejectClaim({ itemId: itemId.value, claimId })
}

function goToEdit() {
  router.push({ name: 'TeacherLostFoundEdit', params: { id: itemId.value } })
}

function goBack() {
  router.push({ name: 'TeacherLostFound' })
}

function getStatusBadge(status: LostFoundStatus) {
  const map: Record<LostFoundStatus, { label: string; variant: 'success' | 'warning' | 'default' }> = {
    open: { label: '发布中', variant: 'success' },
    claiming: { label: '认领中', variant: 'warning' },
    closed: { label: '已关闭', variant: 'default' },
  }
  return map[status]
}

function getClaimStatusBadge(status: ClaimStatus) {
  const map: Record<ClaimStatus, { label: string; variant: 'success' | 'warning' | 'error' }> = {
    pending: { label: '待处理', variant: 'warning' },
    confirmed: { label: '已确认', variant: 'success' },
    rejected: { label: '已拒绝', variant: 'error' },
  }
  return map[status]
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('zh-CN')
}
</script>

<template>
  <div class="space-y-6">
    <!-- 返回按钮 -->
    <button
      class="flex items-center gap-1 text-sm text-[#737373] hover:text-black transition-colors"
      @click="goBack"
    >
      <ArrowLeft class="h-4 w-4" />
      返回列表
    </button>

    <DataContainer
      :loading="isPending"
      :error="error"
      :has-data="!!item"
      empty-text="物品不存在"
      @retry="() => {}"
    >
      <template v-if="item">
        <!-- 标题操作栏 -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
          <div class="flex items-center gap-3">
            <h1 class="text-2xl font-medium text-black">
              {{ item.title }}
            </h1>
            <Badge :variant="getStatusBadge(item.status).variant">
              {{ getStatusBadge(item.status).label }}
            </Badge>
          </div>
          <div class="flex gap-2">
            <Button variant="outline" @click="goToEdit">
              <Edit class="h-4 w-4" />
              编辑
            </Button>
            <Button variant="destructive" @click="showDeleteDialog = true">
              <Trash2 class="h-4 w-4" />
              删除
            </Button>
          </div>
        </div>

        <!-- 物品信息 -->
        <Card class="bg-white border-[#e5e5e5] p-5 mb-6">
          <div class="grid gap-6 md:grid-cols-2">
            <!-- 图片 -->
            <div v-if="item.image_url" class="rounded-xl overflow-hidden border border-[#e5e5e5]">
              <img
                :src="item.image_url"
                :alt="item.title"
                class="w-full h-64 object-cover"
              >
            </div>

            <!-- 详情 -->
            <div class="space-y-4">
              <div>
                <h3 class="text-sm font-medium text-[#737373] mb-1">描述</h3>
                <p class="text-black whitespace-pre-wrap">{{ item.description }}</p>
              </div>

              <div v-if="item.location" class="flex items-center gap-2 text-sm">
                <MapPin class="h-4 w-4 text-[#a3a3a3]" />
                <span class="text-[#737373]">{{ item.location }}</span>
              </div>

              <div class="flex items-center gap-2 text-sm">
                <User class="h-4 w-4 text-[#a3a3a3]" />
                <span class="text-[#737373]">发布者: {{ item.publisher_name || '未知' }}</span>
              </div>

              <div class="flex items-center gap-2 text-sm">
                <Calendar class="h-4 w-4 text-[#a3a3a3]" />
                <span class="text-[#737373]">发布时间: {{ formatDate(item.created_at) }}</span>
              </div>

              <div class="flex items-center gap-2 text-sm">
                <Clock class="h-4 w-4 text-[#a3a3a3]" />
                <span class="text-[#737373]">更新时间: {{ formatDate(item.updated_at) }}</span>
              </div>
            </div>
          </div>
        </Card>

        <!-- 评论区 -->
        <Card class="bg-white border-[#e5e5e5] p-5 mb-6">
          <h2 class="text-lg font-medium text-black mb-4 flex items-center gap-2">
            <MessageSquare class="h-5 w-5" />
            评论 ({{ item.comments.length }})
          </h2>

          <div v-if="item.comments.length === 0" class="text-sm text-[#a3a3a3] py-4 text-center">
            暂无评论
          </div>

          <div v-else class="space-y-3">
            <div
              v-for="comment in item.comments"
              :key="comment.id"
              class="rounded-xl border border-[#e5e5e5] bg-[#fafafa] p-3"
            >
              <div class="flex items-center justify-between mb-1">
                <span class="text-sm font-medium text-black">{{ comment.user_name || '匿名用户' }}</span>
                <span class="text-xs text-[#a3a3a3]">{{ formatDate(comment.created_at) }}</span>
              </div>
              <p class="text-sm text-[#737373]">{{ comment.content }}</p>
            </div>
          </div>
        </Card>

        <!-- 认领列表 -->
        <Card class="bg-white border-[#e5e5e5] p-5">
          <h2 class="text-lg font-medium text-black mb-4 flex items-center gap-2">
            <CheckCircle class="h-5 w-5" />
            认领申请 ({{ item.claims.length }})
            <Badge v-if="item.pending_count > 0" variant="warning">
              {{ item.pending_count }} 待处理
            </Badge>
          </h2>

          <div v-if="item.claims.length === 0" class="text-sm text-[#a3a3a3] py-4 text-center">
            暂无认领申请
          </div>

          <div v-else class="space-y-3">
            <div
              v-for="claim in item.claims"
              :key="claim.id"
              class="rounded-xl border border-[#e5e5e5] bg-[#fafafa] p-4"
            >
              <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div class="space-y-1">
                  <div class="flex items-center gap-2">
                    <span class="text-sm font-medium text-black">{{ claim.student_name || '未知学生' }}</span>
                    <Badge :variant="getClaimStatusBadge(claim.status).variant">
                      {{ getClaimStatusBadge(claim.status).label }}
                    </Badge>
                  </div>

                  <div class="flex items-center gap-2 text-sm text-[#737373]">
                    <Phone class="h-3.5 w-3.5 text-[#a3a3a3]" />
                    {{ claim.contact }}
                  </div>

                  <p v-if="claim.message" class="text-sm text-[#737373]">
                    {{ claim.message }}
                  </p>

                  <span class="text-xs text-[#a3a3a3]">{{ formatDate(claim.created_at) }}</span>
                </div>

                <!-- 操作按钮 -->
                <div v-if="claim.status === 'pending'" class="flex gap-2">
                  <Button
                    variant="cta"
                    size="sm"
                    :loading="confirming"
                    @click="handleConfirmClaim(claim.id)"
                  >
                    <CheckCircle class="h-3.5 w-3.5" />
                    确认
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    :loading="rejecting"
                    @click="handleRejectClaim(claim.id)"
                  >
                    <XCircle class="h-3.5 w-3.5" />
                    拒绝
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </template>
    </DataContainer>

    <!-- 删除确认对话框 -->
    <Dialog v-model:open="showDeleteDialog" title="确认删除" description="删除后不可恢复，确定要删除此物品吗？">
      <div class="flex justify-end gap-2 mt-4">
        <Button variant="outline" @click="showDeleteDialog = false">取消</Button>
        <Button variant="destructive" :loading="deleting" @click="handleDelete">确认删除</Button>
      </div>
    </Dialog>
  </div>
</template>
