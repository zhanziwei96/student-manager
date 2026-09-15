<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores'
import { useStudentProfile } from '@/composables/useStudentProfile'
import { useStudentCourseSession } from '@/composables/useStudentCheckin'
import { usePullToRefresh } from '@/composables/usePullToRefresh'
import { enrollmentsApi } from '@/api/enrollments'
import { groupsApi } from '@/api/groups'
import { Card, Button, PullToRefreshIndicator } from '@/components/ui'
import { Users, Award, TrendingUp, Loader2, AlertCircle, Trophy, BookOpen, CalendarCheck } from 'lucide-vue-next'

const authStore = useAuthStore()
const router = useRouter()
const { data: currentStudent, isPending, error, refetch: refetchProfile } = useStudentProfile()

const studentId = computed(() => currentStudent.value?.student_id || '')

// 当前学期课程成绩（与"我的成绩"页同源，Dashboard 只展示摘要）
const { data: enrollmentsData, isPending: coursesLoading, refetch: refetchEnrollments } = useQuery({
  queryKey: ['my-enrollments', studentId],
  queryFn: () => enrollmentsApi.getMyEnrollments(studentId.value),
  enabled: () => !!studentId.value,
})
const courses = computed(() => enrollmentsData.value ?? [])

// 每科小组累计分
const { data: myGroupsData, refetch: refetchMyGroups } = useQuery({
  queryKey: ['my-groups', studentId],
  queryFn: () => groupsApi.getMyGroups(),
  enabled: () => !!studentId.value,
})
const myGroups = computed(() => myGroupsData.value ?? [])

// 签到主任务：查询班级活跃课堂（class_id 为空时 enabled=false，不发请求）
const classId = computed(() => currentStudent.value?.class_id ?? undefined)
const { data: classSession, hasActiveSession, refetch: refetchSession } = useStudentCourseSession(classId)

// 下拉刷新（移动端手势）：await 全部查询完成后 refreshing 复位
const pageRef = ref<HTMLElement | null>(null)
const { pulling, pullDistance, refreshing } = usePullToRefresh(pageRef, async () => {
  await Promise.all([refetchProfile(), refetchEnrollments(), refetchMyGroups(), refetchSession()])
})

// 课堂开始时间格式化
const formatTime = (time?: string) => {
  if (!time) return ''
  try {
    return new Date(time).toLocaleString('zh-CN')
  } catch {
    return time
  }
}

const getCardTextMutedColor = () => 'text-[#737373]'
</script>

