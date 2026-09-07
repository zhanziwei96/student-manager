<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { useAuthStore } from '@/stores'
import { useLeaderboard } from '@/composables/useLeaderboard'
import { useSubjects } from '@/composables/useSubjects'
import { useTermInfo } from '@/composables/useTermInfo'
import { studentsApi } from '@/api/students'
import { Card, Badge, Button, Select } from '@/components/ui'
import { Trophy, Users, School, Loader2, User } from 'lucide-vue-next'

const authStore = useAuthStore()
const currentStudentId = computed(() => authStore.user?.id)

const activeTab = ref<'class' | 'school'>('class')

// === 科目筛选器（默认当前学期第一个科目） ===
const { data: subjectsData } = useSubjects()
const { data: termInfo } = useTermInfo()

// 当前学期科目列表（学期信息缺失或无匹配时回退为全部科目）
const semesterSubjects = computed(() => {
  const all = subjectsData.value ?? []
  const term = termInfo.value?.term
  if (!term) return all
  const filtered = all.filter((s) => s.semester === term)
  return filtered.length > 0 ? filtered : all
})

const selectedSubjectId = ref<string | number>('')
const hasDefaultedSubject = ref(false)

// 科目列表就绪后默认选中第一个科目（仅自动设置一次，不覆盖用户手动选择）
watch(
  semesterSubjects,
  (list) => {
    if (!hasDefaultedSubject.value && list.length > 0) {
      selectedSubjectId.value = list[0].id
      hasDefaultedSubject.value = true
    }
  },
  { immediate: true }
)

const subjectOptions = computed(() => [
  { value: '', label: '全部科目' },
  ...semesterSubjects.value.map((s) => ({ value: s.id, label: s.name })),
])

// === 教师筛选器（从本人科目分数记录中提取任课教师列表） ===
const studentId = computed(() => (currentStudentId.value ? String(currentStudentId.value) : ''))
const { data: subjectScores } = useQuery({
  queryKey: computed(() => ['student-subjects', studentId.value]),
  queryFn: () => studentsApi.getSubjects(studentId.value),
  enabled: computed(() => !!studentId.value),
})

const selectedTeacherId = ref<string | number>('')

// 选中具体科目时只显示该科目的任课教师，否则显示全部任课教师
const teacherOptions = computed(() => {
  const scores = subjectScores.value ?? []
  const filtered =
    selectedSubjectId.value === ''
      ? scores
      : scores.filter((s) => s.subject_id === Number(selectedSubjectId.value))
  const teacherMap = new Map<number, string>()
  filtered.forEach((s) => teacherMap.set(s.teacher_id, s.teacher_name))
  return [
    { value: '', label: '全部教师' },
    ...[...teacherMap.entries()].map(([value, label]) => ({ value, label })),
  ]
})

// 切换科目后，若已选教师不在新选项中则重置为全部教师
watch(teacherOptions, (options) => {
  if (
    selectedTeacherId.value !== '' &&
    !options.some((o) => String(o.value) === String(selectedTeacherId.value))
  ) {
    selectedTeacherId.value = ''
  }
})

const { isPending, students, myRank } = useLeaderboard(
  computed(() => ({
    scope: activeTab.value,
    limit: 50,
    ...(selectedSubjectId.value !== '' ? { subject_id: Number(selectedSubjectId.value) } : {}),
    ...(selectedTeacherId.value !== '' ? { teacher_id: Number(selectedTeacherId.value) } : {}),
  }))
)

// 前三名样式 - 金银铜奖杯（高对比度配色）
const getRankStyle = (rank: number) => {
  switch (rank) {
    case 1: return { icon: Trophy, color: 'text-yellow-600', bg: 'bg-yellow-300', ring: 'ring-yellow-200', shadow: 'shadow-yellow-400/50', cardBg: 'bg-yellow-500/10', cardBorder: 'border-yellow-400/30' }  // 🥇 金牌
    case 2: return { icon: Trophy, color: 'text-gray-700', bg: 'bg-gray-200', ring: 'ring-gray-100', shadow: 'shadow-gray-400/40', cardBg: 'bg-gray-400/10', cardBorder: 'border-gray-300/30' }    // 🥈 银牌
    case 3: return { icon: Trophy, color: 'text-amber-700', bg: 'bg-amber-400', ring: 'ring-amber-300', shadow: 'shadow-amber-500/40', cardBg: 'bg-amber-500/10', cardBorder: 'border-amber-400/30' } // 🥉 铜牌
    default: return { icon: null, color: 'text-[#737373]', bg: 'bg-[#f5f5f5]', ring: 'ring-[#e5e5e5]', shadow: '', cardBg: '', cardBorder: '' }
  }
}

