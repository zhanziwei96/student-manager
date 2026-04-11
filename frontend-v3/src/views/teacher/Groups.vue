<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useClasses, useToast } from '@/composables'
import { Card, Button, Select, DataContainer, Dialog, Badge } from '@/components/ui'
import {
  useTeacherGroups,
  useAutoAssign,
  useClassGroupSettings,
  useUpdateClassGroupSettings,
} from '@/features/group-collaboration'
import { Users, Shuffle, Crown } from 'lucide-vue-next'
import { getErrorMessage } from '@/lib/error'
import type { ClassInfo } from '@/api/classes'
import { groupsApi } from '@/api'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'

const { success: toastSuccess, error: toastError } = useToast()
const queryClient = useQueryClient()

// 班级选择
const { data: classes } = useClasses()
const selectedClass = ref('')
watch(
  () => classes.value,
  (list) => {
    if (list && list.length > 0 && !selectedClass.value) {
      selectedClass.value = list[0].name
    }
  },
  { immediate: true },
)

const classOptions = computed(() => [
  { value: '', label: '请选择班级', disabled: true },
  ...(classes.value || []).map((c: ClassInfo) => ({ value: c.name, label: c.name })),
])

// 小组列表
const { data: groups, isPending: loadingGroups } = useTeacherGroups(selectedClass)

// 小组人数上限设置
const { data: groupSettings } = useClassGroupSettings(selectedClass)
const { mutateAsync: updateSettings } = useUpdateClassGroupSettings()
const maxMembers = ref(5)
const savingSettings = ref(false)

// Sync settings data to local ref
watch(() => groupSettings.value, (s) => {
  if (s) maxMembers.value = s.max_members_per_group
})

// 自动分配
const { mutateAsync: autoAssign, isPending: autoAssigning } = useAutoAssign()
async function handleAutoAssign() {
  if (!selectedClass.value) return
  try {
    await autoAssign({ className: selectedClass.value })
    toastSuccess('自动分组完成')
  } catch (err) {
    toastError(getErrorMessage(err) || '自动分组失败')
  }
}

async function handleSaveSettings() {
  if (!selectedClass.value) return
  if (maxMembers.value < 2 || maxMembers.value > 10) {
    toastError('每组上限需在 2-10 之间')
    return
  }
  try {
    savingSettings.value = true
    await updateSettings({ class_name: selectedClass.value, max_members_per_group: maxMembers.value })
    toastSuccess('小组人数上限已更新')
  } catch (err) {
    toastError(getErrorMessage(err) || '设置失败')
  } finally {
    savingSettings.value = false
  }
}

// 转让组长
const showTransferDialog = ref(false)
const transferGroupId = ref<number | null>(null)
const newLeaderId = ref('')
const transferring = ref(false)

function openTransfer(groupId: number) {
  transferGroupId.value = groupId
  newLeaderId.value = ''
  showTransferDialog.value = true
}

async function handleTransfer() {
  if (!transferGroupId.value || !newLeaderId.value) return
  try {
    transferring.value = true
    await groupsApi.transferLeader(transferGroupId.value, newLeaderId.value)
    toastSuccess('组长转让成功')
    showTransferDialog.value = false
    queryClient.invalidateQueries({ queryKey: ['teacher-groups'] })
  } catch (err) {
    toastError(getErrorMessage(err) || '转让失败')
  } finally {
    transferring.value = false
  }
}

// 解散申请
const { data: dissolutions, isPending: loadingDissolutions } = useQuery({
  queryKey: ['dissolution-requests'],
  queryFn: () => groupsApi.getDissolutionRequests(),
})

const { mutateAsync: approveDissolution } = useMutation({
  mutationFn: (reqId: number) => groupsApi.approveDissolution(reqId),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['dissolution-requests'] })
    queryClient.invalidateQueries({ queryKey: ['teacher-groups'] })
  },
})
const { mutateAsync: rejectDissolution } = useMutation({
  mutationFn: (reqId: number) => groupsApi.rejectDissolution(reqId),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['dissolution-requests'] })
  },
})

async function handleApproveDissolution(reqId: number) {
  try {
    await approveDissolution(reqId)
    toastSuccess('已批准解散')
  } catch (err) {
    toastError(getErrorMessage(err) || '操作失败')
  }
}

