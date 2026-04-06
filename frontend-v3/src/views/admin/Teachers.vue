<script setup lang="ts">
import { ref, computed } from 'vue'
import { Card, Button, Badge, Input, Dialog } from '@/components/ui'
import { Plus, Search, Loader2, Trash2, Key, BookOpen, Calendar, UserCircle } from 'lucide-vue-next'
import { useTeachers, useTeacherCreate, useTeacherUpdate, useTeacherDelete } from '@/composables/useTeachers'
import { useToast } from '@/composables/useToast'
import ManageClassesDialog from '@/components/admin/ManageClassesDialog.vue'
import ManageSchedulesDialog from '@/components/admin/ManageSchedulesDialog.vue'
import type { User } from '@/types'
import { getErrorMessage } from '@/lib/error'

// 获取教师主题色（基于索引循环使用）
const getTeacherTheme = (index: number) => {
  const themes = ['purple', 'blue', 'green', 'orange'] as const
  return themes[index % themes.length]
}

// 卡片主题辅助函数
type CardColor = 'blue' | 'green' | 'purple' | 'orange'

const getCardStyle = (color: CardColor) => {
  const varPrefix = `--card-${color}`
  return {
    backgroundColor: `var(${varPrefix}-bg)`,
    borderColor: `var(${varPrefix}-border)`,
    '--tw-shadow-color': `var(${varPrefix}-shadow)`,
  } as Record<string, string>
}

const getCardIconStyle = (color: CardColor) => {
  const varPrefix = `--card-${color}`
  return {
    backgroundColor: `var(${varPrefix}-icon-bg)`,
    color: `var(${varPrefix}-icon-text)`,
  }
}

const getCardGlowStyle = (color: CardColor) => {
  const varPrefix = `--card-${color}`
  return {
    backgroundColor: `var(${varPrefix}-glow)`,
  }
}

// Toast
const { showToast } = useToast()

// Data
const { data: teachers, isPending } = useTeachers()
const { mutateAsync: createTeacher, isPending: isCreating } = useTeacherCreate()
const { mutateAsync: updateTeacher, isPending: isUpdating } = useTeacherUpdate()
const { mutateAsync: deleteTeacher, isPending: isDeleting } = useTeacherDelete()

// Search
const searchQuery = ref('')
const filteredTeachers = computed(() => {
  if (!teachers.value) return []
  if (!searchQuery.value.trim()) return teachers.value
  const query = searchQuery.value.toLowerCase()
  return teachers.value.filter(
    t => t.name.toLowerCase().includes(query) || 
         t.username.toLowerCase().includes(query)
  )
})

// Add Dialog
const showAddDialog = ref(false)
const newTeacher = ref({
  username: '',
  name: '',
  password: '',
  confirmPassword: ''
})
const addErrors = ref({
  username: '',
  name: '',
  password: '',
  confirmPassword: ''
})

const openAddDialog = () => {
  newTeacher.value = { username: '', name: '', password: '', confirmPassword: '' }
  addErrors.value = { username: '', name: '', password: '', confirmPassword: '' }
  showAddDialog.value = true
}

const validateAddForm = () => {
  let valid = true
  addErrors.value = { username: '', name: '', password: '', confirmPassword: '' }
  
  if (!newTeacher.value.username.trim()) {
    addErrors.value.username = '请输入用户名'
    valid = false
  } else if (newTeacher.value.username.length < 3) {
    addErrors.value.username = '用户名至少3个字符'
    valid = false
  }
  
  if (!newTeacher.value.name.trim()) {
    addErrors.value.name = '请输入姓名'
    valid = false
  }
  
  if (!newTeacher.value.password) {
    addErrors.value.password = '请输入密码'
    valid = false
  } else if (newTeacher.value.password.length < 6) {
    addErrors.value.password = '密码至少6个字符'
    valid = false
  }
  
  if (newTeacher.value.password !== newTeacher.value.confirmPassword) {
    addErrors.value.confirmPassword = '两次密码输入不一致'
    valid = false
  }
  
  return valid
}

const handleAddTeacher = async (e?: Event) => {
  e?.preventDefault()
  if (!validateAddForm()) return
  
  try {
    await createTeacher({
      username: newTeacher.value.username.trim(),
      name: newTeacher.value.name.trim(),
      password: newTeacher.value.password,
      role: 'teacher'
    })
    showToast('教师创建成功', 'success')
    showAddDialog.value = false
  } catch (error: unknown) {
    showToast(getErrorMessage(error) || '创建失败', 'error')
  }
}

// Edit Dialog
const showEditDialog = ref(false)
const editingTeacher = ref<User | null>(null)
const editForm = ref({ name: '' })
const editError = ref('')