// 获取卡片样式（前三名特殊主题色，当前用户高亮）
const getCardClass = (student: { student_id: string; rank: number }) => {
  const isMe = isCurrentStudent(student.student_id)
  const rankStyle = getRankStyle(student.rank)

  // 当前用户高亮优先
  if (isMe) {
    return 'border-primary/50 bg-primary/10 hover:bg-primary/15 hover:border-primary/60'
  }

  // 前三名特殊主题色
  if (student.rank <= 3 && rankStyle.cardBg) {
    return `${rankStyle.cardBg} ${rankStyle.cardBorder} hover:brightness-110`
  }

  return ''
}

// 是否当前登录学生
const isCurrentStudent = (studentId: string) => {
  return studentId === String(currentStudentId.value)
}

// 姓名脱敏：张三→张*三、李小明→李*明
const maskName = (name: string, studentId: string) => {
  // 自己显示完整姓名
  if (isCurrentStudent(studentId)) return name
  // 其他人脱敏显示：姓氏 + * + 最后一个字
  if (name.length <= 1) return name + '*'
  if (name.length === 2) return name[0] + '*' + name[1]
  return name[0] + '*' + name[name.length - 1]
}
</script>

<template>
  <div>
    <!-- Header -->
    <div class="mb-5">
      <h1 class="text-2xl font-medium text-black">
        {{ activeTab === 'class' ? '班级排行榜' : '全校排行榜' }}
      </h1>
      <p class="text-[#737373]">
        {{ activeTab === 'class' ? '查看同班级同学排名' : '查看全校所有学生排名' }}
      </p>
    </div>

    <!-- Tab Switch -->
    <div class="flex gap-2 mb-5">
      <Button
        :variant="activeTab === 'class' ? 'default' : 'outline'"
        @click="activeTab = 'class'"
      >
        <Users class="mr-2 h-4 w-4" />
        班级榜
      </Button>
      <Button
        :variant="activeTab === 'school' ? 'default' : 'outline'"
        @click="activeTab = 'school'"
      >
        <School class="mr-2 h-4 w-4" />
        全校榜
      </Button>
    </div>

    <!-- Filters: 科目 / 教师 -->
    <div class="flex flex-col sm:flex-row gap-3 mb-5">
      <div
        class="sm:w-48"
        data-testid="subject-filter"
      >
        <Select
          v-model="selectedSubjectId"
          :options="subjectOptions"
        />
      </div>
      <div
        class="sm:w-48"
        data-testid="teacher-filter"
      >
        <Select
          v-model="selectedTeacherId"
          :options="teacherOptions"
        />
      </div>
    </div>

    <!-- My Rank Card - Indigo 主题 -->
    <Card
      v-if="myRank"
      class="relative overflow-hidden p-4 mb-5"
      :class="'bg-white border-[#e5e5e5]'"
    >
      <div class="relative z-10 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div
            class="flex h-10 w-10 items-center justify-center rounded-full flex-shrink-0"
            :class="'bg-primary/10 text-primary'"
          >
            <User class="h-5 w-5" :style="{ color: 'black' }" />
          </div>
          <div>
            <p class="text-sm text-[#737373]">我的排名</p>
            <p class="text-lg font-medium text-black">
              第 {{ myRank.rank }} 名
            </p>
          </div>
        </div>
        <div class="text-right">
          <p class="text-2xl font-medium text-[black]">
            {{ myRank.score }}
          </p>
          <p class="text-sm text-[#a3a3a3]">分</p>
        </div>
      </div>
    </Card>

    <!-- Loading -->
    <div
      v-if="isPending"
      class="flex h-64 items-center justify-center"
    >
      <Loader2 class="h-8 w-8 animate-spin text-primary" />
    </div>

    <!-- Leaderboard - Mobile: Cards, Desktop: Table -->
    <template v-else>
      <!-- Mobile: Card List -->
      <div class="lg:hidden space-y-3">
        <Card
          v-for="student in students"
          :key="`${activeTab}-${student.student_id}`"
          class="group border transition-colors"
          :class="getCardClass(student)"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <!-- Rank -->
              <div
                v-if="getRankStyle(student.rank).icon"
                :class="['flex h-10 w-10 items-center justify-center rounded-full ring-2 flex-shrink-0', getRankStyle(student.rank).bg, getRankStyle(student.rank).ring]"
              >
                <component
                  :is="getRankStyle(student.rank).icon"
                  class="h-5 w-5"
                  :class="getRankStyle(student.rank).color"
                />
              </div>
              <div
                v-else
                class="flex h-10 w-10 items-center justify-center text-base font-medium text-[#737373] flex-shrink-0"
              >
                {{ student.rank }}
              </div>

              <!-- Info -->
              <div>
                <div class="flex items-center gap-2">
                  <span class="font-medium text-black">{{ maskName(student.name, student.student_id) }}</span>
                  <Badge
                    v-if="isCurrentStudent(student.student_id)"
                    variant="default"
                    class="text-xs"
                  >
                    我
                  </Badge>
                </div>
                <p v-if="activeTab === 'school'" class="text-sm text-[#a3a3a3]">
                  {{ student.class_name }}
                </p>
              </div>
            </div>

            <!-- Score -->
            <span class="text-xl font-medium text-primary">
              {{ student.score }}
            </span>
          </div>
        </Card>

        <!-- Empty State -->
        <div
          v-if="students.length === 0"
          class="py-12 text-center text-[#a3a3a3]"
        >
          暂无数据
        </div>
      </div>

      <!-- Desktop: Table -->
      <Card class="hidden lg:block overflow-hidden">
        <table class="w-full">
          <thead>
            <tr class="border-b border-[#e5e5e5]">
              <th class="px-4 py-3 text-left text-sm font-medium text-[#737373]">排名</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-[#737373]">姓名</th>
              <th
                v-if="activeTab === 'school'"
                class="px-4 py-3 text-left text-sm font-medium text-[#737373]"
              >
                班级
              </th>
              <th class="px-4 py-3 text-right text-sm font-medium text-[#737373]">分数</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="student in students"
              :key="`${activeTab}-${student.student_id}`"
              :class="[
                'border-b border-[#e5e5e5] last:border-0 transition-colors',
                isCurrentStudent(student.student_id)
                  ? 'bg-primary/15 border-primary/30'
                  : student.rank === 1
                    ? 'bg-yellow-500/5 hover:bg-yellow-500/10'
                    : student.rank === 2
                      ? 'bg-gray-400/5 hover:bg-gray-400/10'
                      : student.rank === 3
                        ? 'bg-amber-500/5 hover:bg-amber-500/10'
                        : 'hover:bg-[#fafafa]'
              ]"
            >
              <td class="px-4 py-3">
                <div class="flex items-center gap-2">
                  <div
                    v-if="getRankStyle(student.rank).icon"
                    :class="['flex h-8 w-8 items-center justify-center rounded-full ring-2', getRankStyle(student.rank).bg, getRankStyle(student.rank).ring]"
                  >
                    <component
                      :is="getRankStyle(student.rank).icon"
                      class="h-5 w-5"
                      :class="getRankStyle(student.rank).color"
                    />
                  </div>
                  <span
                    v-else
                    class="flex h-8 w-8 items-center justify-center text-sm text-[#737373]"
                  >
                    {{ student.rank }}
                  </span>
                </div>
              </td>
              <td class="px-4 py-3">
                <div class="flex items-center gap-2">
                  <span class="font-medium text-black">{{ maskName(student.name, student.student_id) }}</span>
                  <Badge
                    v-if="isCurrentStudent(student.student_id)"
                    variant="default"
                    class="text-xs"
                  >
                    我
                  </Badge>
                </div>
              </td>
              <td
                v-if="activeTab === 'school'"
                class="px-4 py-3 text-[#737373]"
              >
                {{ student.class_name }}
              </td>
              <td class="px-4 py-3 text-right">
                <span class="text-lg font-medium text-primary">
                  {{ student.score }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- Empty State -->
        <div
          v-if="students.length === 0"
          class="py-12 text-center text-[#a3a3a3]"
        >
          暂无数据
        </div>
      </Card>
    </template>
  </div>
</template>
