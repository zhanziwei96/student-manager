<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores'
import { useToast } from '@/composables'
import { getErrorMessage } from '@/lib/error'
import type { UserRole } from '@/types'
import { Button, Card, Input, Label, ToastContainer } from '@/components/ui'
import { GraduationCap, Lock, User } from 'lucide-vue-next'

const authStore = useAuthStore()
const router = useRouter()
const { success, error: showError } = useToast()

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
  <div class="relative flex min-h-screen items-start sm:items-center justify-center bg-white p-4 pt-16 sm:pt-4">
    <!-- Login form -->
    <Card class="relative w-full max-w-md border-[#e5e5e5] p-6 sm:p-8">
      <div class="flex flex-col items-center space-y-2 text-center">
        <div class="flex h-12 w-12 items-center justify-center rounded-xl bg-[#fafafa] border border-[#e5e5e5]">
          <GraduationCap class="h-7 w-7 text-black" />
        </div>
        <h1 class="text-2xl font-medium text-black">
          欢迎使用智慧课堂
        </h1>
        <p class="text-sm text-[#737373]">
          登录您的账号
        </p>
      </div>

      <form
        class="mt-8 space-y-6"
        autocomplete="off"
        @submit.prevent="handleSubmit"
      >
        <!-- Role selection -->
        <div class="space-y-2">
          <Label for="role">角色</Label>
          <div class="grid grid-cols-3 gap-2">
            <button
              v-for="role in roles"
              :key="role.value"
              type="button"
              :class="[
                'rounded-full border px-3 py-2 text-sm font-medium transition-colors',
                form.role === role.value
                  ? 'border-[#e5e5e5] bg-[#e5e5e5] text-[#262626]'
                  : 'border-[#e5e5e5] bg-white text-[#737373] hover:bg-[#fafafa]',
              ]"
              @click="form.role = role.value as UserRole"
            >
              {{ role.label }}
            </button>
          </div>
        </div>

        <!-- Username -->
        <div class="space-y-2 mt-6">
          <Label for="username">用户名</Label>
          <div class="relative">
            <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
              <User class="h-4 w-4 text-[#a3a3a3]" />
            </div>
            <Input
              id="username"
              v-model="form.username"
              type="text"
              autocomplete="username"
              placeholder="请输入用户名"
              :class="['pl-10', errors.username && 'border-red-500 focus:border-red-500']"
              @input="errors.username = ''"
            />
          </div>
        </div>

        <!-- Password -->
        <div class="space-y-2 mt-6">
          <Label for="password">密码</Label>
          <div class="relative">
            <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
              <Lock class="h-4 w-4 text-[#a3a3a3]" />
            </div>
            <Input
              id="password"
              v-model="form.password"
              type="password"
              autocomplete="current-password"
              placeholder="请输入密码"
              :class="['pl-10', errors.password && 'border-red-500 focus:border-red-500']"
              @input="errors.password = ''"
            />
          </div>
        </div>

        <!-- Submit button -->
        <Button
          type="submit"
          variant="cta"
          class="w-full mt-8"
          :loading="authStore.isLoggingIn"
        >
          登录
        </Button>
      </form>
    </Card>

    <!-- Toast 通知容器（队列模式） -->
    <ToastContainer />
  </div>
</template>
