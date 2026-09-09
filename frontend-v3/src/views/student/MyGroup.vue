<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useToast } from '@/composables'
import { Card, Button, Select, Label, DataContainer, Dialog, Badge } from '@/components/ui'
import {
  useMyGroups,
  useStudentGroups,
  useCreateGroup,
  useJoinGroup,
  useApproveJoin,
} from '@/features/group-collaboration'
import { Users, Crown, Plus, LogIn, Trash2, LogOut } from 'lucide-vue-next'
import { getErrorMessage } from '@/lib/error'
import { groupsApi } from '@/api'
import { coursesApi } from '@/api/courses'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { useAuthStore } from '@/stores'

const { success: toastSuccess, error: toastError } = useToast()
const queryClient = useQueryClient()
const authStore = useAuthStore()

// 学生本班级
const className = computed(() => authStore.user?.class_name || '')

// 我的小组（每科一个）+ 课程目录
const { data: myGroups, isPending: loadingMyGroups } = useMyGroups()
const { data: courses } = useQuery({
  queryKey: ['courses'],
  queryFn: () => coursesApi.list(),
})

// 课程选择（默认选中第一个已有小组的课程）
const selectedCourseId = ref<number | string>('')
watch(myGroups, (groups) => {
  if (selectedCourseId.value === '' && groups && groups.length > 0) {
    selectedCourseId.value = groups[0].course_id ?? ''
  }
}, { immediate: true })

const courseOptions = computed(() => {
  const list = courses.value ?? []
  return list.filter((c) => c.status === 'active').map((c) => ({ value: c.id, label: c.name }))
})

// 当前课程下我的小组
const currentGroup = computed(() =>
  (myGroups.value ?? []).find((g) => g.course_id === Number(selectedCourseId.value)) ?? null,
)

// 退出小组
const { mutateAsync: leaveGroup, isPending: leaving } = useMutation({
  mutationFn: () => groupsApi.leaveGroup(),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['my-groups'] })
    queryClient.invalidateQueries({ queryKey: ['student-groups'] })
    toastSuccess('已退出小组')
  },
  onError: (err) => toastError(getErrorMessage(err) || '退出失败'),
})

// 解散申请
const showDissolveDialog = ref(false)
const dissolveReason = ref('')
const dissolving = ref(false)

const { mutateAsync: requestDissolution } = useMutation({
  mutationFn: (reason: string) => groupsApi.requestDissolution(reason),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['my-groups'] })
  },
})

async function handleDissolve() {
  if (!dissolveReason.value.trim()) {
    toastError('请填写解散原因')
    return
  }
  try {
    dissolving.value = true
    await requestDissolution(dissolveReason.value.trim())
    toastSuccess('解散申请已提交')
    showDissolveDialog.value = false
    dissolveReason.value = ''
  } catch (err) {
    toastError(getErrorMessage(err) || '申请失败')
  } finally {
    dissolving.value = false
  }
}

// 创建小组
const showCreateDialog = ref(false)
const creating = ref(false)
const createForm = ref({ name: '' })
const createCourseId = ref<number | string>('')

function openCreateDialog() {
  createForm.value = { name: '' }
  createCourseId.value = selectedCourseId.value === '' ? '' : selectedCourseId.value
  showCreateDialog.value = true
}

const { mutateAsync: createGroup } = useCreateGroup()
async function handleCreate() {
  if (!createForm.value.name.trim()) {
    toastError('请填写小组名称')
    return
  }
  if (createCourseId.value === '') {
    toastError('请选择课程')
    return
  }
  try {
    creating.value = true
    await createGroup({
      className: className.value,
      name: createForm.value.name.trim(),
      courseId: Number(createCourseId.value),
    })
    toastSuccess('小组创建成功')
    showCreateDialog.value = false
  } catch (err) {
    toastError(getErrorMessage(err) || '创建失败')
  } finally {
    creating.value = false
  }
}

