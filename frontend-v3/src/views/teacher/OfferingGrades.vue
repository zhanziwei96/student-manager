<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { useRoute, useRouter } from 'vue-router'
import { Card, Button, Input, Select, Dialog, Label } from '@/components/ui'
import { Loader2, ArrowLeft, Plus, FileText, Users } from 'lucide-vue-next'
import { offeringsApi } from '@/api/offerings'
import { enrollmentsApi } from '@/api/enrollments'
import { groupsApi } from '@/api/groups'
import { useToast } from '@/composables/useToast'
import { getErrorMessage } from '@/lib/error'
import type { EnrollmentRow } from '@/types'

const route = useRoute()
const router = useRouter()
const { showToast } = useToast()
const queryClient = useQueryClient()

const offeringId = computed(() => Number(route.params.id))

// 教学班信息（从我的教学班列表匹配）
const { data: mine } = useQuery({
  queryKey: ['teacher-offerings'],
  queryFn: () => offeringsApi.listMine(),
})
const offering = computed(() => (mine.value ?? []).find((o) => o.id === offeringId.value))

// 选课名单
const { data: rosterData, isPending } = useQuery({
  queryKey: ['offerings', 'enrollments', offeringId],
  queryFn: () => offeringsApi.listEnrollments(offeringId.value),
})
const roster = computed(() => rosterData.value ?? [])

const invalidateRoster = () => queryClient.invalidateQueries({ queryKey: ['offerings', 'enrollments', offeringId] })

// === 个人成绩加减分 ===
const showScoreDialog = ref(false)
const scoreStudent = ref<EnrollmentRow | null>(null)
const scoreChange = ref(0)
const scoreReason = ref('')
const scoreError = ref('')

const openScoreDialog = (row: EnrollmentRow) => {
  scoreStudent.value = row
  scoreChange.value = 0
  scoreReason.value = ''
  scoreError.value = ''
  showScoreDialog.value = true
}

const { mutateAsync: updateScore, isPending: isUpdatingScore } = useMutation({
  mutationFn: () => enrollmentsApi.updateScore(scoreStudent.value!.enrollment_id, {
    score_change: scoreChange.value,
    reason: scoreReason.value.trim(),
  }),
  onSuccess: () => {
    invalidateRoster()
    showToast('分数已更新', 'success')
    showScoreDialog.value = false
  },
  onError: (error) => showToast(getErrorMessage(error) || '更新失败', 'error'),
})

const handleUpdateScore = async () => {
  if (!scoreReason.value.trim()) {
    scoreError.value = '请输入分数变化原因'
    return
  }
  await updateScore()
}

// === 期末成绩（试卷个人分） ===
const showFinalDialog = ref(false)
const finalStudent = ref<EnrollmentRow | null>(null)
const finalScore = ref(0)

const openFinalDialog = (row: EnrollmentRow) => {
  finalStudent.value = row
  finalScore.value = row.final_score ?? 0
  showFinalDialog.value = true
}

const { mutateAsync: setFinal, isPending: isSettingFinal } = useMutation({
  mutationFn: () => enrollmentsApi.setFinalScore(finalStudent.value!.enrollment_id, {
    final_score: finalScore.value,
  }),
  onSuccess: () => {
    invalidateRoster()
    showToast('期末成绩已登记', 'success')
    showFinalDialog.value = false
  },
  onError: (error) => showToast(getErrorMessage(error) || '登记失败', 'error'),
})

// === 期末成绩（任务小组同分） ===
const showGroupFinalDialog = ref(false)
const groupFinalClass = ref('')
const groupFinalGroupId = ref<number | ''>('')
const groupFinalScore = ref(0)
const groupFinalError = ref('')

// 名单中的行政班（distinct）
const rosterClasses = computed(() => [...new Set(roster.value.map((r) => r.class_name))])

