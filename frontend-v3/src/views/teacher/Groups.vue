<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useClasses, useToast } from '@/composables'
import { Card, Button, Select, Input, Label, DataContainer, Dialog, Badge } from '@/components/ui'
import {
  useTeacherGroups,
  useAutoAssign,
  useClassGroupSettings,
  useUpdateClassGroupSettings,
  useGroupScore,
  useGroupScoreLogs,
} from '@/features/group-collaboration'
import { Users, Shuffle, Crown, ChevronDown, ChevronUp, UserMinus, Trash2, Plus } from 'lucide-vue-next'
import { getErrorMessage } from '@/lib/error'
import type { AdminClass } from '@/types'
import type { GroupDetail } from '@/types/api'
import type { Group } from '@/api/groups'
import { groupsApi } from '@/api'
import { coursesApi } from '@/api/courses'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'

const { success: toastSuccess, error: toastError } = useToast()
const queryClient = useQueryClient()

// 班级选择
const { data: classes } = useClasses()
const selectedClassId = ref<number | ''>('')
watch(
  () => classes.value,
  (list) => {
    if (list && list.length > 0 && !selectedClassId.value) {
      selectedClassId.value = list[0].id
    }
  },
  { immediate: true },
)

const classOptions = computed(() => [
  { value: '', label: '请选择班级', disabled: true },
  ...(classes.value || []).map((c: AdminClass) => ({ value: c.id, label: c.display_name })),
])

// 课程下拉（小组按课程划分）
const { data: courses } = useQuery({
  queryKey: ['courses'],
  queryFn: () => coursesApi.list(),
})
const selectedCourseId = ref<number | string>('')
const courseOptions = computed(() => [
  { value: '', label: '全部课程' },
  ...(courses.value ?? []).map((c) => ({ value: c.id, label: c.name })),
])

// 小组列表（按课程过滤）
const selectedClassIdParam = computed(() => (selectedClassId.value === '' ? undefined : selectedClassId.value))
const { data: groups, isPending: loadingGroups } = useTeacherGroups(
  selectedClassIdParam,
  computed(() => (selectedCourseId.value === '' ? null : Number(selectedCourseId.value))),
)
const filteredGroups = computed(() => groups.value || [])

// 小组人数上限设置
const { data: groupSettings } = useClassGroupSettings(selectedClassIdParam)
const { mutateAsync: updateSettings } = useUpdateClassGroupSettings()
const maxMembers = ref(5)
const savingSettings = ref(false)

// Sync settings data to local ref
watch(() => groupSettings.value, (s) => {
  if (s) maxMembers.value = s.max_members_per_group
}, { immediate: true })

// 自动分配
const { mutateAsync: autoAssign, isPending: autoAssigning } = useAutoAssign()
async function handleAutoAssign() {
  if (selectedClassId.value === '' || selectedCourseId.value === '') {
    toastError('请先选择班级和课程')
    return
  }
  try {
    await autoAssign({ classId: selectedClassId.value, courseId: Number(selectedCourseId.value) })
    toastSuccess('自动分组完成')
  } catch (err) {
    toastError(getErrorMessage(err) || '自动分组失败')
  }
}

async function handleSaveSettings() {
  if (selectedClassId.value === '') return
  if (maxMembers.value < 2 || maxMembers.value > 10) {
    toastError('每组上限需在 2-10 之间')
    return
  }
  try {
    savingSettings.value = true
    await updateSettings({ class_id: selectedClassId.value, max_members_per_group: maxMembers.value })
    toastSuccess('小组人数上限已更新')
  } catch (err) {
    toastError(getErrorMessage(err) || '设置失败')
  } finally {
    savingSettings.value = false
  }
}

// 教师建组
const showCreateGroupDialog = ref(false)
const newGroupName = ref('')
const newGroupCourseId = ref<number | string>('')
const creatingGroup = ref(false)

function openCreateGroupDialog() {
  newGroupName.value = ''
  newGroupCourseId.value = ''
  showCreateGroupDialog.value = true
}

