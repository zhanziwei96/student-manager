<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Dialog, Button } from '@/components/ui'
import { Loader2, Search, BookOpen, Check, X, Users, Plus } from 'lucide-vue-next'
import { useToast } from '@/composables/useToast'
import { useClasses } from '@/composables/useClasses'
import { usersApi } from '@/api/users'
import type { User } from '@/types'
import { getErrorMessage } from '@/lib/error'

const props = defineProps<{
  teacher: User | null
  open: boolean
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  'success': []
  'update:teacher': [teacher: User]
}>()

const { showToast } = useToast()

// 获取所有班级
const { data: allClasses, isPending: isLoadingClasses } = useClasses()

// 搜索
const searchQuery = ref('')

// 当前选中的班级（即将保存的分配）
const selectedClasses = ref<string[]>([])

// 原始分配的班级（用于对比变更）
const originalClasses = ref<string[]>([])

// 初始化选中的班级
watch(() => [props.teacher, allClasses.value], ([teacher, classes]) => {
  if (!teacher || !('assigned_classes' in teacher)) {
    selectedClasses.value = []
    originalClasses.value = []
    return
  }

  // 防御性处理：确保 assigned_classes 是数组
  const assignedClasses = Array.isArray(teacher.assigned_classes)
    ? teacher.assigned_classes
    : []

  if (classes && Array.isArray(classes)) {
    // 获取所有有效的班级名称
    const validClassNames = new Set((classes as { name: string }[]).map((c: { name: string }) => c.name))
    // 只保留教师 assigned_classes 中存在的班级
    const validAssigned = assignedClasses.filter((name: string) => validClassNames.has(name))
    selectedClasses.value = [...validAssigned]
    originalClasses.value = [...validAssigned]
  } else {
    selectedClasses.value = [...assignedClasses]
    originalClasses.value = [...assignedClasses]
  }
}, { immediate: true })

// 计算变更
const changes = computed(() => {
  const original = new Set(originalClasses.value)
  const selected = new Set(selectedClasses.value)
  
  const added = selectedClasses.value.filter(name => !original.has(name))
  const removed = originalClasses.value.filter(name => !selected.has(name))
  
  return { added, removed, hasChanges: added.length > 0 || removed.length > 0 }
})

// 已分配的班级列表（带完整信息）
const assignedClassesList = computed(() => {
  if (!allClasses.value) return []
  const selectedSet = new Set(selectedClasses.value)
  return allClasses.value.filter(cls => selectedSet.has(cls.name))
})

// 可分配的班级列表（未分配且符合搜索条件）
const availableClassesList = computed(() => {
  if (!allClasses.value) return []
  const selectedSet = new Set(selectedClasses.value)
  
  let classes = allClasses.value.filter(cls => !selectedSet.has(cls.name))
  
  // 应用搜索过滤
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    classes = classes.filter(cls => cls.name.toLowerCase().includes(query))
  }
  
  return classes
})

// 添加班级到已分配
const addClass = (className: string) => {
  if (!selectedClasses.value.includes(className)) {
    selectedClasses.value.push(className)
  }
}

// 从已分配中移除班级
const removeClass = (className: string) => {
  const index = selectedClasses.value.indexOf(className)
  if (index > -1) {
    selectedClasses.value.splice(index, 1)
  }
}

// 添加所有可分配班级（根据当前搜索）
const addAllVisible = () => {
  const namesToAdd = availableClassesList.value.map(cls => cls.name)
  namesToAdd.forEach(name => {
    if (!selectedClasses.value.includes(name)) {
      selectedClasses.value.push(name)
    }
  })
}

// 清空所有已分配
const removeAll = () => {
  selectedClasses.value = []
}

// 保存中状态
const isSaving = ref(false)

// 保存修改
const handleSave = async () => {
  if (!props.teacher) return
  
  isSaving.value = true
  try {
    await usersApi.update(props.teacher.id, {
      assigned_classes: selectedClasses.value
    })
    
    // 更新本地教师数据
    emit('update:teacher', { ...props.teacher, assigned_classes: [...selectedClasses.value] })
    originalClasses.value = [...selectedClasses.value]
    
    showToast('班级分配已更新', 'success')
    emit('success')
    emit('update:open', false)
  } catch (error: unknown) {
    showToast(getErrorMessage(error) || '保存失败', 'error')
  } finally {
    isSaving.value = false
  }
}

// 关闭弹窗
const handleClose = () => {
  // 重置选择到原始状态
  if (props.teacher) {
    selectedClasses.value = [...originalClasses.value]
  }
  searchQuery.value = ''
  emit('update:open', false)
}
</script>

