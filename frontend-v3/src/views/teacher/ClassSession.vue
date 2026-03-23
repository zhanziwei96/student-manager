<script setup lang="ts">
import { ref, computed } from 'vue'
import { useClassSession, useStartClassSession, useEndClassSession, useCheckIn } from '@/composables'
import { Card, Button, Input, Badge } from '@/components/ui'
import { Play, Square, CheckCircle, Clock, Users, Loader2 } from 'lucide-vue-next'
import { Toast } from '@/components/ui'

const className = ref('')
const studentCode = ref('')

const { data: activeSession } = useClassSession()
const startSessionMutation = useStartClassSession()
const endSessionMutation = useEndClassSession()
const checkInMutation = useCheckIn()

const showToast = ref(false)
const toastMessage = ref('')
const toastVariant = ref<'default' | 'success' | 'error'>('default')

const isSessionActive = computed(() => !!activeSession.value)

const handleStartSession = async () => {
  if (!className.value.trim()) {
    toastMessage.value = 'Please enter a class name'
    toastVariant.value = 'error'
    showToast.value = true
    return
  }

  try {
    await startSessionMutation.mutateAsync(className.value)
    toastMessage.value = 'Class session started!'
    toastVariant.value = 'success'
    showToast.value = true
  } catch (err: any) {
    toastMessage.value = err.message || 'Failed to start session'
    toastVariant.value = 'error'
    showToast.value = true
  }
}

const handleEndSession = async () => {
  try {
    await endSessionMutation.mutateAsync()
    toastMessage.value = 'Class session ended!'
    toastVariant.value = 'success'
    showToast.value = true
    className.value = ''
  } catch (err: any) {
    toastMessage.value = err.message || 'Failed to end session'
    toastVariant.value = 'error'
    showToast.value = true
  }
}

const handleCheckIn = async () => {
  if (!studentCode.value.trim()) {
    toastMessage.value = 'Please enter student code'
    toastVariant.value = 'error'
    showToast.value = true
    return
  }

  try {
    await checkInMutation.mutateAsync({
      student_code: studentCode.value,
      session_id: activeSession.value?.id || '',
    })
    toastMessage.value = 'Student checked in successfully!'
    toastVariant.value = 'success'
    showToast.value = true
    studentCode.value = ''
  } catch (err: any) {
    toastMessage.value = err.message || 'Check-in failed'
    toastVariant.value = 'error'
    showToast.value = true
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-white">Class Session</h1>
      <p class="text-white/60">Manage your active class sessions</p>
    </div>

    <!-- Session status -->
    <Card
      class="border-white/10 p-6"
      :class="isSessionActive ? 'bg-green-500/5 border-green-500/20' : 'bg-white/[0.02]'"
    >
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-4">
          <div
            class="flex h-12 w-12 items-center justify-center rounded-full"
            :class="isSessionActive ? 'bg-green-500/20 text-green-400' : 'bg-white/10 text-white/60'"
          >
            <Clock class="h-6 w-6" />
          </div>
          <div>
            <h2 class="font-medium text-white">
              {{ isSessionActive ? 'Session Active' : 'No Active Session' }}
            </h2>
            <p v-if="activeSession" class="text-sm text-white/60">
              {{ activeSession.class_name }} • Started {{ activeSession.start_time }}
            </p>
            <p v-else class="text-sm text-white/60">Start a new session to begin</p>
          </div>
        </div>
        <div>
          <Button
            v-if="!isSessionActive"
            :disabled="startSessionMutation.isPending.value"
            @click="handleStartSession"
          >
            <Loader2 v-if="startSessionMutation.isPending.value" class="mr-2 h-4 w-4 animate-spin" />
            <Play v-else class="mr-2 h-4 w-4" />
            Start Session
          </Button>
          <Button
            v-else
            variant="destructive"
            :disabled="endSessionMutation.isPending.value"
            @click="handleEndSession"
          >
            <Loader2 v-if="endSessionMutation.isPending.value" class="mr-2 h-4 w-4 animate-spin" />
            <Square v-else class="mr-2 h-4 w-4" />
            End Session
          </Button>
        </div>
      </div>
    </Card>

    <!-- Start session form -->
    <Card v-if="!isSessionActive" class="border-white/10 bg-white/[0.02] p-6">
      <h3 class="font-medium text-white">Start New Session</h3>
      <p class="text-sm text-white/60">Enter class details to begin</p>
      <div class="mt-4 flex gap-4">
        <Input
          v-model="className"
          placeholder="Enter class name (e.g., CS101)"
          class="flex-1"
          @keyup.enter="handleStartSession"
        />
        <Button :disabled="startSessionMutation.isPending.value" @click="handleStartSession">
          <Loader2 v-if="startSessionMutation.isPending.value" class="mr-2 h-4 w-4 animate-spin" />
          <Play v-else class="mr-2 h-4 w-4" />
          Start
        </Button>
      </div>
    </Card>

    <!-- Check-in form -->
    <Card v-if="isSessionActive" class="border-white/10 bg-white/[0.02] p-6">
      <div class="flex items-center gap-3">
        <div class="flex h-10 w-10 items-center justify-center rounded-full bg-primary/20">
          <CheckCircle class="h-5 w-5 text-primary" />
        </div>
        <div>
          <h3 class="font-medium text-white">Student Check-in</h3>
          <p class="text-sm text-white/60">Enter student code to check them in</p>
        </div>
      </div>
      <div class="mt-4 flex gap-4">
        <Input
          v-model="studentCode"
          placeholder="Enter student code"
          class="flex-1"
          @keyup.enter="handleCheckIn"
        />
        <Button :disabled="checkInMutation.isPending.value" @click="handleCheckIn">
          <Loader2 v-if="checkInMutation.isPending.value" class="mr-2 h-4 w-4 animate-spin" />
          <CheckCircle v-else class="mr-2 h-4 w-4" />
          Check In
        </Button>
      </div>
    </Card>

    <!-- Session stats -->
    <div v-if="isSessionActive" class="grid gap-6 sm:grid-cols-2">
      <Card class="border-white/10 bg-white/[0.02] p-6">
        <div class="flex items-center gap-3">
          <Users class="h-5 w-5 text-white/60" />
          <div>
            <p class="text-sm text-white/60">Checked In</p>
            <p class="text-2xl font-bold text-white">{{ activeSession?.checked_in_count || 0 }}</p>
          </div>
        </div>
      </Card>
      <Card class="border-white/10 bg-white/[0.02] p-6">
        <div class="flex items-center gap-3">
          <Clock class="h-5 w-5 text-white/60" />
          <div>
            <p class="text-sm text-white/60">Duration</p>
            <p class="text-2xl font-bold text-white">45 min</p>
          </div>
        </div>
      </Card>
    </div>

    <!-- Toast -->
    <Toast v-model:show="showToast" :message="toastMessage" :variant="toastVariant" />
  </div>
</template>
