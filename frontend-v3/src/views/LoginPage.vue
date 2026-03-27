<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores'
import { useToast } from '@/composables'
import { getErrorMessage } from '@/lib/error'
import type { UserRole } from '@/types'
import { Button, Card, Input, Label } from '@/components/ui'
import { GraduationCap, Lock, User } from 'lucide-vue-next'
import { Toast } from '@/components/ui'

const authStore = useAuthStore()
const router = useRouter()
const { show, message: toastMessage, variant: toastVariant, success, error: showError } = useToast()

const form = ref({
  username: '',
  password: '',
  role: 'admin' as 'admin' | 'teacher' | 'student',
})

const errors = ref({
  username: '',
  password: '',
})

const roles = [
  { value: 'admin', label: '管理员' },
  { value: 'teacher', label: '教师' },
  { value: 'student', label: '学生' },
]

const validateForm = () => {
  errors.value = { username: '', password: '' }
  let isValid = true

  if (!form.value.username.trim()) {
    errors.value.username = '请输入用户名'
    showError('请输入用户名')
    isValid = false
  } else if (!form.value.password.trim()) {
    errors.value.password = '请输入密码'
    showError('请输入密码')
    isValid = false
  }

  return isValid
}

const handleSubmit = async () => {
  if (!validateForm()) {
    return
  }

  try {
    const userInfo = await authStore.login(form.value)
    success('登录成功！')

    // 根据后端返回的实际角色跳转（而非前端选择的角色）
    const userRole = userInfo?.role
    const redirectMap: Record<string, string> = {
      admin: '/admin',
      teacher: '/teacher',
      student: '/student',
    }
    if (userRole && redirectMap[userRole]) {
      router.push(redirectMap[userRole])
    } else {
      throw new Error('无法获取用户角色信息')
    }
  } catch (err: unknown) {
    showError(getErrorMessage(err) || '登录失败')
  }
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
        <h1 class="text-2xl font-bold text-white">欢迎使用智慧课堂</h1>
        <p class="text-sm text-white/60">登录您的账号</p>
      </div>

      <form @submit.prevent="handleSubmit" class="mt-8 space-y-6">
        <!-- Role selection -->
        <div class="space-y-2">
          <Label for="role">角色</Label>
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
              @click="form.role = role.value as UserRole"
            >
              {{ role.label }}
            </button>
          </div>
        </div>

        <!-- Username -->
        <div class="space-y-2">
          <Label for="username">用户名</Label>
          <div class="relative">
            <User class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/50" />
            <Input
              id="username"
              v-model="form.username"
              placeholder="请输入用户名"
              :class="['pl-10', errors.username && 'border-red-500 focus:border-red-500']"
              @input="errors.username = ''"
            />
          </div>
        </div>

        <!-- Password -->
        <div class="space-y-2">
          <Label for="password">密码</Label>
          <div class="relative">
            <Lock class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/50" />
            <Input
              id="password"
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              :class="['pl-10', errors.password && 'border-red-500 focus:border-red-500']"
              @input="errors.password = ''"
            />
          </div>
        </div>

        <!-- Submit button -->
        <Button
          type="submit"
          class="w-full"
          :loading="authStore.isLoggingIn"
        >
          登录
        </Button>
      </form>

    </Card>

    <!-- Toast -->
    <Toast v-model:show="show" :message="toastMessage" :variant="toastVariant" />
  </div>
</template>
