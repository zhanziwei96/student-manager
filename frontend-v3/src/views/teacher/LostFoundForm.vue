<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Card, Button, Input, DataContainer } from '@/components/ui'
import {
  useCreateLostFoundItem,
  useUpdateLostFoundItem,
  useTeacherLostFoundDetail,
} from '@/composables/useLostFound'
import { useToast } from '@/composables'
import { ArrowLeft, Upload, X } from 'lucide-vue-next'

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

// 编辑模式：加载现有数据
const { data: existingItem, isPending: loadingItem } = useTeacherLostFoundDetail(() => editId.value)

watch(
  () => existingItem.value,
  (item) => {
    if (item && isEditMode.value) {
      title.value = item.title
      description.value = item.description
      location.value = item.location || ''
      if (item.image_url) {
        imagePreview.value = item.image_url
      }
    }
  },
  { immediate: true },
)

// 图片选择
function handleFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  const selected = input.files?.[0]
  if (!selected) return

  if (!selected.type.startsWith('image/')) {
    toastError('请选择图片文件')
    return
  }

  if (selected.size > 5 * 1024 * 1024) {
    toastError('图片大小不能超过 5MB')
    return
  }

  file.value = selected
  imagePreview.value = URL.createObjectURL(selected)
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
      class="flex items-center gap-1 text-sm text-[#737373] hover:text-black transition-colors"
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
                class="flex w-full rounded-xl border border-[#e5e5e5] bg-white px-3 py-2 text-sm text-black placeholder:text-[#a3a3a3] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#3b82f6]/50 focus-visible:border-black resize-none"
                required
              />
            </div>

            <!-- 地点 -->
            <div>
              <label class="block text-sm font-medium text-black mb-1.5">地点</label>
              <Input v-model="location" placeholder="请输入拾获/丢失地点（选填）" />
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
                  class="absolute -top-2 -right-2 h-6 w-6 rounded-full bg-[#ef4444] text-white flex items-center justify-center hover:bg-[#dc2626]"
                  @click="removeImage"
                >
                  <X class="h-3.5 w-3.5" />
                </button>
              </div>

              <label
                v-else
                class="flex flex-col items-center justify-center h-40 w-64 rounded-xl border-2 border-dashed border-[#e5e5e5] cursor-pointer hover:border-[#d4d4d4] transition-colors"
              >
                <Upload class="h-8 w-8 text-[#a3a3a3] mb-2" />
                <span class="text-sm text-[#737373]">点击上传图片</span>
                <span class="text-xs text-[#a3a3a3] mt-1">支持 JPG、PNG，最大 5MB</span>
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
            class="flex w-full rounded-xl border border-[#e5e5e5] bg-white px-3 py-2 text-sm text-black placeholder:text-[#a3a3a3] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#3b82f6]/50 focus-visible:border-black resize-none"
            required
          />
        </div>

        <!-- 地点 -->
        <div>
          <label class="block text-sm font-medium text-black mb-1.5">地点</label>
          <Input v-model="location" placeholder="请输入拾获/丢失地点（选填）" />
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
              class="absolute -top-2 -right-2 h-6 w-6 rounded-full bg-[#ef4444] text-white flex items-center justify-center hover:bg-[#dc2626]"
              @click="removeImage"
            >
              <X class="h-3.5 w-3.5" />
            </button>
          </div>

          <label
            v-else
            class="flex flex-col items-center justify-center h-40 w-64 rounded-xl border-2 border-dashed border-[#e5e5e5] cursor-pointer hover:border-[#d4d4d4] transition-colors"
          >
            <Upload class="h-8 w-8 text-[#a3a3a3] mb-2" />
            <span class="text-sm text-[#737373]">点击上传图片</span>
            <span class="text-xs text-[#a3a3a3] mt-1">支持 JPG、PNG，最大 5MB</span>
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