async function handleRejectDissolution(reqId: number) {
  try {
    await rejectDissolution(reqId)
    toastSuccess('已拒绝解散')
  } catch (err) {
    toastError(getErrorMessage(err) || '操作失败')
  }
}
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-medium text-black">
        小组管理
      </h1>
      <p class="text-[#737373] mt-1">
        查看班级小组并处理解散申请
      </p>
    </div>

    <!-- 班级小组 -->
    <Card class="bg-white border-[#e5e5e5] p-5">
      <div class="flex flex-col sm:flex-row sm:flex-wrap sm:items-center justify-between gap-3 mb-4">
        <div class="flex flex-col sm:flex-row sm:items-center gap-3">
          <Select v-model="selectedClass" :options="classOptions" class="w-full sm:w-48" />
          <div class="flex items-center gap-2">
            <span class="text-sm text-[#737373]">每组上限</span>
            <input
              v-model.number="maxMembers"
              type="number"
              min="2"
              max="10"
              class="w-16 rounded-full border border-[#e5e5e5] bg-white px-3 py-1.5 text-sm text-black text-center focus:outline-none focus:ring-2 focus:ring-[#3b82f6]/50"
            >
            <span class="text-sm text-[#737373]">人</span>
            <Button size="sm" variant="cta" :loading="savingSettings" @click="handleSaveSettings">保存</Button>
          </div>
          <Button
            :loading="autoAssigning"
            @click="handleAutoAssign"
          >
            <Shuffle class="h-4 w-4 mr-1" />
            自动分组
          </Button>
        </div>
        <span class="text-sm text-[#737373]">
          共 {{ (groups || []).length }} 个小组
        </span>
      </div>

      <DataContainer
        :loading="loadingGroups"
        :has-data="(groups || []).length > 0"
        empty-text="该班级暂无小组"
      >
        <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <div
            v-for="g in groups"
            :key="g.id"
            class="rounded-xl border border-[#e5e5e5] bg-white p-4"
          >
            <div class="flex items-start justify-between">
              <div>
                <h4 class="font-medium text-black">
                  {{ g.name }}
                </h4>
                <div class="mt-1 flex items-center gap-2 text-xs text-[#737373]">
                  <Users class="h-3.5 w-3.5" />
                  {{ g.member_count || (g.members ? g.members.length : 0) }} 人
                </div>
              </div>
              <Badge variant="secondary">
                <Crown class="h-3 w-3 mr-1" />
                {{ g.leader_name || g.leader_student_id }}
              </Badge>
            </div>
            <div class="mt-3 flex gap-2">
              <Button
                size="sm"
                variant="outline"
                @click="openTransfer(g.id)"
              >
                转让组长
              </Button>
            </div>
          </div>
        </div>
      </DataContainer>
    </Card>

    <!-- 解散申请 -->
    <Card class="bg-white border-[#e5e5e5] p-5">
      <h2 class="text-lg font-medium text-black mb-4">
        待处理解散申请
      </h2>
      <DataContainer
        :loading="loadingDissolutions"
        :has-data="(dissolutions || []).length > 0"
        empty-text="暂无待处理解散申请"
      >
        <div class="space-y-3">
          <div
            v-for="req in dissolutions"
            :key="req.id"
            class="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[#e5e5e5] bg-[#fafafa] p-4"
          >
            <div>
              <p class="text-sm text-black font-medium">
                小组 ID: {{ req.group_id }}
              </p>
              <p class="text-xs text-[#737373] mt-0.5">
                {{ req.reason }}
              </p>
              <p class="text-[11px] text-[#a3a3a3] mt-0.5">
                {{ new Date(req.created_at).toLocaleString() }}
              </p>
            </div>
            <div class="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                @click="handleRejectDissolution(req.id)"
              >
                拒绝
              </Button>
              <Button
                size="sm"
                variant="destructive"
                @click="handleApproveDissolution(req.id)"
              >
                批准解散
              </Button>
            </div>
          </div>
        </div>
      </DataContainer>
    </Card>

    <Dialog
      v-model:open="showTransferDialog"
      title="转让组长"
    >
      <div class="space-y-3">
        <p class="text-sm text-[#737373]">
          输入新组长的学号
        </p>
        <input
          v-model="newLeaderId"
          placeholder="学号"
          class="w-full rounded-full border border-[#e5e5e5] bg-white px-3 py-2 text-sm text-black placeholder:text-[#a3a3a3] focus:outline-none focus:ring-2 focus:ring-[#3b82f6]/50"
        >
      </div>
      <template #footer>
        <div class="flex w-full gap-2 sm:justify-end">
          <Button
            variant="outline"
            @click="showTransferDialog = false"
          >
            取消
          </Button>
          <Button
            variant="cta"
            :loading="transferring"
            @click="handleTransfer"
          >
            确认转让
          </Button>
        </div>
      </template>
    </Dialog>
  </div>
</template>
