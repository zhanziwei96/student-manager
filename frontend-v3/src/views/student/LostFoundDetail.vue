<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  useStudentLostFoundDetail,
  useCreateLostFoundComment,
  useClaimLostFoundItem,
} from '@/composables/useLostFound'
import { Card, Button, Badge, DataContainer, Dialog } from '@/components/ui'
import { ArrowLeft, MapPin, User, Clock, MessageCircle, Send } from 'lucide-vue-next'
import type { ClaimStatus } from '@/types/lostFound'

const route = useRoute()
const router = useRouter()

const itemId = computed(() => Number(route.params.id))

const { data: detail, isPending, error, refetch } = useStudentLostFoundDetail(() => itemId.value)

const { mutateAsync: createComment, isPending: submittingComment } = useCreateLostFoundComment()
const { mutateAsync: claimItem, isPending: claiming } = useClaimLostFoundItem()

// 评论
const commentContent = ref('')

async function handleSubmitComment() {
  const content = commentContent.value.trim()
  if (!content) return
  await createComment({ itemId: itemId.value, data: { content } })
  commentContent.value = ''
}

// 认领弹窗
const showClaimModal = ref(false)
const claimContact = ref('')
const claimMessage = ref('')

function openClaimModal() {
  claimContact.value = ''
  claimMessage.value = ''
  showClaimModal.value = true
}

async function handleSubmitClaim() {
  const contact = claimContact.value.trim()
  if (!contact) return
  await claimItem({
    itemId: itemId.value,
    data: {
      contact,
      message: claimMessage.value.trim() || undefined,
    },
  })
  showClaimModal.value = false
}

// 状态
const isClosed = computed(() => detail.value?.status === 'closed')

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

const claimStatusLabel: Record<ClaimStatus, string> = {
  pending: '审核中',
  confirmed: '已确认',
  rejected: '已拒绝',
}

const claimStatusVariant: Record<ClaimStatus, string> = {
  pending: 'bg-yellow-500/15 text-yellow-600 border-yellow-500/30',
  confirmed: 'bg-green-500/15 text-green-600 border-green-500/30',
  rejected: 'bg-red-500/15 text-red-600 border-red-500/30',
}

function formatDate(date: string) {
  try {
    return new Date(date).toLocaleString('zh-CN')
  } catch {
    return date
  }
}

function goBack() {
  router.push({ name: 'StudentLostFound' })
}
</script>

