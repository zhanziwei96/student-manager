<script setup lang="ts">
import { computed, ref } from 'vue'
import { Dialog, Button, Badge } from '@/components/ui'
import { Download, Loader2, Upload } from 'lucide-vue-next'
import { studentsApi, type StudentImportResult } from '@/api/students'
import { useToast } from '@/composables/useToast'
import { getErrorMessage } from '@/lib/error'

const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'imported'): void
}>()

const { showToast } = useToast()

const selectedFile = ref<File | null>(null)
const result = ref<StudentImportResult | null>(null)
const isImporting = ref(false)
const isDownloading = ref(false)

const hasIssues = computed(() =>
  !!result.value && (result.value.errors.length > 0 || result.value.skipped > 0)
)

const reset = () => {
  selectedFile.value = null
  result.value = null
}

const close = () => {
  emit('update:open', false)
  reset()
}

const onFileChange = (event: Event) => {
  const files = (event.target as HTMLInputElement).files
  selectedFile.value = files && files.length > 0 ? files[0] : null
  result.value = null
}

const downloadTemplate = async () => {
  isDownloading.value = true
  try {
    const blob = await studentsApi.downloadImportTemplate()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = '学生导入模板.xlsx'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    showToast(getErrorMessage(error) || '模板下载失败', 'error')
  } finally {
    isDownloading.value = false
  }
}

const handleImport = async () => {
  if (!selectedFile.value) return
  isImporting.value = true
  try {
    const data = await studentsApi.import(selectedFile.value)
    result.value = data
    if (data.imported > 0) {
      emit('imported')
      showToast(`成功导入 ${data.imported} 名学生`, 'success')
    } else {
      showToast('没有导入任何学生，请检查文件内容', 'warning')
    }
  } catch (error) {
    showToast(getErrorMessage(error) || '导入失败', 'error')
  } finally {
    isImporting.value = false
  }
}
</script>

<template>
  <Dialog
    :open="props.open"
    title="批量导入学生"
    description="按模板填写后上传 Excel（.xlsx），一次可导入多名学生"
    @update:open="close"
  >
    <div class="space-y-4">
      <!-- 说明 -->
      <div class="rounded-lg bg-[#fafafa] px-4 py-3 text-sm text-[#737373]">
        <p class="mb-2 font-medium text-black">
          导入说明
        </p>
        <ul class="list-disc space-y-1 pl-4">
          <li>列：学号、姓名、所属届、专业、班级名</li>
          <li>班级不存在时，按「所属届 + 专业 + 班级名」自动创建</li>
          <li>学号已存在的学生会被跳过，不会修改既有数据</li>
          <li>初始密码默认为学号</li>
        </ul>
      </div>

      <!-- 模板下载 -->
      <Button
        variant="outline"
        data-testid="download-template"
        :disabled="isDownloading"
        @click="downloadTemplate"
      >
        <Loader2
          v-if="isDownloading"
          class="mr-2 h-4 w-4 animate-spin"
        />
        <Download
          v-else
          class="mr-2 h-4 w-4"
        />
        下载导入模板
      </Button>

      <!-- 选择文件 -->
      <div>
        <label class="text-sm text-[#737373]">选择文件</label>
        <input
          data-testid="import-file"
          type="file"
          accept=".xlsx"
          class="mt-1 w-full rounded-lg border border-[#e5e5e5] bg-[#f5f5f5] px-3 py-2 text-sm text-black file:mr-4 file:rounded-md file:border-0 file:bg-black file:px-3 file:py-1 file:text-sm file:text-white hover:file:bg-black/80"
          @change="onFileChange"
        >
      </div>

      <!-- 导入结果 -->
      <div
        v-if="result"
        class="space-y-2 rounded-lg border border-[#e5e5e5] px-4 py-3 text-sm"
      >
        <div class="flex items-center gap-3">
          <Badge variant="default">
            成功 {{ result.imported }}
          </Badge>
          <Badge
            v-if="result.skipped > 0"
            variant="secondary"
          >
            跳过 {{ result.skipped }}
          </Badge>
          <Badge
            v-if="result.errors.length > 0"
            variant="error"
          >
            失败 {{ result.errors.length }}
          </Badge>
        </div>
        <ul
          v-if="hasIssues"
          class="max-h-40 space-y-1 overflow-y-auto text-[#737373]"
        >
          <li
            v-for="line in [...result.errors, ...result.skipped_rows]"
            :key="line"
          >
            {{ line }}
          </li>
        </ul>
      </div>
    </div>

    <template #footer>
      <Button
        variant="outline"
        @click="close"
      >
        关闭
      </Button>
      <Button
        data-testid="submit-import"
        :disabled="!selectedFile || isImporting"
        @click="handleImport"
      >
        <Loader2
          v-if="isImporting"
          class="mr-2 h-4 w-4 animate-spin"
        />
        <Upload
          v-else
          class="mr-2 h-4 w-4"
        />
        导入
      </Button>
    </template>
  </Dialog>
</template>
