<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useMutation } from '@tanstack/vue-query'
import { authApi } from '@/api'
import { useToast } from '@/composables'
import { getErrorMessage } from '@/lib/error'
import { Dialog, Input, Label, Button } from '@/components/ui'

const props = defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
}>()

const { success, error: showError } = useToast()

const form = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const formError = ref('')

const validate = (): boolean => {
  formError.value = ''

  if (!form.old_password.trim()) {
    formError.value = '请输入旧密码'
    return false
  }
  if (!form.new_password.trim()) {
    formError.value = '请输入新密码'
    return false
  }
  if (form.new_password.length < 6) {
    formError.value = '新密码至少需要 6 个字符'
    return false
  }
  if (form.new_password !== form.confirm_password) {
    formError.value = '两次输入的新密码不一致'
    return false
  }

  return true
}

const resetForm = () => {
  form.old_password = ''
  form.new_password = ''
  form.confirm_password = ''
  formError.value = ''
}

const mutation = useMutation({
  mutationFn: () =>
    authApi.changePassword({
      old_password: form.old_password,
      new_password: form.new_password,
    }),
  onSuccess: () => {
    success('密码修改成功')
    emit('update:open', false)
    resetForm()
  },
  onError: (err: unknown) => {
    showError(getErrorMessage(err) || '密码修改失败')
  },
})

const handleSubmit = () => {
  if (!validate()) return
  mutation.mutate()
}

const handleClose = () => {
  emit('update:open', false)
  resetForm()
}
</script>

<template>
  <Dialog
    :open="open"
    :as-form="true"
    :on-submit="handleSubmit"
    title="修改密码"
    description="请输入旧密码和新密码来完成修改"
    @update:open="emit('update:open', $event)"
  >
    <div class="space-y-4">
      <!-- 旧密码 -->
      <div class="space-y-2">
        <Label for="old-password" class="text-black">旧密码</Label>
        <Input
          id="old-password"
          v-model="form.old_password"
          type="password"
          placeholder="请输入旧密码"
          autocomplete="current-password"
        />
      </div>

      <!-- 新密码 -->
      <div class="space-y-2">
        <Label for="new-password" class="text-black">新密码</Label>
        <Input
          id="new-password"
          v-model="form.new_password"
          type="password"
          placeholder="请输入新密码（至少 6 个字符）"
          autocomplete="new-password"
        />
      </div>

      <!-- 确认新密码 -->
      <div class="space-y-2">
        <Label for="confirm-password" class="text-black">确认新密码</Label>
        <Input
          id="confirm-password"
          v-model="form.confirm_password"
          type="password"
          placeholder="请再次输入新密码"
          autocomplete="new-password"
        />
      </div>

      <!-- 错误提示 -->
      <p
        v-if="formError"
        class="text-sm text-[#ef4444]"
      >
        {{ formError }}
      </p>
    </div>

    <template #footer>
      <Button
        variant="default"
        type="button"
        @click="handleClose"
      >
        取消
      </Button>
      <Button
        variant="cta"
        type="submit"
        :loading="mutation.isPending.value"
      >
        确认修改
      </Button>
    </template>
  </Dialog>
</template>