// 小组列表（按选中班级，enabled 时查询）
const { data: groupsData } = useQuery({
  queryKey: ['teacher-groups', groupFinalClass],
  queryFn: () => groupsApi.getGroups(groupFinalClass.value),
  enabled: () => showGroupFinalDialog.value && groupFinalClass.value !== '',
})

const openGroupFinalDialog = () => {
  groupFinalClass.value = rosterClasses.value[0] ?? ''
  groupFinalGroupId.value = ''
  groupFinalScore.value = 0
  groupFinalError.value = ''
  showGroupFinalDialog.value = true
}

const { mutateAsync: setGroupFinal, isPending: isSettingGroupFinal } = useMutation({
  mutationFn: () => enrollmentsApi.setGroupFinalScores(offeringId.value, {
    group_id: Number(groupFinalGroupId.value),
    final_score: groupFinalScore.value,
  }),
  onSuccess: (result) => {
    invalidateRoster()
    showToast(`期末成绩已登记（${result.affected} 人）`, 'success')
    showGroupFinalDialog.value = false
  },
  onError: (error) => showToast(getErrorMessage(error) || '登记失败', 'error'),
})

const handleSetGroupFinal = async () => {
  if (groupFinalGroupId.value === '') {
    groupFinalError.value = '请选择小组'
    return
  }
  await setGroupFinal()
}
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-5">
      <div>
        <Button
          variant="ghost"
          size="sm"
          class="-ml-2 mb-1"
          @click="router.push('/teacher/my-offerings')"
        >
          <ArrowLeft class="mr-1 h-4 w-4" />
          我的教学班
        </Button>
        <h1 class="text-2xl font-medium text-black">
          {{ offering?.course_name ?? '成绩录入' }}
        </h1>
        <p class="text-[#737373]">
          {{ offering?.class_scope }} · 共 {{ roster.length }} 名学生
        </p>
      </div>
      <Button
        variant="outline"
        @click="openGroupFinalDialog"
      >
        <Users class="mr-2 h-4 w-4" />
        期末任务同分
      </Button>
    </div>

    <!-- 名单表格 -->
    <Card class="overflow-hidden p-0">
      <div
        v-if="isPending"
        class="flex h-64 items-center justify-center"
      >
        <Loader2 class="h-8 w-8 animate-spin text-primary" />
      </div>

      <table
        v-else-if="roster.length > 0"
        class="w-full text-sm"
      >
        <thead class="bg-[#fafafa] text-[#737373] border-b border-[#e5e5e5]">
          <tr>
            <th class="px-4 py-3 text-left font-medium">
              学号
            </th>
            <th class="px-4 py-3 text-left font-medium">
              姓名
            </th>
            <th class="px-4 py-3 text-left font-medium">
              班级
            </th>
            <th class="px-4 py-3 text-right font-medium">
              平时成绩
            </th>
            <th class="px-4 py-3 text-right font-medium">
              期末成绩
            </th>
            <th class="px-4 py-3 text-right font-medium">
              操作
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-[#e5e5e5]">
          <tr
            v-for="row in roster"
            :key="row.enrollment_id"
            class="text-[#737373] hover:bg-[#fafafa] transition-colors"
          >
            <td class="px-4 py-3 font-mono text-xs">
              {{ row.student_id }}
            </td>
            <td class="px-4 py-3 font-medium text-black">
              {{ row.name }}
            </td>
            <td class="px-4 py-3">
              {{ row.class_name }}
            </td>
            <td class="px-4 py-3 text-right font-medium text-black">
              {{ row.score }}
            </td>
            <td class="px-4 py-3 text-right font-medium text-black">
              {{ row.final_score ?? '—' }}
            </td>
            <td class="px-4 py-3">
              <div class="flex justify-end gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  class="hover:bg-[#fafafa]"
                  @click="openScoreDialog(row)"
                >
                  <Plus class="mr-1 h-4 w-4" />
                  加减分
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  class="hover:bg-[#fafafa]"
                  @click="openFinalDialog(row)"
                >
                  <FileText class="mr-1 h-4 w-4" />
                  期末分
                </Button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Empty state -->
      <div
        v-else
        class="flex h-64 flex-col items-center justify-center text-[#737373]"
      >
        <p>暂无选课学生</p>
        <p class="mt-1 text-sm text-[#a3a3a3]">
          请联系管理员导入选课名单
        </p>
      </div>
    </Card>

    <!-- 加减分 Dialog -->
    <Dialog
      v-model:open="showScoreDialog"
      :title="scoreStudent ? `调整 ${scoreStudent.name} 的平时成绩` : '调整平时成绩'"
      description="分数变化会记录操作人与原因"
    >
      <div class="space-y-4">
        <div class="space-y-2">
          <Label>分数变化（正数加分，负数减分）</Label>
          <Input
            v-model.number="scoreChange"
            type="number"
            placeholder="如：5 或 -3"
          />
        </div>
        <div class="space-y-2">
          <Label>原因</Label>
          <Input
            v-model="scoreReason"
            placeholder="如：课堂表现优秀"
          />
        </div>
        <p
          v-if="scoreError"
          class="text-sm text-[#ef4444]"
        >
          {{ scoreError }}
        </p>
      </div>
      <template #footer>
        <Button
          variant="outline"
          @click="showScoreDialog = false"
        >
          取消
        </Button>
        <Button
          :disabled="isUpdatingScore"
          @click="handleUpdateScore"
        >
          <Loader2
            v-if="isUpdatingScore"
            class="mr-2 h-4 w-4 animate-spin"
          />
          保存
        </Button>
      </template>
    </Dialog>

    <!-- 期末分 Dialog -->
    <Dialog
      v-model:open="showFinalDialog"
      :title="finalStudent ? `登记 ${finalStudent.name} 的期末成绩` : '登记期末成绩'"
      description="试卷考试使用个人分数；任务考核请用「期末任务同分」"
    >
      <div class="space-y-4">
        <div class="space-y-2">
          <Label>期末成绩</Label>
          <Input
            v-model.number="finalScore"
            type="number"
            placeholder="如：88"
          />
        </div>
      </div>
      <template #footer>
        <Button
          variant="outline"
          @click="showFinalDialog = false"
        >
          取消
        </Button>
        <Button
          :disabled="isSettingFinal"
          @click="setFinal()"
        >
          <Loader2
            v-if="isSettingFinal"
            class="mr-2 h-4 w-4 animate-spin"
          />
          登记
        </Button>
      </template>
    </Dialog>

    <!-- 期末任务同分 Dialog -->
    <Dialog
      v-model:open="showGroupFinalDialog"
      title="期末任务同分"
      description="小组任务考核：组内成员获得相同期末成绩"
    >
      <div class="space-y-4">
        <div class="space-y-2">
          <Label>班级</Label>
          <Select
            v-model="groupFinalClass"
            :options="rosterClasses.map((c) => ({ value: c, label: c }))"
            placeholder="选择班级"
          />
        </div>
        <div class="space-y-2">
          <Label>小组</Label>
          <Select
            v-model="groupFinalGroupId"
            :options="(groupsData ?? []).map((g) => ({ value: g.id, label: g.name }))"
            placeholder="选择小组"
          />
        </div>
        <div class="space-y-2">
          <Label>期末成绩</Label>
          <Input
            v-model.number="groupFinalScore"
            type="number"
            placeholder="如：90"
          />
        </div>
        <p
          v-if="groupFinalError"
          class="text-sm text-[#ef4444]"
        >
          {{ groupFinalError }}
        </p>
      </div>
      <template #footer>
        <Button
          variant="outline"
          @click="showGroupFinalDialog = false"
        >
          取消
        </Button>
        <Button
          :disabled="isSettingGroupFinal"
          @click="handleSetGroupFinal"
        >
          <Loader2
            v-if="isSettingGroupFinal"
            class="mr-2 h-4 w-4 animate-spin"
          />
          登记
        </Button>
      </template>
    </Dialog>
  </div>
</template>