<template>
  <div class="space-y-5">
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
      :has-data="!!detail"
      empty-text="物品不存在"
      @retry="refetch"
    >
      <div v-if="detail" class="space-y-5">
        <!-- 物品信息 -->
        <Card class="bg-white border-[#e5e5e5] p-5">
          <div class="flex items-start justify-between gap-3 mb-4">
            <h1 class="text-2xl font-medium text-black">
              {{ detail.title }}
            </h1>
            <Badge
              :class="statusVariant[detail.status]"
              class="flex-shrink-0"
            >
              {{ statusLabel[detail.status] }}
            </Badge>
          </div>

          <div class="flex flex-wrap items-center gap-4 text-sm text-[#737373] mb-4">
            <span v-if="detail.publisher_name" class="flex items-center gap-1">
              <User class="h-4 w-4" />
              {{ detail.publisher_name }}
            </span>
            <span v-if="detail.location" class="flex items-center gap-1">
              <MapPin class="h-4 w-4" />
              {{ detail.location }}
            </span>
            <span class="flex items-center gap-1">
              <Clock class="h-4 w-4" />
              {{ formatDate(detail.created_at) }}
            </span>
          </div>

          <!-- 图片 -->
          <div v-if="detail.image_url" class="mb-4">
            <img
              :src="detail.image_url"
              :alt="detail.title"
              class="max-w-full max-h-80 rounded-xl object-cover"
            >
          </div>

          <p class="text-sm text-[#262626] leading-relaxed whitespace-pre-wrap">
            {{ detail.description }}
          </p>

          <!-- 我的认领状态 -->
          <div
            v-if="detail.my_claim"
            class="mt-4 p-3 rounded-xl border border-[#e5e5e5] bg-[#fafafa]"
          >
            <div class="flex items-center gap-2">
              <span class="text-sm text-[#737373]">我的认领状态：</span>
              <Badge :class="claimStatusVariant[detail.my_claim.status]">
                {{ claimStatusLabel[detail.my_claim.status] }}
              </Badge>
            </div>
          </div>

          <!-- 认领按钮 -->
          <div v-if="!isClosed && !detail.my_claim" class="mt-4">
            <Button @click="openClaimModal">
              申请认领
            </Button>
          </div>
        </Card>

        <!-- 评论区 -->
        <Card class="bg-white border-[#e5e5e5] p-5">
          <h2 class="text-lg font-medium text-black mb-4 flex items-center gap-2">
            <MessageCircle class="h-5 w-5" />
            评论 ({{ detail.comments.length }})
          </h2>

          <!-- 评论列表 -->
          <div v-if="detail.comments.length > 0" class="space-y-3 mb-4">
            <div
              v-for="comment in detail.comments"
              :key="comment.id"
              class="rounded-xl border border-[#e5e5e5] bg-[#fafafa] p-3"
            >
              <div class="flex items-center gap-2 mb-1">
                <span class="text-sm font-medium text-black">匿名用户</span>
                <span class="text-xs text-[#a3a3a3]">
                  {{ formatDate(comment.created_at) }}
                </span>
              </div>
              <p class="text-sm text-[#262626] whitespace-pre-wrap">
                {{ comment.content }}
              </p>
            </div>
          </div>
          <p v-else class="text-sm text-[#a3a3a3] mb-4">
            暂无评论
          </p>

          <!-- 评论输入 -->
          <div v-if="!isClosed" class="flex gap-2">
            <input
              v-model="commentContent"
              type="text"
              placeholder="写下你的评论..."
              class="flex-1 rounded-full border border-[#e5e5e5] bg-white px-4 py-2 text-sm text-black placeholder:text-[#a3a3a3] focus:outline-none focus:ring-2 focus:ring-[#3b82f6]/50"
              @keyup.enter="handleSubmitComment"
            >
            <Button
              :loading="submittingComment"
              :disabled="!commentContent.trim()"
              @click="handleSubmitComment"
            >
              <Send class="h-4 w-4 mr-1" />
              发送
            </Button>
          </div>
          <p v-else class="text-sm text-[#a3a3a3]">
            该物品已关闭，无法发表评论
          </p>
        </Card>
      </div>
    </DataContainer>

    <!-- 认领弹窗 -->
    <Dialog
      v-model:open="showClaimModal"
      title="申请认领"
      description="请填写联系方式，以便物品发布者与你联系"
    >
      <div class="space-y-3">
        <div>
          <label class="block text-sm font-medium text-black mb-1">
            联系方式 <span class="text-red-500">*</span>
          </label>
          <input
            v-model="claimContact"
            type="text"
            placeholder="手机号/微信号/QQ号"
            class="w-full rounded-full border border-[#e5e5e5] bg-white px-4 py-2 text-sm text-black placeholder:text-[#a3a3a3] focus:outline-none focus:ring-2 focus:ring-[#3b82f6]/50"
          >
        </div>
        <div>
          <label class="block text-sm font-medium text-black mb-1">
            留言（可选）
          </label>
          <textarea
            v-model="claimMessage"
            rows="3"
            placeholder="补充说明..."
            class="w-full rounded-xl border border-[#e5e5e5] bg-white px-4 py-2 text-sm text-black placeholder:text-[#a3a3a3] focus:outline-none focus:ring-2 focus:ring-[#3b82f6]/50 resize-none"
          />
        </div>
      </div>
      <template #footer>
        <div class="flex w-full gap-2 sm:justify-end">
          <Button
            variant="outline"
            @click="showClaimModal = false"
          >
            取消
          </Button>
          <Button
            :loading="claiming"
            :disabled="!claimContact.trim()"
            @click="handleSubmitClaim"
          >
            提交申请
          </Button>
        </div>
      </template>
    </Dialog>
  </div>
</template>
