<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuery } from '@tanstack/vue-query'
import { Card, Button, Input, DataContainer, Checkbox } from '@/components/ui'
import {
  useCreateLostFoundItem,
  useUpdateLostFoundItem,
  useTeacherLostFoundDetail,
} from '@/composables/useLostFound'
import { classesApi } from '@/api/classes'
import { useToast } from '@/composables'
import { ArrowLeft, Upload, X } from 'lucide-vue-next'
import type { AdminClass } from '@/types'

const route = useRoute()
const router = useRouter()
const { error: toastError } = useToast()

const isEditMode = computed(() => !!route.params.id)
const editId = computed(() => Number(route.params.id) || 0)

// 表单数据
const title = ref('')
const description = ref('')
const location = ref('')
const file = ref<File | null>(null)
const imagePreview = ref('')

// 班级多选数据源（空选 = 所有班级可见）
const { data: classesData } = useQuery({
  queryKey: ['classes'],
  queryFn: () => classesApi.list(),
})
const classes = computed(() => classesData.value ?? [])

/** 班级选项按「届 · 专业」分组，组内保持后端的届/班级名顺序 */
const classGroups = computed(() => {
  const groups = new Map<string, { label: string; items: AdminClass[] }>()
  for (const cls of classes.value) {
    const label = `${cls.cohort_year}届 · ${cls.major}`
    const group = groups.get(label) ?? { label, items: [] }
    group.items.push(cls)
    groups.set(label, group)
  }
  return [...groups.values()].sort((a, b) => b.label.localeCompare(a.label, 'zh-Hans-CN'))
})

const selectedClassIds = ref<number[]>([])

const toggleClassId = (classId: number, checked: boolean) => {
  const ids = selectedClassIds.value
  if (checked) {
    if (!ids.includes(classId)) ids.push(classId)
    return
  }
  const index = ids.indexOf(classId)
  if (index >= 0) ids.splice(index, 1)
}

const toggleAllClassIds = () => {
  const ids = selectedClassIds.value
  if (ids.length === classes.value.length) ids.length = 0
  else ids.splice(0, ids.length, ...classes.value.map((c) => c.id))
}

// 编辑模式：加载现有数据
const { data: existingItem, isPending: loadingItem } = useTeacherLostFoundDetail(
  () => editId.value,
  () => isEditMode.value && editId.value > 0
)

watch(
  () => existingItem.value,
  (item) => {
    if (item && isEditMode.value) {
      title.value = item.title
      description.value = item.description
      location.value = item.location || ''
      selectedClassIds.value = [...(item.class_ids ?? [])]
      if (item.image_url) {
        imagePreview.value = item.image_url
      }
    }
  },
  { immediate: true },
)

// 图片压缩函数
function compressImage(file: File, maxWidth = 1920, quality = 0.8): Promise<File> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const img = new Image()
      img.onload = () => {
        try {
          const canvas = document.createElement('canvas')
          let { width, height } = img
          
          // 如果图片宽度超过最大宽度，按比例缩放
          if (width > maxWidth) {
            height = (height * maxWidth) / width
            width = maxWidth
          }
          
          canvas.width = width
          canvas.height = height
          
          const ctx = canvas.getContext('2d')
          if (!ctx) {
            resolve(file)
            return
          }
          
          ctx.drawImage(img, 0, 0, width, height)
          canvas.toBlob(
            (blob) => {
              if (blob) {
                const compressedFile = new File([blob], file.name.replace(/\.[^.]+$/, '.jpg'), {
                  type: 'image/jpeg',
                  lastModified: Date.now(),
                })
                resolve(compressedFile)
              } else {
                resolve(file)
              }
            },
            'image/jpeg',
            quality
          )
        } catch {
          resolve(file)
        }
      }
      img.onerror = () => resolve(file)
      img.src = e.target?.result as string
    }
    reader.onerror = () => reject(new Error('Failed to read file'))
    reader.readAsDataURL(file)
  })
}

// 图片选择
async function handleFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  const selected = input.files?.[0]
  if (!selected) return

  if (!selected.type.startsWith('image/')) {
    toastError('请选择图片文件')
    return
  }

  if (selected.size > 10 * 1024 * 1024) {
    toastError('图片大小不能超过 10MB')
    return
  }

  // 压缩图片
  try {
    const compressed = await compressImage(selected)
    file.value = compressed
    imagePreview.value = URL.createObjectURL(compressed)
  } catch {
    file.value = selected
    imagePreview.value = URL.createObjectURL(selected)
  }
}

function removeImage() {
  file.value = null
  imagePreview.value = ''
}

// 提交
const { mutateAsync: createItem, isPending: creating } = useCreateLostFoundItem()
const { mutateAsync: updateItem, isPending: updating } = useUpdateLostFoundItem()
const submitting = computed(() => creating.value || updating.value)