const openEditDialog = (teacher: User) => {
  editingTeacher.value = teacher
  editForm.value.name = teacher.name
  editError.value = ''
  showEditDialog.value = true
}

const handleEditTeacher = async () => {
  if (!editingTeacher.value) return
  if (!editForm.value.name.trim()) {
    editError.value = '请输入姓名'
    return
  }
  
  try {
    await updateTeacher({
      id: editingTeacher.value.id,
      data: { name: editForm.value.name.trim() }
    })
    showToast('教师信息更新成功', 'success')
    showEditDialog.value = false
  } catch (error: unknown) {
    showToast(getErrorMessage(error) || '更新失败', 'error')
  }
}

// Delete Dialog
const showDeleteDialog = ref(false)
const deletingTeacher = ref<User | null>(null)

const openDeleteDialog = (teacher: User) => {
  deletingTeacher.value = teacher
  showDeleteDialog.value = true
}

const handleDeleteTeacher = async () => {
  if (!deletingTeacher.value) return
  
  try {
    await deleteTeacher(deletingTeacher.value.id)
    showToast('教师删除成功', 'success')
    showDeleteDialog.value = false
  } catch (error: unknown) {
    showToast(getErrorMessage(error) || '删除失败', 'error')
  }
}

// Reset Password Dialog
const showResetDialog = ref(false)
const resettingTeacher = ref<User | null>(null)
const resetForm = ref({ newPassword: '', confirmPassword: '' })
const resetErrors = ref({ newPassword: '', confirmPassword: '' })
const isResetting = ref(false)

const openResetDialog = (teacher: User) => {
  resettingTeacher.value = teacher
  resetForm.value = { newPassword: '', confirmPassword: '' }
  resetErrors.value = { newPassword: '', confirmPassword: '' }
  showResetDialog.value = true
}

// Manage Classes Dialog
const showManageClassesDialog = ref(false)
const managingClassesTeacher = ref<User | null>(null)

const openManageClassesDialog = (teacher: User) => {
  managingClassesTeacher.value = teacher
  showManageClassesDialog.value = true
}

// Manage Schedules Dialog
const showManageSchedulesDialog = ref(false)
const managingSchedulesTeacher = ref<User | null>(null)

const openManageSchedulesDialog = (teacher: User) => {
  managingSchedulesTeacher.value = teacher
  showManageSchedulesDialog.value = true
}

const validateResetForm = () => {
  let valid = true
  resetErrors.value = { newPassword: '', confirmPassword: '' }
  
  if (!resetForm.value.newPassword) {
    resetErrors.value.newPassword = '请输入新密码'
    valid = false
  } else if (resetForm.value.newPassword.length < 6) {
    resetErrors.value.newPassword = '密码至少6个字符'
    valid = false
  }
  
  if (resetForm.value.newPassword !== resetForm.value.confirmPassword) {
    resetErrors.value.confirmPassword = '两次密码输入不一致'
    valid = false
  }
  
  return valid
}

