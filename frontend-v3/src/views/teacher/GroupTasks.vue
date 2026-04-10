<script setup lang="ts">
import { ref } from 'vue'
import { useCreateGroupTask } from '@/features/group-collaboration'

const { mutate: createTask, isPending: creating } = useCreateGroupTask()
const showCreateDialog = ref(false)
const newTask = ref({ class_name: '', title: '', description: '', dimensions: [''] })

function addDimension() {
  if (newTask.value.dimensions.length < 5) newTask.value.dimensions.push('')
}
function removeDimension(idx: number) {
  newTask.value.dimensions.splice(idx, 1)
}
function handleCreate() {
  const dims = newTask.value.dimensions.filter(Boolean)
  createTask({
    class_name: newTask.value.class_name,
    title: newTask.value.title,
    description: newTask.value.description || undefined,
    dimensions: dims,
  }, { onSuccess: () => { showCreateDialog.value = false } })
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-medium text-black">合作项目</h1>
    <button class="mt-4 rounded-full bg-black px-4 py-2 text-white text-sm font-medium" @click="showCreateDialog = true">创建任务</button>

    <div v-if="showCreateDialog" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div class="w-full max-w-md rounded-xl bg-white p-6">
        <h2 class="text-lg font-medium">创建任务</h2>
        <input v-model="newTask.class_name" placeholder="班级" class="mt-3 w-full rounded-lg border border-[#e5e5e5] px-3 py-2" />
        <input v-model="newTask.title" placeholder="任务名称" class="mt-2 w-full rounded-lg border border-[#e5e5e5] px-3 py-2" />
        <div v-for="(dim, idx) in newTask.dimensions" :key="idx" class="mt-2 flex gap-2">
          <input v-model="newTask.dimensions[idx]" placeholder="维度名称" class="flex-1 rounded-lg border border-[#e5e5e5] px-3 py-2" />
          <button v-if="newTask.dimensions.length > 1" class="text-red-500 text-sm" @click="removeDimension(idx)">删除</button>
        </div>
        <button v-if="newTask.dimensions.length < 5" class="mt-2 text-sm text-[#737373]" @click="addDimension">+ 添加维度</button>
        <div class="mt-4 flex gap-2">
          <button class="flex-1 rounded-full bg-black py-2 text-white text-sm font-medium" :disabled="creating" @click="handleCreate">确认</button>
          <button class="flex-1 rounded-full border border-[#d4d4d4] py-2 text-sm font-medium" @click="showCreateDialog = false">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>