<template>
  <div ref="pageRef" class="overscroll-y-contain space-y-5 px-4">
    <PullToRefreshIndicator :pulling="pulling" :pull-distance="pullDistance" :refreshing="refreshing" />
    <!-- Header -->
    <div class="px-1">
      <h1 class="text-2xl font-medium text-black tracking-tight">
        学生仪表板
      </h1>
      <p class="text-[#525252] text-sm mt-1">
        欢迎回来，{{ authStore.user?.name }}
      </p>
    </div>

    <!-- Loading state -->
    <div
      v-if="isPending"
      class="flex h-64 items-center justify-center"
    >
      <Loader2 class="h-8 w-8 animate-spin text-primary" />
    </div>

    <!-- Error state -->
    <div
      v-else-if="error"
      class="rounded-xl border border-red-500/30 bg-red-500/15 p-4 text-red-400"
    >
      <div class="flex items-center gap-2">
        <AlertCircle class="h-5 w-5" />
        <span>加载数据失败: {{ error.message }}</span>
      </div>
    </div>

    <!-- No data state -->
    <div
      v-else-if="!currentStudent"
      class="rounded-xl border border-[#e5e5e5] bg-white p-8 text-center"
    >
      <p class="text-[#737373]">
        未找到您的学生信息
      </p>
    </div>

    <template v-else>
      <!-- 签到主卡片：最高频任务置顶（HIG 聚焦主任务） -->
      <Card class="border-[#e5e5e5] bg-white p-5">
        <!-- 有活跃课堂：课堂信息 + 大号签到按钮 -->
        <div v-if="hasActiveSession && classSession">
          <div class="flex items-center gap-3">
            <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <CalendarCheck class="h-5 w-5" />
            </div>
            <div class="min-w-0 flex-1">
              <h2 class="text-lg font-medium text-black">
                课堂进行中
              </h2>
              <p class="text-xs text-[#525252] mt-0.5 truncate">
                {{ classSession.class_name || '课堂' }} · {{ classSession.teacher_name || '教师' }}
                <template v-if="classSession.start_time">· 开始于 {{ formatTime(classSession.start_time) }}</template>
              </p>
            </div>
          </div>
          <Button
            variant="cta"
            class="mt-4 h-14 w-full text-base"
            @click="router.push('/student/checkin')"
          >
            立即签到
          </Button>
        </div>

        <!-- 无活跃课堂 / 未分班：安静状态，无操作按钮 -->
        <div v-else class="flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-[#f5f5f5] text-[#525252]">
            <CalendarCheck class="h-5 w-5" />
          </div>
          <p class="text-sm text-[#737373]">
            当前没有进行中的课堂
          </p>
        </div>
      </Card>

      <!-- Stats grid -->
      <div class="grid grid-cols-2 gap-3 sm:gap-4">
        <!-- 班级卡片 -->
        <Card class="group relative overflow-hidden p-4 bg-white border-[#e5e5e5]">
          <div class="relative z-10">
            <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <Users class="h-5 w-5" />
            </div>
            <p class="mt-3 text-xs font-medium" :class="getCardTextMutedColor()">
              班级
            </p>
            <p class="text-sm font-medium text-black mt-0.5 truncate">
              {{ currentStudent.class_name }}
            </p>
          </div>
        </Card>

        <!-- 学号卡片 -->
        <Card class="group relative overflow-hidden p-4 bg-white border-[#e5e5e5]">
          <div class="relative z-10">
            <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <Award class="h-5 w-5" />
            </div>
            <p class="mt-3 text-xs font-medium" :class="getCardTextMutedColor()">
              学号
            </p>
            <p class="text-sm font-medium text-black mt-0.5 font-mono tracking-wide">
              {{ currentStudent.student_id }}
            </p>
          </div>
        </Card>

        <!-- 状态卡片 - 跨两列 -->
        <Card class="group col-span-2 relative overflow-hidden p-4 bg-white border-[#e5e5e5]">
          <div class="relative z-10 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <TrendingUp class="h-5 w-5" />
              </div>
              <div>
                <p class="text-xs font-medium" :class="getCardTextMutedColor()">
                  账户状态
                </p>
                <p class="text-sm font-medium text-black mt-0.5">
                  {{ currentStudent.is_account_enabled ? '账户启用' : '账户禁用' }}
                </p>
              </div>
            </div>
            <div
              class="h-2.5 w-2.5 rounded-full transition-all"
              :class="currentStudent.is_account_enabled ? 'bg-green-400' : 'bg-gray-400'"
            />
          </div>
        </Card>
      </div>

      <!-- 我的课程 -->
      <Card class="border-[#e5e5e5] bg-white p-5">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-lg font-medium text-black">
              我的课程
            </h2>
            <p class="text-xs text-[#525252] mt-0.5">
              当前学期各科成绩概览
            </p>
          </div>
          <button
            class="inline-flex min-h-[44px] items-center gap-1.5 rounded-full bg-[#f5f5f5] px-3 py-1.5 text-xs font-medium text-black transition-colors hover:bg-[#e5e5e5]"
            @click="router.push('/student/grades')"
          >
            <BookOpen class="h-3.5 w-3.5" />
            查看全部成绩
          </button>
        </div>

        <div
          v-if="coursesLoading"
          class="mt-6 flex h-24 items-center justify-center"
        >
          <Loader2 class="h-6 w-6 animate-spin text-primary" />
        </div>

        <div
          v-else-if="courses.length > 0"
          class="mt-5 space-y-2.5"
        >
          <div
            v-for="course in courses"
            :key="course.enrollment_id"
            class="flex items-center justify-between rounded-xl border border-[#e5e5e5] bg-[#fafafa] p-4"
          >
            <div class="flex items-center gap-3">
              <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <BookOpen class="h-4 w-4" />
              </div>
              <div class="text-left">
                <p class="text-sm font-medium text-black">
                  {{ course.course_name }}
                </p>
                <p class="text-xs text-[#525252] mt-0.5">
                  {{ course.teacher_name }}
                </p>
              </div>
            </div>
            <div class="flex items-center gap-4 text-sm">
              <span class="text-[#737373]">平时 <span class="font-medium text-black tabular-nums">{{ course.score }}</span></span>
              <span class="text-[#737373]">期末 <span class="font-medium text-black tabular-nums">{{ course.final_score ?? '—' }}</span></span>
            </div>
          </div>
        </div>

        <div
          v-else
          class="mt-6 flex flex-col items-center justify-center py-4 text-[#525252]"
        >
          <div class="h-12 w-12 rounded-full bg-[#f5f5f5] flex items-center justify-center mb-3">
            <BookOpen class="h-5 w-5 opacity-50" />
          </div>
          <p class="text-sm">
            暂无选课成绩
          </p>
        </div>
      </Card>

      <!-- 我的小组 -->
      <Card class="border-[#e5e5e5] bg-white p-5">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-lg font-medium text-black">
              我的小组
            </h2>
            <p class="text-xs text-[#525252] mt-0.5">
              各科小组累计分
            </p>
          </div>
          <button
            class="inline-flex min-h-[44px] items-center gap-1.5 rounded-full bg-[#f5f5f5] px-3 py-1.5 text-xs font-medium text-black transition-colors hover:bg-[#e5e5e5]"
            @click="router.push('/student/my-group')"
          >
            <Users class="h-3.5 w-3.5" />
            我的小组
          </button>
        </div>

        <div
          v-if="myGroups.length > 0"
          class="mt-5 space-y-2.5"
        >
          <div
            v-for="group in myGroups"
            :key="group.id"
            class="flex items-center justify-between rounded-xl border border-[#e5e5e5] bg-[#fafafa] p-4"
          >
            <div>
              <p class="text-sm font-medium text-black">
                {{ group.name }}
              </p>
              <p class="text-xs text-[#525252] mt-0.5">
                {{ group.course_name || '未分科' }}
              </p>
            </div>
            <span class="text-lg font-medium text-black tabular-nums">{{ group.score }}</span>
          </div>
        </div>

        <div
          v-else
          class="mt-6 flex flex-col items-center justify-center py-4 text-[#525252]"
        >
          <div class="h-12 w-12 rounded-full bg-[#f5f5f5] flex items-center justify-center mb-3">
            <Users class="h-5 w-5 opacity-50" />
          </div>
          <p class="text-sm">
            尚未加入任何小组
          </p>
        </div>
      </Card>

      <!-- 快捷入口 -->
      <div class="flex gap-3">
        <button
          class="flex-1 inline-flex min-h-[44px] items-center justify-center gap-1.5 rounded-full bg-[#f5f5f5] px-4 py-2.5 text-sm font-medium text-black transition-colors hover:bg-[#e5e5e5]"
          @click="router.push('/student/rankings')"
        >
          <Trophy class="h-4 w-4" />
          查看排行榜
        </button>
      </div>
    </template>
  </div>
</template>