// 可加入小组（当前课程、未入组时）
const { data: availableGroups, isPending: loadingGroups } = useStudentGroups(
  className,
  computed(() => (selectedCourseId.value === '' ? null : Number(selectedCourseId.value))),
)
const { mutateAsync: joinGroup, isPending: joining } = useJoinGroup()

async function handleJoin(groupId: number) {
  try {
    await joinGroup(groupId)
    toastSuccess('入组申请已提交')
  } catch (err) {
    toastError(getErrorMessage(err) || '申请失败')
  }
}

// 审批入组申请
const { mutateAsync: approveJoin } = useApproveJoin()
async function handleApprove(reqId: number) {
  try {
    await approveJoin(reqId)
    toastSuccess('已批准加入')
    queryClient.invalidateQueries({ queryKey: ['my-groups'] })
  } catch (err) {
    toastError(getErrorMessage(err) || '审批失败')
  }
}

async function handleReject(reqId: number) {
  try {
    await groupsApi.rejectJoin(reqId)
    toastSuccess('已拒绝加入')
    queryClient.invalidateQueries({ queryKey: ['my-groups'] })
  } catch (err) {
    toastError(getErrorMessage(err) || '审批失败')
  }
}

// 格式化时间
function formatTime(iso: string) {
  return new Date(iso).toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<template>
  <div class="space-y-5">
    <div>
      <h1 class="text-2xl font-medium text-black">
        我的小组
      </h1>
      <p class="text-[#737373] mt-1">
        小组按课程划分，可在不同科目加入不同小组
      </p>
    </div>

    <!-- 课程选择 -->
    <div class="w-full sm:w-56">
      <Select
        v-model="selectedCourseId"
        :options="courseOptions"
        placeholder="选择课程"
      />
    </div>

    <DataContainer
      :loading="loadingMyGroups"
      :has-data="true"
    >
      <!-- 已有小组 -->
      <Card
        v-if="currentGroup"
        class="bg-white border-[#e5e5e5] p-5"
      >
        <div class="flex items-start justify-between">
          <div>
            <h2 class="text-xl font-medium text-black">
              {{ currentGroup.name }}
            </h2>
            <p class="text-sm text-[#737373] mt-0.5">
              {{ currentGroup.course_name || '未分科' }} · {{ currentGroup.class_name }} · 小组分 {{ currentGroup.score }}
            </p>
          </div>
          <Badge v-if="currentGroup.is_leader" variant="info">
            <Crown class="h-3 w-3 mr-1" />
            组长
          </Badge>
          <Badge v-else variant="secondary">
            组员
          </Badge>
        </div>

        <div class="mt-5">
          <h3 class="text-sm font-medium text-black mb-2">
            小组成员
          </h3>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="m in currentGroup.members"
              :key="m.student_id"
              class="inline-flex items-center rounded-full bg-[#f5f5f5] px-3 py-1 text-xs text-black"
            >
              <Users class="h-3 w-3 mr-1 text-[#737373]" />
              {{ m.name || m.student_id }}
              <span v-if="m.student_id === currentGroup.leader_student_id" class="ml-1 text-[#6366f1]">(组长)</span>
            </span>
          </div>
        </div>

        <!-- 待处理申请 -->
        <div v-if="currentGroup.is_leader && (currentGroup.pending_requests || []).length > 0" class="mt-5 pt-5 border-t border-[#e5e5e5]">
          <h3 class="text-sm font-medium text-black mb-2">
            待处理入组申请
          </h3>
          <div class="space-y-2">
            <div
              v-for="req in currentGroup.pending_requests"
              :key="req.id"
              class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 rounded-xl border border-[#e5e5e5] bg-[#fafafa] p-3"
            >
              <div class="text-sm">
                <span class="text-black font-medium">{{ req.student_id }}</span>
                <span class="text-[#a3a3a3] text-xs ml-2">{{ formatTime(req.created_at) }}</span>
              </div>
              <div class="flex gap-2">
                <Button size="sm" variant="outline" @click="handleReject(req.id)">
                  拒绝
                </Button>
                <Button size="sm" variant="cta" @click="handleApprove(req.id)">
                  同意
                </Button>
              </div>
            </div>
          </div>
        </div>

        <div class="mt-5 pt-5 border-t border-[#e5e5e5] flex justify-end gap-2">
          <Button
            v-if="!currentGroup.is_leader"
            variant="outline"
            :loading="leaving"
            @click="leaveGroup()"
          >
            <LogOut class="h-4 w-4 mr-1" />
            退出小组
          </Button>
          <Button
            v-if="currentGroup.is_leader"
            variant="destructive"
            @click="showDissolveDialog = true"
          >
            <Trash2 class="h-4 w-4 mr-1" />
            申请解散
          </Button>
        </div>
      </Card>

      <!-- 没有小组 -->
      <Card
        v-else
        class="bg-white border-[#e5e5e5] p-5"
      >
        <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
          <p class="text-sm text-[#737373]">
            尚未加入该课程的小组
          </p>
          <Button variant="cta" @click="openCreateDialog">
            <Plus class="h-4 w-4 mr-1" />
            创建小组
          </Button>
        </div>

        <DataContainer
          :loading="loadingGroups"
          :has-data="(availableGroups || []).length > 0"
          empty-text="该课程暂无可加入的小组"
        >
          <div class="grid gap-3 sm:grid-cols-2">
            <div
              v-for="g in availableGroups"
              :key="g.id"
              class="rounded-xl border border-[#e5e5e5] bg-white p-4"
            >
              <div class="flex items-start justify-between">
                <div>
                  <h4 class="font-medium text-black">
                    {{ g.name }}
                  </h4>
                  <p class="text-xs text-[#737373] mt-0.5">
                    {{ g.member_count }}{{ g.max_members ? ` / ${g.max_members}` : '' }} 人 · 组长 {{ g.leader_name || g.leader_student_id }}
                  </p>
                </div>
                <Button
                  size="sm"
                  :disabled="g.is_full"
                  :loading="joining"
                  @click="handleJoin(g.id)"
                >
                  <LogIn class="h-3.5 w-3.5 mr-1" />
                  {{ g.is_full ? '已满' : '申请加入' }}
                </Button>
              </div>
            </div>
          </div>
        </DataContainer>
      </Card>
    </DataContainer>

    <!-- 创建小组弹窗 -->
    <Dialog v-model:open="showCreateDialog" title="创建小组">
      <div class="space-y-3">
        <div class="text-sm text-[#737373]">
          班级：{{ className }}
        </div>
        <div class="space-y-1">
          <Label>课程</Label>
          <Select
            v-model="createCourseId"
            :options="courseOptions"
            data-testid="create-group-course-select"
          />
        </div>
        <input
          v-model="createForm.name"
          placeholder="小组名称"
          class="w-full rounded-full border border-[#e5e5e5] bg-white px-3 py-2 text-sm text-black placeholder:text-[#a3a3a3] focus:outline-none focus:ring-2 focus:ring-[#3b82f6]/50"
        >
      </div>
      <template #footer>
        <div class="flex w-full gap-2 sm:justify-end">
          <Button variant="outline" @click="showCreateDialog = false">取消</Button>
          <Button variant="cta" :loading="creating" @click="handleCreate">确认创建</Button>
        </div>
      </template>
    </Dialog>

    <!-- 解散申请弹窗 -->
    <Dialog v-model:open="showDissolveDialog" title="申请解散小组">
      <div class="space-y-3">
        <textarea
          v-model="dissolveReason"
          placeholder="请填写解散原因"
          rows="3"
          class="w-full rounded-xl border border-[#e5e5e5] bg-white px-3 py-2 text-sm text-black placeholder:text-[#a3a3a3] focus:outline-none focus:ring-2 focus:ring-[#3b82f6]/50"
        />
      </div>
      <template #footer>
        <div class="flex w-full gap-2 sm:justify-end">
          <Button variant="outline" @click="showDissolveDialog = false">取消</Button>
          <Button variant="destructive" :loading="dissolving" @click="handleDissolve">提交申请</Button>
        </div>
      </template>
    </Dialog>
  </div>
</template>
