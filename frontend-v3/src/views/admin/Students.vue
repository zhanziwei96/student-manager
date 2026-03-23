<script setup lang="ts">
import { ref, computed } from 'vue'
import { useStudents, useUpdateScore } from '@/composables'
import { Card, Button, Badge, Dialog, Input, Label } from '@/components/ui'
import { Search, Plus, Minus, Loader2 } from 'lucide-vue-next'
import { Toast } from '@/components/ui'
import type { Student } from '@/types'

const { data: students, isPending, error } = useStudents()
const updateScoreMutation = useUpdateScore()

const searchQuery = ref('')
const selectedStudent = ref<Student | null>(null)
const showScoreDialog = ref(false)
const scoreChange = ref(0)
const scoreReason = ref('')

const showToast = ref(false)
const toastMessage = ref('')
const toastVariant = ref<'default' | 'success' | 'error'>('default')

const filteredStudents = computed(() => {
  if (!students.value) return []
  if (!searchQuery.value) return students.value
  
  const query = searchQuery.value.toLowerCase()
  return students.value.filter(
    (s) =>
      s.name.toLowerCase().includes(query) ||
      s.student_id.toLowerCase().includes(query) ||
      s.class_name.toLowerCase().includes(query)
  )
})

const openScoreDialog = (student: Student, isAdd: boolean) => {
  selectedStudent.value = student
  scoreChange.value = isAdd ? 10 : -10
  scoreReason.value = ''
  showScoreDialog.value = true
}

const handleUpdateScore = async () => {
  if (!selectedStudent.value) return

  try {
    await updateScoreMutation.mutateAsync({
      id: selectedStudent.value.id,
      data: {
        score_change: scoreChange.value,
        reason: scoreReason.value,
      },
    })

    toastMessage.value = `Score updated for ${selectedStudent.value.name}`
    toastVariant.value = 'success'
    showToast.value = true
    showScoreDialog.value = false
  } catch (err: any) {
    toastMessage.value = err.message || 'Failed to update score'
    toastVariant.value = 'error'
    showToast.value = true
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold text-white">Students</h1>
        <p class="text-white/60">Manage student records and scores</p>
      </div>
      <Button>
        <Plus class="mr-2 h-4 w-4" />
        Add Student
      </Button>
    </div>

    <!-- Search -->
    <div class="relative">
      <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/50" />
      <Input
        v-model="searchQuery"
        placeholder="Search by name, ID, or class..."
        class="pl-10"
      />
    </div>

    <!-- Loading state -->
    <div v-if="isPending" class="flex h-64 items-center justify-center">
      <Loader2 class="h-8 w-8 animate-spin text-primary" />
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="rounded-lg border border-red-500/20 bg-red-500/10 p-4 text-red-400">
      Failed to load students: {{ error.message }}
    </div>

    <!-- Students table -->
    <Card v-else class="overflow-hidden border-white/10">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-white/10 bg-white/[0.02]">
              <th class="px-4 py-3 text-left text-sm font-medium text-white/60">ID</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-white/60">Name</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-white/60">Class</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-white/60">Score</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-white/60">Status</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-white/60">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="student in filteredStudents"
              :key="student.id"
              class="border-b border-white/5 transition-colors hover:bg-white/[0.02]"
            >
              <td class="px-4 py-3 text-sm text-white/60">{{ student.student_id }}</td>
              <td class="px-4 py-3 text-sm font-medium text-white">{{ student.name }}</td>
              <td class="px-4 py-3 text-sm text-white/60">{{ student.class_name }}</td>
              <td class="px-4 py-3 text-sm font-bold text-primary">{{ student.score }}</td>
              <td class="px-4 py-3">
                <Badge :variant="student.status === 'active' ? 'success' : 'secondary'">
                  {{ student.status }}
                </Badge>
              </td>
              <td class="px-4 py-3">
                <div class="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    @click="openScoreDialog(student, true)"
                  >
                    <Plus class="h-3 w-3" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    @click="openScoreDialog(student, false)"
                  >
                    <Minus class="h-3 w-3" />
                  </Button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>

    <!-- Score Dialog -->
    <Dialog v-model:open="showScoreDialog" title="Update Score">
      <div class="space-y-4">
        <p v-if="selectedStudent" class="text-white/60">
          Update score for <span class="font-medium text-white">{{ selectedStudent.name }}</span>
        </p>
        <div class="space-y-2">
          <Label for="scoreChange">Score Change</Label>
          <Input
            id="scoreChange"
            v-model.number="scoreChange"
            type="number"
            placeholder="Enter points (positive or negative)"
          />
        </div>
        <div class="space-y-2">
          <Label for="reason">Reason</Label>
          <Input
            id="reason"
            v-model="scoreReason"
            placeholder="Enter reason for score change"
          />
        </div>
      </div>
      <template #footer>
        <Button variant="outline" @click="showScoreDialog = false">Cancel</Button>
        <Button
          :disabled="updateScoreMutation.isPending.value"
          @click="handleUpdateScore"
        >
          <Loader2 v-if="updateScoreMutation.isPending.value" class="mr-2 h-4 w-4 animate-spin" />
          Update Score
        </Button>
      </template>
    </Dialog>

    <!-- Toast -->
    <Toast v-model:show="showToast" :message="toastMessage" :variant="toastVariant" />
  </div>
</template>
