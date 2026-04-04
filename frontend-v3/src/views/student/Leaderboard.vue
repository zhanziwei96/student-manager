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

// 前三名样式 - 金银铜奖杯（高对比度）
const getRankStyle = (rank: number) => {
  switch (rank) {
    case 1: return { icon: Trophy, color: 'text-yellow-200', bg: 'bg-gradient-to-br from-yellow-300 to-yellow-600', ring: 'ring-yellow-400', shadow: 'shadow-yellow-500/40' }  // 🥇 金牌
    case 2: return { icon: Trophy, color: 'text-blue-100', bg: 'bg-gradient-to-br from-slate-200 to-slate-500', ring: 'ring-slate-300', shadow: 'shadow-slate-400/30' }    // 🥈 银牌
    case 3: return { icon: Trophy, color: 'text-orange-200', bg: 'bg-gradient-to-br from-orange-500 to-red-600', ring: 'ring-orange-500', shadow: 'shadow-orange-500/30' } // 🥉 铜牌
    default: return { icon: null, color: 'text-white/60', bg: 'bg-white/10', ring: 'ring-white/10', shadow: '' }
  }
}

// 是否当前登录学生
const isCurrentStudent = (studentId: string) => {
  return studentId === String(currentStudentId.value)
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-white">
        {{ activeTab === 'class' ? '班级排行榜' : '全校排行榜' }}
      </h1>
      <p class="text-white/60">
        {{ activeTab === 'class' ? '查看同班级同学排名' : '查看全校所有学生排名' }}
      </p>
    </div>

    <!-- Tab Switch -->
    <div class="flex gap-2">
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

    <!-- My Rank Card -->
    <Card
      v-if="myRank"
      class="border-primary/30 bg-primary/5 p-4"
    >
      <div class="flex items-center justify-between">
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
          :class="[
            'bg-white/[0.02] rounded-lg p-4 border border-white/10',
            isCurrentStudent(student.student_id) ? 'border-primary/30 bg-primary/5' : ''
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
                  <span class="font-medium text-white">{{ student.name }}</span>
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
                  <span class="font-medium text-white">{{ student.name }}</span>
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