async function handleSubmit() {
  if (!title.value.trim()) {
    toastError('请输入标题')
    return
  }
  if (!description.value.trim()) {
    toastError('请输入描述')
    return
  }

  const payload = {
    title: title.value.trim(),
    description: description.value.trim(),
    location: location.value.trim() || undefined,
    file: file.value || undefined,
    class_ids: selectedClassIds.value,
  }

  if (isEditMode.value) {
    await updateItem({ id: editId.value, data: payload })
    router.push({ name: 'TeacherLostFoundDetail', params: { id: editId.value } })
  } else {
    await createItem(payload)
    router.push({ name: 'TeacherLostFound' })
  }
}

function goBack() {
  if (isEditMode.value) {
    router.push({ name: 'TeacherLostFoundDetail', params: { id: editId.value } })
  } else {
    router.push({ name: 'TeacherLostFound' })
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- 返回按钮 -->
    <button
      class="flex items-center gap-1 min-h-[44px] text-sm text-[#737373] hover:text-black transition-colors"
      @click="goBack"
    >
      <ArrowLeft class="h-4 w-4" />
      {{ isEditMode ? '返回详情' : '返回列表' }}
    </button>

    <DataContainer
      v-if="isEditMode"
      :loading="loadingItem"
      :has-data="!!existingItem"
      empty-text="物品不存在"
    >
      <template #default>
        <Card class="bg-white border-[#e5e5e5] p-5">
          <h1 class="text-2xl font-medium text-black mb-6">编辑物品</h1>

          <form class="space-y-5" @submit.prevent="handleSubmit">
            <!-- 标题 -->
            <div>
              <label class="block text-sm font-medium text-black mb-1.5">标题 <span class="text-[#ef4444]">*</span></label>
              <Input v-model="title" placeholder="请输入物品标题" required />
            </div>

            <!-- 描述 -->
            <div>
              <label class="block text-sm font-medium text-black mb-1.5">描述 <span class="text-[#ef4444]">*</span></label>
              <textarea
                v-model="description"
                placeholder="请输入物品描述"
                rows="4"
                class="flex w-full rounded-xl border border-[#e5e5e5] bg-white px-3 py-2 text-sm text-black placeholder:text-[#525252] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#3b82f6]/50 focus-visible:border-black resize-none"
                required
              />
            </div>

            <!-- 地点 -->
            <div>
              <label class="block text-sm font-medium text-black mb-1.5">地点</label>
              <Input v-model="location" placeholder="请输入拾获/丢失地点（选填）" />
            </div>

            <!-- 可见班级 -->
            <div>
              <div class="flex items-center justify-between">
                <label class="block text-sm font-medium text-black">可见班级</label>
                <Button
                  variant="outline"
                  size="sm"
                  data-testid="select-all-classes"
                  @click="toggleAllClassIds"
                >
                  {{ selectedClassIds.length === classes.length && classes.length > 0 ? '清空' : '全选' }}
                </Button>
              </div>
              <div class="mt-1 max-h-56 space-y-3 overflow-y-auto rounded-xl border border-[#e5e5e5] p-3">
                <div
                  v-for="group in classGroups"
                  :key="group.label"
                >
                  <p class="mb-1 text-xs font-medium text-[#a3a3a3]">
                    {{ group.label }}
                  </p>
                  <div class="space-y-1.5">
                    <div
                      v-for="cls in group.items"
                      :key="cls.id"
                      class="flex items-center gap-2"
                    >
                      <Checkbox
                        :checked="selectedClassIds.includes(cls.id)"
                        @update:checked="(checked) => toggleClassId(cls.id, checked)"
                      />
                      <span class="text-sm text-black">{{ cls.name }}</span>
                    </div>
                  </div>
                </div>
                <p
                  v-if="classGroups.length === 0"
                  class="text-xs text-[#a3a3a3]"
                >
                  暂无班级
                </p>
              </div>
              <p
                class="mt-1 text-xs"
                :class="selectedClassIds.length === 0 ? 'text-[#737373]' : 'text-[#a3a3a3]'"
              >
                {{ selectedClassIds.length === 0
                  ? '未选择班级 = 所有班级可见'
                  : `已选 ${selectedClassIds.length} 个班级` }}
              </p>
            </div>

            <!-- 图片上传 -->
            <div>
              <label class="block text-sm font-medium text-black mb-1.5">图片</label>

              <div v-if="imagePreview" class="relative inline-block">
                <img
                  :src="imagePreview"
                  alt="预览"
                  class="h-40 rounded-xl border border-[#e5e5e5] object-cover"
                >
                <button
                  type="button"
                  class="absolute -top-2 -right-2 h-6 w-6 rounded-full bg-[#ef4444] text-white flex items-center justify-center hover:bg-[#dc2626] after:absolute after:-inset-[10px] after:content-['']"
                  @click="removeImage"
                >
                  <X class="h-3.5 w-3.5" />
                </button>
              </div>

              <label
                v-else
                class="flex flex-col items-center justify-center h-40 w-64 rounded-xl border-2 border-dashed border-[#e5e5e5] cursor-pointer hover:border-[#d4d4d4] transition-colors"
              >
                <Upload class="h-8 w-8 text-[#525252] mb-2" />
                <span class="text-sm text-[#737373]">点击上传图片</span>
                <span class="text-xs text-[#525252] mt-1">支持 JPG、PNG，最大 10MB（自动压缩）</span>
                <input type="file" accept="image/*" class="hidden" @change="handleFileSelect">
              </label>
            </div>

            <!-- 提交按钮 -->
            <div class="flex gap-3 pt-2">
              <Button variant="outline" type="button" @click="goBack">取消</Button>
              <Button variant="cta" type="submit" :loading="submitting">
                保存修改
              </Button>
            </div>
          </form>
        </Card>
      </template>
    </DataContainer>

    <!-- 创建模式 -->
    <Card v-else class="bg-white border-[#e5e5e5] p-5">
      <h1 class="text-2xl font-medium text-black mb-6">发布新物品</h1>

      <form class="space-y-5" @submit.prevent="handleSubmit">
        <!-- 标题 -->
        <div>
          <label class="block text-sm font-medium text-black mb-1.5">标题 <span class="text-[#ef4444]">*</span></label>
          <Input v-model="title" placeholder="请输入物品标题" required />
        </div>

        <!-- 描述 -->
        <div>
          <label class="block text-sm font-medium text-black mb-1.5">描述 <span class="text-[#ef4444]">*</span></label>
          <textarea
            v-model="description"
            placeholder="请输入物品描述"
            rows="4"
            class="flex w-full rounded-xl border border-[#e5e5e5] bg-white px-3 py-2 text-sm text-black placeholder:text-[#525252] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#3b82f6]/50 focus-visible:border-black resize-none"
            required
          />
        </div>

        <!-- 地点 -->
        <div>
          <label class="block text-sm font-medium text-black mb-1.5">地点</label>
          <Input v-model="location" placeholder="请输入拾获/丢失地点（选填）" />
        </div>

        <!-- 可见班级 -->
        <div>
          <div class="flex items-center justify-between">
            <label class="block text-sm font-medium text-black">可见班级</label>
            <Button
              variant="outline"
              size="sm"
              data-testid="select-all-classes"
              @click="toggleAllClassIds"
            >
              {{ selectedClassIds.length === classes.length && classes.length > 0 ? '清空' : '全选' }}
            </Button>
          </div>
          <div class="mt-1 max-h-56 space-y-3 overflow-y-auto rounded-xl border border-[#e5e5e5] p-3">
            <div
              v-for="group in classGroups"
              :key="group.label"
            >
              <p class="mb-1 text-xs font-medium text-[#a3a3a3]">
                {{ group.label }}
              </p>
              <div class="space-y-1.5">
                <div
                  v-for="cls in group.items"
                  :key="cls.id"
                  class="flex items-center gap-2"
                >
                  <Checkbox
                    :checked="selectedClassIds.includes(cls.id)"
                    @update:checked="(checked) => toggleClassId(cls.id, checked)"
                  />
                  <span class="text-sm text-black">{{ cls.name }}</span>
                </div>
              </div>
            </div>
            <p
              v-if="classGroups.length === 0"
              class="text-xs text-[#a3a3a3]"
            >
              暂无班级
            </p>
          </div>
          <p
            class="mt-1 text-xs"
            :class="selectedClassIds.length === 0 ? 'text-[#737373]' : 'text-[#a3a3a3]'"
          >
            {{ selectedClassIds.length === 0
              ? '未选择班级 = 所有班级可见'
              : `已选 ${selectedClassIds.length} 个班级` }}
          </p>
        </div>

        <!-- 图片上传 -->
        <div>
          <label class="block text-sm font-medium text-black mb-1.5">图片</label>

          <div v-if="imagePreview" class="relative inline-block">
            <img
              :src="imagePreview"
              alt="预览"
              class="h-40 rounded-xl border border-[#e5e5e5] object-cover"
            >
            <button
              type="button"
              class="absolute -top-2 -right-2 h-6 w-6 rounded-full bg-[#ef4444] text-white flex items-center justify-center hover:bg-[#dc2626] after:absolute after:-inset-[10px] after:content-['']"
              @click="removeImage"
            >
              <X class="h-3.5 w-3.5" />
            </button>
          </div>

          <label
            v-else
            class="flex flex-col items-center justify-center h-40 w-64 rounded-xl border-2 border-dashed border-[#e5e5e5] cursor-pointer hover:border-[#d4d4d4] transition-colors"
          >
            <Upload class="h-8 w-8 text-[#525252] mb-2" />
            <span class="text-sm text-[#737373]">点击上传图片</span>
            <span class="text-xs text-[#525252] mt-1">支持 JPG、PNG，最大 10MB（自动压缩）</span>
            <input type="file" accept="image/*" class="hidden" @change="handleFileSelect">
          </label>
        </div>

        <!-- 提交按钮 -->
        <div class="flex gap-3 pt-2">
          <Button variant="outline" type="button" @click="goBack">取消</Button>
          <Button variant="cta" type="submit" :loading="submitting">
            发布物品
          </Button>
        </div>
      </form>
    </Card>
  </div>
</template>
