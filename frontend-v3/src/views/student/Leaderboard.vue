<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores'
import { useLeaderboard } from '@/composables/useLeaderboard'
import { Card, Badge, Button } from '@/components/ui'
import { Trophy, Medal, Award, Users, School, Loader2, User } from 'lucide-vue-next'

const authStore = useAuthStore()
const currentStudentId = computed(() => authStore.user?.id)

const activeTab = ref<'class' | 'school'>('class')

const { isPending, students, myRank } = useLeaderboard(
  computed(() => ({ scope: activeTab.value, limit: 50 }))
)

// 前三名样式
const getRankStyle = (rank: number) => {
  switch (rank) {
    case 1: return { icon: Trophy, color: 'text-yellow-400', bg: 'bg-yellow-400/20' }
    case 2: return { icon: Medal, color: 'text-gray-300', bg: 'bg-gray-300/20' }
    case 3: return { icon: Award, color: 'text-amber-600', bg: 'bg-amber-600/20' }
    default: return { icon: null, color: 'text-white/60', bg: 'bg-white/10' }
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
        排行榜
      </h1>
      <p class="text-white/60">
        查看班级和全校排名
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

    <!-- Leaderboard Table -->
    <Card
      v-else
      class="border-white/10 bg-white/[0.02] overflow-hidden"
    >
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
            :key="student.student_id"
            :class="[
              'border-b border-white/5 last:border-0',
              isCurrentStudent(student.student_id) ? 'bg-primary/10' : 'hover:bg-white/[0.02]'
            ]"
          >
            <td class="px-4 py-3">
              <div class="flex items-center gap-2">
                <div
                  v-if="getRankStyle(student.rank).icon"
                  :class="['flex h-8 w-8 items-center justify-center rounded-full', getRankStyle(student.rank).bg]"
                >
                  <component
                    :is="getRankStyle(student.rank).icon"
                    class="h-4 w-4"
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
  </div>
</template>
