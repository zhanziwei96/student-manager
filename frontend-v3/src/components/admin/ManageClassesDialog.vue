<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Dialog, Button, Checkbox } from '@/components/ui'
import { Loader2, Search, BookOpen } from 'lucide-vue-next'
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
}>()

const { showToast } = useToast()

// 获取所有班级
const { data: allClasses, isPending: isLoadingClasses } = useClasses()

// 搜索
const searchQuery = ref('')

// 选中的班级
const selectedClasses = ref<string[]>([])

// 初始化选中的班级（只保留有效的班级名称）
watch(() => [props.teacher, allClasses.value], ([teacher, classes]) => {
  // 防御性处理：确保 assigned_classes 是数组
  const assignedClasses = Array.isArray(teacher?.assigned_classes) 
    ? teacher.assigned_classes 
    : []
  
  if (teacher && classes) {
    // 获取所有有效的班级名称
    const validClassNames = new Set(classes.map(c => c.name))
    // 只保留教师 assigned_classes 中存在的班级
    selectedClasses.value = assignedClasses.filter(
      name => validClassNames.has(name)
    )
  } else if (teacher) {
    selectedClasses.value = [...assignedClasses]
  } else {
    selectedClasses.value = []
  }
}, { immediate: true })

// 过滤后的班级列表
const filteredClasses = computed(() => {
  if (!allClasses.value) return []
  if (!searchQuery.value.trim()) return allClasses.value
  
  const query = searchQuery.value.toLowerCase()
  return allClasses.value.filter(cls => 
    cls.name.toLowerCase().includes(query)
  )
})

// 已选择的数量
const selectedCount = computed(() => selectedClasses.value.length)

// 切换班级选择
const toggleClass = (className: string) => {
  const index = selectedClasses.value.indexOf(className)
  if (index > -1) {
    selectedClasses.value.splice(index, 1)
  } else {
    selectedClasses.value.push(className)
  }
}

// 是否选中
const isSelected = (className: string) => {
  return selectedClasses.value.includes(className)
}

// 全选
const selectAll = () => {
  if (filteredClasses.value) {
    selectedClasses.value = filteredClasses.value.map(cls => cls.name)
  }
}

// 取消全选
const deselectAll = () => {
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
    props.teacher.assigned_classes = [...selectedClasses.value]
    
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
  // 重置选择
  if (props.teacher) {
    selectedClasses.value = [...(props.teacher.assigned_classes || [])]
  }
  emit('update:open', false)
}
</script>

<template>
  <Dialog
    :open="open"
    @update:open="handleClose"
    :title="`管理班级 - ${teacher?.name || ''}`"
    description="选择该教师负责的班级"
  >
    <div class="space-y-4">
      <!-- 搜索框 -->
      <div class="relative">
        <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/50" />
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜索班级..."
          class="w-full rounded-lg border border-white/10 bg-white/[0.02] py-2 pl-10 pr-4 text-sm text-white placeholder:text-white/40 focus:border-primary focus:outline-none"
        />
      </div>

      <!-- 加载中 -->
      <div v-if="isLoadingClasses" class="flex h-32 items-center justify-center">
        <Loader2 class="h-6 w-6 animate-spin text-primary" />
      </div>

      <!-- 班级列表 -->
      <div v-else-if="filteredClasses.length > 0" class="max-h-[300px] space-y-2 overflow-y-auto">
        <!-- 全选/取消全选 -->
        <div class="sticky top-0 flex gap-2 bg-[#030307] pb-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            @click="selectAll"
          >
            全选
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            @click="deselectAll"
          >
            取消全选
          </Button>
        </div>

        <!-- 班级项 -->
        <div
          v-for="cls in filteredClasses"
          :key="cls.name"
          class="flex items-center gap-3 rounded-lg border border-white/10 bg-white/[0.02] p-3 hover:bg-white/[0.04] cursor-pointer transition-colors"
          @click="toggleClass(cls.name)"
        >
          <Checkbox
            :checked="isSelected(cls.name)"
            @click.stop
            @update:checked="() => toggleClass(cls.name)"
          />
          <BookOpen class="h-4 w-4 text-primary" />
          <span class="flex-1 text-sm text-white">{{ cls.name }}</span>
          <span 
            class="text-xs px-2 py-0.5 rounded-full"
            :class="cls.status === 'active' ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'"
          >
            {{ cls.status === 'active' ? '启用' : '停用' }}
          </span>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="flex h-32 flex-col items-center justify-center text-white/60">
        <BookOpen class="mb-2 h-8 w-8" />
        <p>{{ searchQuery ? '未找到匹配的班级' : '暂无班级数据' }}</p>
      </div>

      <!-- 已选择统计 -->
      <div class="rounded-lg border border-white/10 bg-white/[0.02] p-3">
        <p class="text-sm text-white/80">
          已选择: <span class="font-medium text-primary">{{ selectedCount }}</span> 个班级
        </p>
      </div>
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
        :disabled="isSaving"
        @click="handleSave"
      >
        <Loader2
          v-if="isSaving"
          class="mr-2 h-4 w-4 animate-spin"
        />
        保存
      </Button>
    </template>
  </Dialog>
</template>
