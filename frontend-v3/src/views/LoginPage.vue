<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores'
import { Button, Card, Input, Label } from '@/components/ui'
import { GraduationCap, Lock, User, Loader2 } from 'lucide-vue-next'
import { Toast } from '@/components/ui'

const authStore = useAuthStore()
const router = useRouter()

const form = ref({
  username: '',
  password: '',
  role: 'admin' as 'admin' | 'teacher' | 'student',
})

const showToast = ref(false)
const toastMessage = ref('')
const toastVariant = ref<'default' | 'success' | 'error'>('default')

const roles = [
  { value: 'admin', label: 'Administrator' },
  { value: 'teacher', label: 'Teacher' },
  { value: 'student', label: 'Student' },
]

const handleSubmit = async () => {
  if (!form.value.username || !form.value.password) {
    toastMessage.value = 'Please enter username and password'
    toastVariant.value = 'error'
    showToast.value = true
    return
  }

  try {
    await authStore.login(form.value)
    toastMessage.value = 'Login successful!'
    toastVariant.value = 'success'
    showToast.value = true

    // Redirect based on role
    const redirectMap: Record<string, string> = {
      admin: '/admin',
      teacher: '/teacher',
      student: '/student',
    }
    router.push(redirectMap[form.value.role])
  } catch (error: any) {
    toastMessage.value = error.message || 'Login failed'
    toastVariant.value = 'error'
    showToast.value = true
  }
}

// Demo credentials for quick login
const setDemoCredentials = (role: 'admin' | 'teacher' | 'student') => {
  form.value.role = role
  const credentials: Record<string, { username: string; password: string }> = {
    admin: { username: 'admin', password: 'admin123' },
    teacher: { username: 'teacher', password: 'teacher123' },
    student: { username: '2023001', password: 'student123' },
  }
  form.value.username = credentials[role].username
  form.value.password = credentials[role].password
}
</script>

<template>
  <div class="relative flex min-h-screen items-center justify-center overflow-hidden bg-background p-4">
    <!-- Background effects -->
    <div class="absolute inset-0 overflow-hidden">
      <div class="absolute -left-1/4 -top-1/4 h-[500px] w-[500px] rounded-full bg-primary/10 blur-[100px]" />
      <div class="absolute -right-1/4 -bottom-1/4 h-[500px] w-[500px] rounded-full bg-accent-cyan/10 blur-[100px]" />
    </div>

    <!-- Login form -->
    <Card class="relative w-full max-w-md border-white/10 p-8 backdrop-blur-xl">
      <div class="flex flex-col items-center space-y-2 text-center">
        <div class="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/20">
          <GraduationCap class="h-7 w-7 text-primary" />
        </div>
        <h1 class="text-2xl font-bold text-white">Welcome to ClassHub</h1>
        <p class="text-sm text-white/60">Sign in to your account</p>
      </div>

      <form @submit.prevent="handleSubmit" class="mt-8 space-y-6">
        <!-- Role selection -->
        <div class="space-y-2">
          <Label for="role">Role</Label>
          <div class="grid grid-cols-3 gap-2">
            <button
              v-for="role in roles"
              :key="role.value"
              type="button"
              :class="[
                'rounded-lg border px-3 py-2 text-sm font-medium transition-colors',
                form.role === role.value
                  ? 'border-primary bg-primary/10 text-primary'
                  : 'border-white/10 bg-white/5 text-white/60 hover:bg-white/10',
              ]"
              @click="form.role = role.value as any"
            >
              {{ role.label }}
            </button>
          </div>
        </div>

        <!-- Username -->
        <div class="space-y-2">
          <Label for="username">Username</Label>
          <div class="relative">
            <User class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/50" />
            <Input
              id="username"
              v-model="form.username"
              placeholder="Enter your username"
              class="pl-10"
              required
            />
          </div>
        </div>

        <!-- Password -->
        <div class="space-y-2">
          <Label for="password">Password</Label>
          <div class="relative">
            <Lock class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/50" />
            <Input
              id="password"
              v-model="form.password"
              type="password"
              placeholder="Enter your password"
              class="pl-10"
              required
            />
          </div>
        </div>

        <!-- Submit button -->
        <Button
          type="submit"
          class="w-full"
          :disabled="authStore.isLoggingIn"
        >
          <Loader2 v-if="authStore.isLoggingIn" class="mr-2 h-4 w-4 animate-spin" />
          Sign In
        </Button>
      </form>

      <!-- Quick login buttons for demo -->
      <div class="mt-6 border-t border-white/10 pt-6">
        <p class="mb-3 text-center text-xs text-white/50">Quick login (Demo)</p>
        <div class="flex gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            class="flex-1"
            @click="setDemoCredentials('admin')"
          >
            Admin
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            class="flex-1"
            @click="setDemoCredentials('teacher')"
          >
            Teacher
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            class="flex-1"
            @click="setDemoCredentials('student')"
          >
            Student
          </Button>
        </div>
      </div>
    </Card>

    <!-- Toast -->
    <Toast v-model:show="showToast" :message="toastMessage" :variant="toastVariant" />
  </div>
</template>