<template>
  <Dialog
    :open="open"
    :title="`管理班级 - ${teacher?.name || ''}`"
    description="管理该教师负责的班级"
    @update:open="handleClose"
  >
    <div class="space-y-4">
      <!-- 加载中 -->
      <div
        v-if="isLoadingClasses"
        class="flex h-32 items-center justify-center"
      >
        <Loader2 class="h-6 w-6 animate-spin text-black" />
      </div>

      <template v-else>
        <!-- 已分配班级区域 -->
        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <h4 class="text-sm font-medium text-black flex items-center gap-2">
              <Check class="h-4 w-4 text-[#16a34a]" />
              已分配班级
              <span class="text-xs text-[#a3a3a3]">({{ assignedClassesList.length }})</span>
            </h4>
            <Button
              v-if="assignedClassesList.length > 0"
              type="button"
              variant="ghost"
              size="sm"
              class="h-7 text-xs text-[#dc2626] hover:text-[#b91c1c] hover:bg-[rgba(239,68,68,0.1)]"
              @click="removeAll"
            >
              <X class="mr-1 h-3 w-3" />
              全部移除
            </Button>
          </div>
          
          <div
            v-if="assignedClassesList.length === 0"
            class="rounded-xl border border-dashed border-[#e5e5e5] bg-[#fafafa] p-4 text-center"
          >
            <p class="text-sm text-[#a3a3a3]">
              暂无分配的班级
            </p>
          </div>
          
          <div
            v-else
            class="max-h-[120px] space-y-1.5 overflow-y-auto rounded-xl border border-[#e5e5e5] bg-[#fafafa] p-2"
          >
            <div
              v-for="cls in assignedClassesList"
              :key="cls.name"
              class="flex items-center gap-2 rounded-md bg-[rgba(34,197,94,0.15)] px-3 py-2 group hover:bg-green-500/15 transition-colors"
            >
              <BookOpen class="h-4 w-4 text-[#16a34a]" />
              <span class="flex-1 text-sm text-black">{{ cls.name }}</span>
              <button
                type="button"
                class="ml-1 p-1 rounded hover:bg-[rgba(239,68,68,0.1)] text-[#a3a3a3] hover:text-[#dc2626] transition-colors opacity-0 group-hover:opacity-100"
                title="移除"
                @click="removeClass(cls.name)"
              >
                <X class="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        </div>

        <!-- 分隔线 -->
        <div class="border-t border-[#e5e5e5]" />

        <!-- 可分配班级区域 -->
        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <h4 class="text-sm font-medium text-black flex items-center gap-2">
              <Users class="h-4 w-4 text-black" />
              可分配班级
              <span class="text-xs text-[#a3a3a3]">({{ availableClassesList.length }})</span>
            </h4>
          </div>

          <!-- 搜索框 -->
          <div class="relative">
            <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#a3a3a3]" />
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索班级..."
              class="w-full rounded-full border border-[#e5e5e5] bg-[#fafafa] py-2 pl-10 pr-4 text-sm text-black placeholder:text-[#a3a3a3] focus:border-black focus:outline-none"
            >
          </div>

          <!-- 批量操作 -->
          <div
            v-if="availableClassesList.length > 0 && !searchQuery"
            class="flex gap-2"
          >
            <Button
              type="button"
              variant="outline"
              size="sm"
              class="h-7 text-xs"
              @click="addAllVisible"
            >
              添加全部
            </Button>
          </div>

          <!-- 可分配班级列表 -->
          <div
            v-if="availableClassesList.length === 0"
            class="rounded-xl border border-dashed border-[#e5e5e5] bg-[#fafafa] p-4 text-center"
          >
            <p class="text-sm text-[#a3a3a3]">
              {{ searchQuery ? '未找到匹配的班级' : '暂无可分配的班级' }}
            </p>
          </div>
          
          <div
            v-else
            class="max-h-[160px] space-y-1.5 overflow-y-auto rounded-xl border border-[#e5e5e5] bg-[#fafafa] p-2"
          >
            <div
              v-for="cls in availableClassesList"
              :key="cls.name"
              class="flex items-center gap-2 rounded-md px-3 py-2 hover:bg-[#fafafa] cursor-pointer transition-colors group"
              @click="addClass(cls.name)"
            >
              <div class="w-4 h-4 rounded border border-[#d4d4d4] flex items-center justify-center group-hover:border-[#d4d4d4] transition-colors">
                <Plus class="h-3 w-3 text-transparent group-hover:text-[#525252] transition-colors" />
              </div>
              <BookOpen class="h-4 w-4 text-[#a3a3a3]" />
              <span class="flex-1 text-sm text-[#262626]">{{ cls.name }}</span>
            </div>
          </div>
        </div>

        <!-- 变更摘要 -->
        <div 
          class="rounded-xl border p-3 transition-colors"
          :class="changes.hasChanges ? 'border-[#d4d4d4] bg-[#fafafa]' : 'border-[#e5e5e5] bg-[#fafafa]'"
        >
          <div class="flex items-center justify-between">
            <p class="text-sm text-[#737373]">
              <span v-if="!changes.hasChanges">暂无变更</span>
              <span
                v-else
                class="flex items-center gap-3"
              >
                <span
                  v-if="changes.added.length > 0"
                  class="text-[#16a34a]"
                >
                  +{{ changes.added.length }} 个新增
                </span>
                <span
                  v-if="changes.removed.length > 0"
                  class="text-[#dc2626]"
                >
                  -{{ changes.removed.length }} 个移除
                </span>
              </span>
            </p>
            <span class="text-xs text-[#a3a3a3]">
              共 {{ selectedClasses.length }} 个班级
            </span>
          </div>
        </div>
      </template>
    </div>

    <template #footer>
      <Button
        type="button"
        variant="outline"
        @click="handleClose"
      >
        取消
      </Button>
      <Button
        type="button"
        :disabled="isSaving || !changes.hasChanges"
        @click="handleSave"
      >
        <Loader2
          v-if="isSaving"
          class="mr-2 h-4 w-4 animate-spin"
        />
        {{ changes.hasChanges ? `保存变更 (${changes.added.length + changes.removed.length})` : '暂无变更' }}
      </Button>
    </template>
  </Dialog>
</template>