async function handleCreateGroup() {
  if (selectedClassId.value === '') return
  if (!newGroupName.value.trim()) {
    toastError('请输入小组名称')
    return
  }
  if (newGroupCourseId.value === '') {
    toastError('请选择课程')
    return
  }
  try {
    creatingGroup.value = true
    await groupsApi.createTeacherGroup({
      class_id: selectedClassId.value,
      name: newGroupName.value.trim(),
      course_id: Number(newGroupCourseId.value),
    })
    toastSuccess('小组创建成功')
    showCreateGroupDialog.value = false
    queryClient.invalidateQueries({ queryKey: ['teacher-groups'] })
  } catch (err) {
    toastError(getErrorMessage(err) || '创建失败')
  } finally {
    creatingGroup.value = false
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

// 展开/收起小组成员
const expandedGroupId = ref<number | null>(null)
const groupDetail = ref<GroupDetail | null>(null)
const loadingDetail = ref(false)

async function toggleGroup(groupId: number) {
  if (expandedGroupId.value === groupId) {
    expandedGroupId.value = null
    groupDetail.value = null
  } else {
    expandedGroupId.value = groupId
    loadingDetail.value = true
    try {
      groupDetail.value = await groupsApi.getGroupDetail(groupId)
    } catch (err) {
      toastError(getErrorMessage(err) || '获取小组详情失败')
    } finally {
      loadingDetail.value = false
    }
  }
}

// 踢出成员
const removingMember = ref<{ groupId: number; studentId: string } | null>(null)

async function handleRemoveMember(groupId: number, studentId: string) {
  removingMember.value = { groupId, studentId }
  try {
    await groupsApi.removeMember(groupId, studentId)
    toastSuccess('成员已踢出')
    await queryClient.invalidateQueries({ queryKey: ['teacher-groups'] })
    if (expandedGroupId.value === groupId) {
      // 刷新后检查小组是否仍存在（踢出最后一名成员后小组会自动解散）
      const updatedGroups = queryClient.getQueryData<Group[]>([
        'teacher-groups',
        selectedClassId.value === '' ? undefined : selectedClassId.value,
        selectedCourseId.value === '' ? null : Number(selectedCourseId.value),
      ])
      const stillExists = updatedGroups?.some((g: Group) => g.id === groupId)
      if (stillExists) {
        groupDetail.value = await groupsApi.getGroupDetail(groupId)
      } else {
        expandedGroupId.value = null
        groupDetail.value = null
      }
    }
  } catch (err) {
    toastError(getErrorMessage(err) || '踢出失败')
  } finally {
    removingMember.value = null
  }
}

// 解散小组
const showDissolveDialog = ref(false)
const dissolvingGroupId = ref<number | null>(null)
const dissolvingGroupName = ref('')
const dissolving = ref(false)

function confirmDissolve(groupId: number, groupName: string) {
  dissolvingGroupId.value = groupId
  dissolvingGroupName.value = groupName
  showDissolveDialog.value = true
}

async function handleDissolve() {
  if (!dissolvingGroupId.value) return
  try {
    dissolving.value = true
    await groupsApi.dissolveGroup(dissolvingGroupId.value)
    toastSuccess('小组已解散')
    showDissolveDialog.value = false
    if (expandedGroupId.value === dissolvingGroupId.value) {
      expandedGroupId.value = null
      groupDetail.value = null
    }
    queryClient.invalidateQueries({ queryKey: ['teacher-groups'] })
  } catch (err) {
    toastError(getErrorMessage(err) || '解散失败')
  } finally {
    dissolving.value = false
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

// 小组加减分
const showScoreDialog = ref(false)
const scoreGroup = ref<Group | null>(null)
const scoreChange = ref(0)
const scoreReason = ref('')
const updatingScore = ref(false)

const { mutateAsync: updateGroupScore } = useGroupScore()
const { data: scoreLogs, isPending: loadingScoreLogs } = useGroupScoreLogs(
  computed(() => scoreGroup.value?.id ?? null),
)

function openScoreDialog(group: Group) {
  scoreGroup.value = group
  scoreChange.value = 0
  scoreReason.value = ''
  showScoreDialog.value = true
}

async function handleUpdateScore() {
  if (!scoreGroup.value) return
  if (!scoreChange.value) {
    toastError('请输入分数变化值')
    return
  }
  if (!scoreReason.value.trim()) {
    toastError('请输入分数变化原因')
    return
  }
  try {
    updatingScore.value = true
    await updateGroupScore({
      groupId: scoreGroup.value.id,
      scoreChange: scoreChange.value,
      reason: scoreReason.value.trim(),
    })
    toastSuccess('小组分数已更新')
    showScoreDialog.value = false
  } catch (err) {
    toastError(getErrorMessage(err) || '更新分数失败')
  } finally {
    updatingScore.value = false
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
          <Select v-model="selectedClassId" :options="classOptions" class="w-full sm:w-48" />
          <Select v-model="selectedCourseId" :options="courseOptions" class="w-full sm:w-40" />
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
          <Button
            variant="outline"
            @click="openCreateGroupDialog"
          >
            <Plus class="h-4 w-4 mr-1" />
            建组
          </Button>
        </div>
        <span class="text-sm text-[#737373]">
          共 {{ (filteredGroups || []).length }} 个小组
        </span>
      </div>

      <DataContainer
        :loading="loadingGroups"
        :has-data="(filteredGroups || []).length > 0"
        empty-text="该班级暂无小组"
      >
        <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <div
            v-for="g in filteredGroups"
            :key="g.id"
            class="rounded-xl border border-[#e5e5e5] bg-white p-4"
          >
            <!-- 卡片头部：点击展开/收起 -->
            <div
              class="flex items-start justify-between cursor-pointer"
              @click="toggleGroup(g.id)"
            >
              <div>
                <h4 class="font-medium text-black">
                  {{ g.name }}
                </h4>
                <div class="mt-1 flex items-center gap-2 text-xs text-[#737373]">
                  <Users class="h-3.5 w-3.5" />
                  {{ g.member_count || (g.members ? g.members.length : 0) }} 人
                </div>
              </div>
              <div class="flex items-center gap-2">
                <Badge variant="secondary">
                  <Crown class="h-3 w-3 mr-1" />
                  {{ g.leader_name || g.leader_student_id }}
                </Badge>
                <component
                  :is="expandedGroupId === g.id ? ChevronUp : ChevronDown"
                  class="h-4 w-4 text-[#737373]"
                />
              </div>
            </div>

            <!-- 科目与分数 -->
            <div class="mt-2 flex flex-wrap items-center gap-2">
              <Badge variant="secondary">
                {{ g.course_name || '未分科' }}
              </Badge>
              <span class="text-xs text-[#737373]">分数</span>
              <span class="text-sm font-medium text-black">{{ g.score ?? 0 }}</span>
            </div>

            <!-- 操作按钮 -->
            <div class="mt-3 flex flex-wrap gap-2">
              <Button
                size="sm"
                variant="cta"
                data-testid="open-group-score-btn"
                @click.stop="openScoreDialog(g)"
              >
                <Plus class="h-3.5 w-3.5 mr-1" />
                加减分
              </Button>
              <Button
                size="sm"
                variant="outline"
                @click.stop="openTransfer(g.id)"
              >
                转让组长
              </Button>
              <Button
                size="sm"
                variant="destructive"
                @click.stop="confirmDissolve(g.id, g.name)"
              >
                <Trash2 class="h-3.5 w-3.5 mr-1" />
                解散小组
              </Button>
            </div>

            <!-- 成员列表（展开时显示） -->
            <div v-if="expandedGroupId === g.id" class="mt-3 border-t border-[#e5e5e5] pt-3">
              <div v-if="loadingDetail" class="text-sm text-[#737373] py-2">
                加载中...
              </div>
              <div v-else-if="groupDetail && groupDetail.id === g.id" class="space-y-2">
                <div
                  v-for="member in groupDetail.members"
                  :key="member.student_id"
                  class="flex items-center justify-between py-1.5"
                >
                  <div class="flex items-center gap-2">
                    <span class="text-sm text-black">{{ member.student_name }}</span>
                    <span
                      v-if="member.student_id === g.leader_student_id"
                      class="text-xs text-[#6366f1]"
                    >
                      (组长)
                    </span>
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    :loading="removingMember?.groupId === g.id && removingMember?.studentId === member.student_id"
                    @click.stop="handleRemoveMember(g.id, member.student_id)"
                  >
                    <UserMinus class="h-3.5 w-3.5 mr-1" />
                    踢出
                  </Button>
                </div>
              </div>
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

    <!-- 解散确认对话框 -->
    <Dialog
      v-model:open="showDissolveDialog"
      title="解散小组"
    >
      <p class="text-sm text-[#737373]">
        确定要解散小组「{{ dissolvingGroupName }}」吗？此操作不可撤销。
      </p>
      <template #footer>
        <div class="flex w-full gap-2 sm:justify-end">
          <Button
            variant="outline"
            @click="showDissolveDialog = false"
          >
            取消
          </Button>
          <Button
            variant="destructive"
            :loading="dissolving"
            @click="handleDissolve"
          >
            确认解散
          </Button>
        </div>
      </template>
    </Dialog>

    <!-- 加减分弹窗 -->
    <Dialog
      v-model:open="showScoreDialog"
      :title="scoreGroup ? `加减分 - ${scoreGroup.name}` : '加减分'"
    >
      <div class="space-y-4">
        <div class="flex items-center justify-between rounded-lg bg-[#fafafa] px-3 py-2">
          <span class="text-sm text-[#737373]">当前分数</span>
          <span class="text-sm font-medium text-black">{{ scoreGroup?.score ?? 0 }}</span>
        </div>
        <div class="space-y-2">
          <Label for="groupScoreChange">分数变化</Label>
          <Input
            id="groupScoreChange"
            v-model.number="scoreChange"
            type="number"
            placeholder="正数加分，负数扣分"
            data-testid="group-score-change"
          />
        </div>
        <div class="space-y-2">
          <Label for="groupScoreReason">原因</Label>
          <Input
            id="groupScoreReason"
            v-model="scoreReason"
            placeholder="输入分数变化原因"
            data-testid="group-score-reason"
          />
        </div>
        <!-- 分数日志 -->
        <div class="space-y-2">
          <p class="text-sm font-medium text-black">分数日志</p>
          <p v-if="loadingScoreLogs" class="text-xs text-[#737373]">加载中...</p>
          <p v-else-if="!scoreLogs || scoreLogs.length === 0" class="text-xs text-[#737373]">
            暂无分数变更记录
          </p>
          <div v-else class="max-h-40 space-y-1 overflow-y-auto">
            <div
              v-for="(log, idx) in scoreLogs"
              :key="idx"
              class="flex items-center justify-between text-xs"
              data-testid="group-score-log"
            >
              <span class="text-[#737373]">{{ log.reason || '未填写原因' }}</span>
              <span :class="(log.delta ?? 0) >= 0 ? 'text-[#16a34a]' : 'text-[#dc2626]'">
                {{ (log.delta ?? 0) >= 0 ? '+' : '' }}{{ log.delta }}（{{ log.old_score }} → {{ log.new_score }}）
              </span>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="flex w-full gap-2 sm:justify-end">
          <Button
            variant="outline"
            @click="showScoreDialog = false"
          >
            取消
          </Button>
          <Button
            variant="cta"
            :loading="updatingScore"
            data-testid="confirm-group-score-btn"
            @click="handleUpdateScore"
          >
            确认加减分
          </Button>
        </div>
      </template>
    </Dialog>

    <!-- 建组 Dialog -->
    <Dialog
      v-model:open="showCreateGroupDialog"
      title="创建小组"
      description="小组按课程划分，学生可申请加入"
    >
      <div class="space-y-3">
        <div class="space-y-1">
          <label class="text-sm text-[#737373]">课程</label>
          <Select
            v-model="newGroupCourseId"
            :options="courses?.filter((c) => c.status === 'active').map((c) => ({ value: c.id, label: c.name })) ?? []"
            placeholder="选择课程"
          />
        </div>
        <div class="space-y-1">
          <label class="text-sm text-[#737373]">小组名称</label>
          <input
            v-model="newGroupName"
            placeholder="如：数学A组"
            class="w-full rounded-full border border-[#e5e5e5] bg-white px-3 py-2 text-sm text-black placeholder:text-[#a3a3a3] focus:outline-none focus:ring-2 focus:ring-[#3b82f6]/50"
          >
        </div>
      </div>
      <template #footer>
        <div class="flex w-full gap-2 sm:justify-end">
          <Button
            variant="outline"
            @click="showCreateGroupDialog = false"
          >
            取消
          </Button>
          <Button
            variant="cta"
            :loading="creatingGroup"
            @click="handleCreateGroup"
          >
            创建
          </Button>
        </div>
      </template>
    </Dialog>
  </div>
</template>
