<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores'
import { useLeaderboard } from '@/composables/useLeaderboard'
import { Card, Badge, Button } from '@/components/ui'
import { Trophy, Users, School, Loader2, User } from 'lucide-vue-next'

const authStore = useAuthStore()
const currentStudentId = computed(() => authStore.user?.id)

const activeTab = ref<'class' | 'school'>('class')

const { isPending, students, myRank } = useLeaderboard(
  computed(() => ({ scope: activeTab.value, limit: 50 }))
)

// 前三名样式 - 金银铜奖杯（高对比度配色）
const getRankStyle = (rank: number) => {
  switch (rank) {
    case 1: return { icon: Trophy, color: 'text-yellow-600', bg: 'bg-yellow-300', ring: 'ring-yellow-200', shadow: 'shadow-yellow-400/50' }  // 🥇 金牌
    case 2: return { icon: Trophy, color: 'text-gray-700', bg: 'bg-gray-200', ring: 'ring-gray-100', shadow: 'shadow-gray-400/40' }    // 🥈 银牌
    case 3: return { icon: Trophy, color: 'text-amber-700', bg: 'bg-amber-400', ring: 'ring-amber-300', shadow: 'shadow-amber-500/40' } // 🥉 铜牌
    default: return { icon: null, color: 'text-white/60', bg: 'bg-white/10', ring: 'ring-white/10', shadow: '' }
  }
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
      <h1 class="text-2xl font-bold text-white">
        {{ activeTab === 'class' ? '班级排行榜' : '全校排行榜' }}
      </h1>
      <p class="text-white/60">
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

    <!-- My Rank Card - 渐变主题 -->
    <Card
      v-if="myRank"
      class="relative overflow-hidden border-primary/30 bg-gradient-to-br from-primary/25 via-primary/15 to-accent-cyan/20 p-4 shadow-xl shadow-primary/10 mb-5"
    >
      <div class="relative z-10 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-full bg-primary/20">
            <User class="h-5 w-5 text-primary" />
          </div>
          <div>
            <p class="text-sm text-white/60">我的排名</p>
            <p class="text-lg font-bold text-white">
              第 {{ myRank.rank }} 名
            </p>
          </div>
        </div>
        <div class="text-right">
          <p class="text-2xl font-bold text-primary">
            {{ myRank.score }}
          </p>
          <p class="text-sm text-white/40">分</p>
        </div>
      </div>
      <!-- 动态背景装饰 -->
      <div class="absolute -right-6 -top-6 h-32 w-32 rounded-full bg-primary/30 blur-3xl" />
      <div class="absolute -bottom-8 -left-4 h-28 w-28 rounded-full bg-accent-cyan/20 blur-3xl" />
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
        <div
          v-for="student in students"
          :key="`${activeTab}-${student.student_id}`"
          class="group rounded-xl border border-white/5 bg-white/[0.03] p-4 transition-all duration-200 hover:bg-white/[0.06] hover:border-white/10"
          :class="[
            isCurrentStudent(student.student_id) ? 'border-primary/30 bg-primary/5 hover:bg-primary/10' : ''
          ]"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <!-- Rank -->
              <div
                v-if="getRankStyle(student.rank).icon"
                :class="['flex h-10 w-10 items-center justify-center rounded-full ring-2 flex-shrink-0', getRankStyle(student.rank).bg, getRankStyle(student.rank).ring, getRankStyle(student.rank).shadow]"
              >
                <component
                  :is="getRankStyle(student.rank).icon"
                  class="h-5 w-5"
                  :class="getRankStyle(student.rank).color"
                />
              </div>
              <div
                v-else
                class="flex h-10 w-10 items-center justify-center text-base font-medium text-white/60 flex-shrink-0"
              >
                {{ student.rank }}
              </div>

              <!-- Info -->
              <div>
                <div class="flex items-center gap-2">
                  <span class="font-medium text-white">{{ maskName(student.name, student.student_id) }}</span>
                  <Badge
                    v-if="isCurrentStudent(student.student_id)"
                    variant="primary"
                    class="text-xs"
                  >
                    我
                  </Badge>
                </div>
                <p v-if="activeTab === 'school'" class="text-sm text-white/50">
                  {{ student.class_name }}
                </p>
              </div>
            </div>

            <!-- Score -->
            <span class="text-xl font-bold text-primary">
              {{ student.score }}
            </span>
          </div>
        </div>

        <!-- Empty State -->
        <div
          v-if="students.length === 0"
          class="py-12 text-center text-white/40"
        >
          暂无数据
        </div>
      </div>

      <!-- Desktop: Table -->
      <Card class="hidden lg:block border-white/10 bg-white/[0.02] overflow-hidden">
        <table class="w-full">
          <thead>
            <tr class="border-b border-white/10">
              <th class="px-4 py-3 text-left text-sm font-medium text-white/60">排名</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-white/60">姓名</th>
              <th
                v-if="activeTab === 'school'"
                class="px-4 py-3 text-left text-sm font-medium text-white/60"
              >
                班级
              </th>
              <th class="px-4 py-3 text-right text-sm font-medium text-white/60">分数</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="student in students"
              :key="`${activeTab}-${student.student_id}`"
              :class="[
                'border-b border-white/5 last:border-0',
                isCurrentStudent(student.student_id) ? 'bg-primary/10' : 'hover:bg-white/[0.02]'
              ]"
            >
              <td class="px-4 py-3">
                <div class="flex items-center gap-2">
                  <div
                    v-if="getRankStyle(student.rank).icon"
                    :class="['flex h-8 w-8 items-center justify-center rounded-full ring-2', getRankStyle(student.rank).bg, getRankStyle(student.rank).ring, getRankStyle(student.rank).shadow]"
                  >
                    <component
                      :is="getRankStyle(student.rank).icon"
                      class="h-5 w-5"
                      :class="getRankStyle(student.rank).color"
                    />
                  </div>
                  <span
                    v-else
                    class="flex h-8 w-8 items-center justify-center text-sm text-white/60"
                  >
                    {{ student.rank }}
                  </span>
                </div>
              </td>
              <td class="px-4 py-3">
                <div class="flex items-center gap-2">
                  <span class="font-medium text-white">{{ maskName(student.name, student.student_id) }}</span>
                  <Badge
                    v-if="isCurrentStudent(student.student_id)"
                    variant="primary"
                    class="text-xs"
                  >
                    我
                  </Badge>
                </div>
              </td>
              <td
                v-if="activeTab === 'school'"
                class="px-4 py-3 text-white/60"
              >
                {{ student.class_name }}
              </td>
              <td class="px-4 py-3 text-right">
                <span class="text-lg font-bold text-primary">
                  {{ student.score }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- Empty State -->
        <div
          v-if="students.length === 0"
          class="py-12 text-center text-white/40"
        >
          暂无数据
        </div>
      </Card>
    </template>
  </div>
</template>