const handleResetPassword = async () => {
  if (!resettingTeacher.value) return
  if (!validateResetForm()) return
  
  isResetting.value = true
  try {
    const { usersApi } = await import('@/api/users')
    await usersApi.resetPassword(resettingTeacher.value.id, resetForm.value.newPassword)
    showToast('密码重置成功', 'success')
    showResetDialog.value = false
  } catch (error: unknown) {
    showToast(getErrorMessage(error) || '密码重置失败', 'error')
  } finally {
    isResetting.value = false
  }
}
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-5">
      <div>
        <h1 class="text-2xl font-bold text-white">
          教师管理
        </h1>
        <p class="text-white/60">
          管理教师账号
        </p>
      </div>
      <Button @click="openAddDialog">
        <Plus class="mr-2 h-4 w-4" />
        添加教师
      </Button>
    </div>

    <!-- Search -->
    <div class="relative mb-5">
      <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/50" />
      <Input
        v-model="searchQuery"
        placeholder="搜索教师..."
        class="pl-10"
      />
    </div>

    <!-- Loading state -->
    <div
      v-if="isPending"
      class="flex h-64 items-center justify-center"
    >
      <Loader2 class="h-8 w-8 animate-spin text-primary" />
    </div>

    <!-- Teachers grid -->
    <div
      v-else-if="filteredTeachers.length > 0"
      class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3"
    >
      <Card
        v-for="(teacher, index) in filteredTeachers"
        :key="teacher.id"
        class="relative overflow-hidden p-6 transition-all duration-300 hover:scale-[1.02]"
        :style="getCardStyle(getTeacherTheme(index))"
      >
        <!-- 背景光晕效果 -->
        <div
          class="absolute -right-4 -bottom-4 h-24 w-24 rounded-full blur-2xl opacity-30"
          :style="getCardGlowStyle(getTeacherTheme(index))"
        />

        <div class="relative z-10 flex items-start gap-4">
          <div
            class="flex h-12 w-12 items-center justify-center rounded-xl shadow-inner"
            :style="getCardIconStyle(getTeacherTheme(index))"
          >
            <UserCircle
              class="h-6 w-6"
              :style="{ color: 'var(--card-' + getTeacherTheme(index) + '-icon-text)' }"
            />
          </div>
          <div class="flex-1 min-w-0">
            <h3 class="truncate font-medium text-white">
              {{ teacher.name }}
            </h3>
            <p class="text-sm text-[var(--color-text-tertiary)]">
              @{{ teacher.username }}
            </p>
            <div class="mt-2 flex items-center gap-2">
              <Badge variant="secondary">
                教师
              </Badge>
            </div>
          </div>
        </div>

        <!-- 任课信息展示 -->
        <div class="relative z-10 mt-4 rounded-xl bg-[var(--color-background-card)] p-3 border border-[var(--color-divider)]">
          <div class="flex items-center gap-2 text-[var(--color-text-tertiary)]">
            <BookOpen class="h-4 w-4" />
            <span class="text-xs">任课信息</span>
          </div>
          <p class="text-sm text-[var(--color-text-secondary)] mt-1">
            管理班级和课表安排
          </p>
        </div>

        <!-- 操作按钮组 -->
        <div class="relative z-10 mt-4 flex gap-2">
          <Button
            variant="outline"
            size="sm"
            class="flex-1 hover:bg-white/10"
            @click="openResetDialog(teacher)"
          >
            <Key class="mr-2 h-4 w-4" />
            重置密码
          </Button>
          <Button
            variant="outline"
            size="sm"
            class="flex-1 hover:bg-white/10"
            @click="openEditDialog(teacher)"
          >
            编辑
          </Button>
          <Button
            variant="outline"
            size="sm"
            class="hover:bg-red-500/10"
            @click="openDeleteDialog(teacher)"
          >
            <Trash2 class="h-4 w-4 text-[var(--color-error)]" />
          </Button>
        </div>
        <div class="relative z-10 mt-2 flex gap-2">
          <Button
            variant="outline"
            size="sm"
            class="flex-1 hover:bg-white/10"
            @click="openManageClassesDialog(teacher)"
          >
            <BookOpen class="mr-2 h-4 w-4" />
            管理班级
          </Button>
          <Button
            variant="outline"
            size="sm"
            class="flex-1 hover:bg-white/10"
            @click="openManageSchedulesDialog(teacher)"
          >
            <Calendar class="mr-2 h-4 w-4" />
            管理课表
          </Button>
        </div>
      </Card>
    </div>

    <!-- Empty state -->
    <div
      v-else
      class="flex h-64 flex-col items-center justify-center text-[var(--color-text-tertiary)]"
    >
      <UserCircle class="mb-4 h-12 w-12 opacity-50" />
      <p>暂无教师数据</p>
      <p class="mt-1 text-sm text-[var(--color-text-muted)]">
        点击右上角按钮添加教师
      </p>
    </div>

    <!-- Add Dialog -->
    <Dialog 
      v-model:open="showAddDialog" 
      title="添加教师" 
      description="创建新的教师账号"
      :as-form="true"
      :on-submit="handleAddTeacher"
    >
      <div class="space-y-4">
        <div>
          <label class="text-sm text-white/80">用户名</label>
          <Input
            v-model="newTeacher.username"
            placeholder="请输入用户名"
            :class="['mt-1', addErrors.username && 'border-red-500']"
          />
          <p
            v-if="addErrors.username"
            class="mt-1 text-sm text-red-400"
          >
            {{ addErrors.username }}
          </p>
        </div>
        <div>
          <label class="text-sm text-white/80">姓名</label>
          <Input
            v-model="newTeacher.name"
            placeholder="请输入姓名"
            :class="['mt-1', addErrors.name && 'border-red-500']"
          />
          <p
            v-if="addErrors.name"
            class="mt-1 text-sm text-red-400"
          >
            {{ addErrors.name }}
          </p>
        </div>
        <div>
          <label class="text-sm text-white/80">密码</label>
          <Input
            v-model="newTeacher.password"
            type="password"
            placeholder="请输入密码（至少6位）"
            :class="['mt-1', addErrors.password && 'border-red-500']"
          />
          <p
            v-if="addErrors.password"
            class="mt-1 text-sm text-red-400"
          >
            {{ addErrors.password }}
          </p>
        </div>
        <div>
          <label class="text-sm text-white/80">确认密码</label>
          <Input
            v-model="newTeacher.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            :class="['mt-1', addErrors.confirmPassword && 'border-red-500']"
          />
          <p
            v-if="addErrors.confirmPassword"
            class="mt-1 text-sm text-red-400"
          >
            {{ addErrors.confirmPassword }}
          </p>
        </div>
      </div>
      <template #footer>
        <Button
          type="button"
          variant="outline"
          @click="showAddDialog = false"
        >
          取消
        </Button>
        <Button
          type="submit"
          :disabled="isCreating"
        >
          <Loader2
            v-if="isCreating"
            class="mr-2 h-4 w-4 animate-spin"
          />
          创建
        </Button>
      </template>
    </Dialog>

    <!-- Edit Dialog -->
    <Dialog
      v-model:open="showEditDialog"
      title="编辑教师"
      description="修改教师信息"
    >
      <div class="space-y-4">
        <div>
          <label class="text-sm text-white/80">姓名</label>
          <Input
            v-model="editForm.name"
            placeholder="请输入姓名"
            :class="['mt-1', editError && 'border-red-500']"
            @keyup.enter="handleEditTeacher"
          />
          <p
            v-if="editError"
            class="mt-1 text-sm text-red-400"
          >
            {{ editError }}
          </p>
        </div>
      </div>
      <template #footer>
        <Button
          variant="outline"
          @click="showEditDialog = false"
        >
          取消
        </Button>
        <Button
          :disabled="isUpdating"
          @click="handleEditTeacher"
        >
          <Loader2
            v-if="isUpdating"
            class="mr-2 h-4 w-4 animate-spin"
          />
          保存
        </Button>
      </template>
    </Dialog>

    <!-- Delete Dialog -->
    <Dialog
      v-model:open="showDeleteDialog"
      title="删除教师"
      :description="`确定要删除教师 '${deletingTeacher?.name}' 吗？此操作不可恢复。`"
    >
      <template #footer>
        <Button
          variant="outline"
          @click="showDeleteDialog = false"
        >
          取消
        </Button>
        <Button
          variant="destructive"
          :disabled="isDeleting"
          @click="handleDeleteTeacher"
        >
          <Loader2
            v-if="isDeleting"
            class="mr-2 h-4 w-4 animate-spin"
          />
          删除
        </Button>
      </template>
    </Dialog>

    <!-- Reset Password Dialog -->
    <Dialog
      v-model:open="showResetDialog"
      title="重置密码"
      :description="`为 '${resettingTeacher?.name}' 设置新密码`"
    >
      <div class="space-y-4">
        <div>
          <label class="text-sm text-white/80">新密码</label>
          <Input
            v-model="resetForm.newPassword"
            type="password"
            placeholder="请输入新密码（至少6位）"
            :class="['mt-1', resetErrors.newPassword && 'border-red-500']"
            @keyup.enter="handleResetPassword"
          />
          <p
            v-if="resetErrors.newPassword"
            class="mt-1 text-sm text-red-400"
          >
            {{ resetErrors.newPassword }}
          </p>
        </div>
        <div>
          <label class="text-sm text-white/80">确认新密码</label>
          <Input
            v-model="resetForm.confirmPassword"
            type="password"
            placeholder="请再次输入新密码"
            :class="['mt-1', resetErrors.confirmPassword && 'border-red-500']"
            @keyup.enter="handleResetPassword"
          />
          <p
            v-if="resetErrors.confirmPassword"
            class="mt-1 text-sm text-red-400"
          >
            {{ resetErrors.confirmPassword }}
          </p>
        </div>
      </div>
      <template #footer>
        <Button
          variant="outline"
          @click="showResetDialog = false"
        >
          取消
        </Button>
        <Button
          :disabled="isResetting"
          @click="handleResetPassword"
        >
          <Loader2
            v-if="isResetting"
            class="mr-2 h-4 w-4 animate-spin"
          />
          重置密码
        </Button>
      </template>
    </Dialog>

    <!-- Manage Classes Dialog -->
    <ManageClassesDialog
      v-model:open="showManageClassesDialog"
      :teacher="managingClassesTeacher"
      @success="() => { /* 数据会自动刷新 */ }"
    />

    <!-- Manage Schedules Dialog -->
    <ManageSchedulesDialog
      v-model:open="showManageSchedulesDialog"
      :teacher="managingSchedulesTeacher"
      @success="() => { /* 数据会自动刷新 */ }"
    />
  </div>
</template>
