<script setup lang="ts">
import { ref, computed } from 'vue'
import { useSubjects, useUpdateSubject, useDeriveSubjects } from '@/composables/useSubjects'
import { useToast } from '@/composables'
import { Card, Button, Dialog, Input, Label, DataContainer } from '@/components/ui'
import { Pencil, RefreshCw } from 'lucide-vue-next'
import type { Subject } from '@/api'
import { getErrorMessage } from '@/lib/error'

/**
 * 科目管理页面（管理员）
 *
 * 展示当前学期科目列表（卡片式），支持修改科目名称、从课表推导科目
 */

// === 数据获取 ===
const { data, isPending, error, refetch } = useSubjects()
// 通过 computed 统一取值，兼容 Ref 与普通 { value } 对象
const subjects = computed<Subject[]>(() => data.value ?? [])
const loading = computed(() => isPending.value)
const loadError = computed(() => error?.value ?? null)
const { mutateAsync: updateSubject, isPending: isUpdating } = useUpdateSubject()
const { mutateAsync: deriveSubjects, isPending: isDeriving } = useDeriveSubjects()

// === Toast 状态 (队列模式) ===
const { success: showSuccessToast, error: showErrorToast } = useToast()

// === 修改科目名称对话框 ===
const showEditDialog = ref(false)
const editingSubject = ref<Subject | null>(null)
const editName = ref('')
const editNameError = ref('')

// 打开修改科目名称弹窗
const openEditDialog = (subject: Subject) => {
  editingSubject.value = subject
  editName.value = subject.name
  editNameError.value = ''
  showEditDialog.value = true
}

// 处理修改科目名称
const handleUpdateSubject = async () => {
  const name = editName.value.trim()
  if (!name) {
    editNameError.value = '请输入科目名称'
    return
  }
  if (!editingSubject.value) return

  try {
    await updateSubject({ id: editingSubject.value.id, name })
    showEditDialog.value = false
    showSuccessToast('科目已更新')
  } catch (err: unknown) {
    showErrorToast(getErrorMessage(err) || '修改科目名称失败')
  }
}

// === 从课表推导 ===
const handleDerive = async () => {
  try {
    const result = await deriveSubjects()
    showSuccessToast(`已推导 ${result.created_count} 个科目`)
  } catch (err: unknown) {
    showErrorToast(getErrorMessage(err) || '从课表推导失败')
  }
}
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-5">
      <div>
        <h1 class="text-2xl font-medium text-black">
          科目管理
        </h1>
        <p class="text-[#737373]">
          管理当前学期的科目
        </p>
      </div>
      <Button
        variant="outline"
        :loading="isDeriving"
        data-testid="derive-subjects-btn"
        @click="handleDerive"
      >
        <RefreshCw class="mr-2 h-4 w-4" />
        从课表推导
      </Button>
    </div>

    <!-- Data Container -->
    <DataContainer
      :loading="loading"
      :error="loadError"
      :has-data="subjects.length > 0"
      empty-text="当前学期暂无科目"
      @retry="refetch"
    >
      <!-- 卡片列表 -->
      <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <Card
          v-for="subject in subjects"
          :key="subject.id"
          class="p-4 bg-white border-[#e5e5e5]"
        >
          <div class="flex items-center justify-between">
            <div class="min-w-0">
              <p class="font-medium text-black truncate">
                {{ subject.name }}
              </p>
              <p class="text-sm text-[#a3a3a3] mt-0.5">
                {{ subject.semester }}
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              :data-testid="`edit-subject-${subject.id}`"
              @click="openEditDialog(subject)"
            >
              <Pencil class="mr-1 h-3.5 w-3.5" />
              修改
            </Button>
          </div>
        </Card>
      </div>
    </DataContainer>

    <!-- Edit Subject Dialog -->
    <Dialog
      v-model:open="showEditDialog"
      title="修改科目名称"
    >
      <div class="space-y-2">
        <Label for="subjectName">科目名称</Label>
        <Input
          id="subjectName"
          v-model="editName"
          placeholder="输入科目名称"
          :class="editNameError ? 'border-[#ef4444]' : ''"
        />
        <p
          v-if="editNameError"
          class="text-sm text-[#ef4444]"
        >
          {{ editNameError }}
        </p>
      </div>
      <template #footer>
        <Button
          variant="outline"
          @click="showEditDialog = false"
        >
          取消
        </Button>
        <Button
          :loading="isUpdating"
          data-testid="confirm-edit-subject-btn"
          @click="handleUpdateSubject"
        >
          保存
        </Button>
      </template>
    </Dialog>
  </div>
</template>
