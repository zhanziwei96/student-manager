<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { Card, Button, Badge, Input, Select, Dialog, Checkbox } from '@/components/ui'
import { Plus, Loader2, Pencil, Users, Presentation } from 'lucide-vue-next'
import { offeringsApi } from '@/api/offerings'
import { classesApi } from '@/api/classes'
import { coursesApi } from '@/api/courses'
import { semestersApi } from '@/api/semesters'
import { usersApi } from '@/api/users'
import { useToast } from '@/composables/useToast'
import { getErrorMessage } from '@/lib/error'
import type { AdminClass, CourseOffering, EnrollmentRow } from '@/types'

const { showToast } = useToast()
const queryClient = useQueryClient()

// 基础数据：课程/学期/教师
const { data: coursesData } = useQuery({
  queryKey: ['courses'],
  queryFn: () => coursesApi.list(),
})
const courses = computed(() => coursesData.value ?? [])

const { data: semestersData } = useQuery({
  queryKey: ['semesters'],
  queryFn: () => semestersApi.list(),
})
const semesters = computed(() => semestersData.value ?? [])

const { data: teachersData } = useQuery({
  queryKey: ['teachers'],
  queryFn: () => usersApi.getTeachers(),
})
const teachers = computed(() => teachersData.value ?? [])

// 班级多选数据源（空选 = 全部班级通配）
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

const toggleClassId = (ids: number[], classId: number, checked: boolean) => {
  if (checked) {
    if (!ids.includes(classId)) ids.push(classId)
    return
  }
  const index = ids.indexOf(classId)
  if (index >= 0) ids.splice(index, 1)
}

const toggleAllClassIds = (ids: number[]) => {
  if (ids.length === classes.value.length) ids.length = 0
  else ids.splice(0, ids.length, ...classes.value.map((c) => c.id))
}

// 学期筛选（缺省当前学期）
const { data: currentSemester } = useQuery({
  queryKey: ['semesters', 'current'],
  queryFn: () => semestersApi.list().then((list) => list.find((s) => s.is_current) ?? null),
})
const semesterFilter = ref<number | ''>('')
const effectiveSemesterId = computed(() =>
  semesterFilter.value === '' ? (currentSemester.value?.id ?? undefined) : semesterFilter.value,
)

// 教学班列表
const { data: offeringsData, isPending } = useQuery({
  queryKey: ['offerings', effectiveSemesterId],
  queryFn: () => offeringsApi.list(effectiveSemesterId.value),
})
const offerings = computed(() => offeringsData.value ?? [])

const invalidateOfferings = () => queryClient.invalidateQueries({ queryKey: ['offerings'] })

// 课程/学期显示名映射
const courseName = (courseId: number) => courses.value.find((c) => c.id === courseId)?.name ?? `课程#${courseId}`
const semesterLabel = (semesterId: number) => semesters.value.find((s) => s.id === semesterId)?.label ?? `学期#${semesterId}`

// 创建
const showCreateDialog = ref(false)
const createForm = ref({ course_id: '', semester_id: '', teacher_id: '', class_ids: [] as number[], capacity: '' })
const createError = ref('')

const openCreateDialog = () => {
  createForm.value = {
    course_id: '',
    semester_id: effectiveSemesterId.value ? String(effectiveSemesterId.value) : '',
    teacher_id: '',
    class_ids: [],
    capacity: '',
  }
  createError.value = ''
  showCreateDialog.value = true
}

const { mutateAsync: createOffering, isPending: isCreating } = useMutation({
  mutationFn: () => offeringsApi.create({
    course_id: Number(createForm.value.course_id),
    semester_id: Number(createForm.value.semester_id),
    teacher_id: createForm.value.teacher_id ? Number(createForm.value.teacher_id) : null,
    class_ids: createForm.value.class_ids,  // 空数组 = 全部班级
    capacity: createForm.value.capacity ? Number(createForm.value.capacity) : null,
  }),
  onSuccess: () => {
    invalidateOfferings()
    showToast('教学班创建成功', 'success')
    showCreateDialog.value = false
  },
  onError: (error) => showToast(getErrorMessage(error) || '创建失败', 'error'),
})

const handleCreate = async () => {
  if (!createForm.value.course_id) {
    createError.value = '请选择课程'
    return
  }
  if (!createForm.value.semester_id) {
    createError.value = '请选择学期'
    return
  }
  // 面向范围不校验：不选班级 = 全部班级
  await createOffering()
}

// 编辑
const showEditDialog = ref(false)
const editingOffering = ref<CourseOffering | null>(null)
const editForm = ref({ teacher_id: '', class_ids: [] as number[], capacity: '' })

const openEditDialog = (offering: CourseOffering) => {
  editingOffering.value = offering
  editForm.value = {
    teacher_id: offering.teacher_id ? String(offering.teacher_id) : '',
    class_ids: [...(offering.class_ids ?? [])],
    capacity: offering.capacity ? String(offering.capacity) : '',
  }
  showEditDialog.value = true
}

const { mutateAsync: updateOffering, isPending: isUpdating } = useMutation({
  mutationFn: () => offeringsApi.update(editingOffering.value!.id, {
    teacher_id: editForm.value.teacher_id ? Number(editForm.value.teacher_id) : null,
    class_ids: editForm.value.class_ids,  // 空数组 = 全部班级（整体替换关联行）
    capacity: editForm.value.capacity ? Number(editForm.value.capacity) : null,
  }),
  onSuccess: () => {
    invalidateOfferings()
    showToast('教学班更新成功', 'success')
    showEditDialog.value = false
  },
  onError: (error) => showToast(getErrorMessage(error) || '更新失败', 'error'),
})

// 名单管理
const showRosterDialog = ref(false)
const rosterOffering = ref<CourseOffering | null>(null)
const importText = ref('')

const { data: rosterData, refetch: refetchRoster } = useQuery({
  queryKey: ['offerings', 'enrollments', () => rosterOffering.value?.id],
  queryFn: () => offeringsApi.listEnrollments(rosterOffering.value!.id),
  enabled: () => rosterOffering.value !== null,
})
const roster = computed(() => rosterData.value ?? [])

const openRosterDialog = (offering: CourseOffering) => {
  rosterOffering.value = offering
  importText.value = ''
  showRosterDialog.value = true
}

// 按班级加入名单（该班全部在读学生）
const rosterClassId = ref('')
const rosterClassOptions = computed(() => [
  { value: '', label: '选择班级' },
  ...classes.value.map((c) => ({ value: String(c.id), label: c.display_name })),
])

const { mutateAsync: enrollByClass, isPending: isEnrollingByClass } = useMutation({
  mutationFn: () => offeringsApi.enrollByClass(rosterOffering.value!.id, [Number(rosterClassId.value)]),
  onSuccess: (result) => {
    refetchRoster()
    showToast(`按班级加入 ${result.imported} 人，跳过 ${result.skipped} 人`, 'success')
    rosterClassId.value = ''
  },
  onError: (error) => showToast(getErrorMessage(error) || '加入失败', 'error'),
})

const { mutateAsync: importEnrollments, isPending: isImporting } = useMutation({
  mutationFn: () => offeringsApi.importEnrollments(
    rosterOffering.value!.id,
    importText.value.split('\n').map((s) => s.trim()).filter(Boolean),
  ),
  onSuccess: (result) => {
    refetchRoster()
    showToast(`导入 ${result.imported} 人，跳过 ${result.skipped} 人`, 'success')
    importText.value = ''
  },
  onError: (error) => showToast(getErrorMessage(error) || '导入失败', 'error'),
})

const { mutateAsync: dropEnrollment, isPending: isDropping } = useMutation({
  mutationFn: (row: EnrollmentRow) => offeringsApi.dropEnrollment(row.enrollment_id),
  onSuccess: () => {
    refetchRoster()
    showToast('已退课', 'success')
  },
  onError: (error) => showToast(getErrorMessage(error) || '退课失败', 'error'),
})
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-5">
      <div>
        <h1 class="text-2xl font-medium text-black">
          教学班管理
        </h1>
        <p class="text-[#737373]">
          按学期开课、安排教师并管理选课名单
        </p>
      </div>
      <Button @click="openCreateDialog">
        <Plus class="mr-2 h-4 w-4" />
        创建教学班
      </Button>
    </div>

    <!-- 学期筛选 -->
    <div class="mb-5 w-full sm:w-48">
      <Select
        v-model="semesterFilter"
        :options="[
          { value: '', label: '当前学期' },
          ...semesters.map((s) => ({ value: s.id, label: s.label })),
        ]"
        placeholder="选择学期"
      />
    </div>

    <!-- 教学班列表 -->
    <Card class="overflow-hidden p-0">
      <div
        v-if="isPending"
        class="flex h-64 items-center justify-center"
      >
        <Loader2 class="h-8 w-8 animate-spin text-primary" />
      </div>

      <table
        v-else-if="offerings.length > 0"
        class="w-full text-sm"
      >
        <thead class="bg-[#fafafa] text-[#737373] border-b border-[#e5e5e5]">
          <tr>
            <th class="px-4 py-3 text-left font-medium">
              课程
            </th>
            <th class="px-4 py-3 text-left font-medium">
              学期
            </th>
            <th class="px-4 py-3 text-left font-medium">
              教师
            </th>
            <th class="px-4 py-3 text-left font-medium">
              面向范围
            </th>
            <th class="px-4 py-3 text-right font-medium">
              容量
            </th>
            <th class="px-4 py-3 text-left font-medium">
              状态
            </th>
            <th class="px-4 py-3 text-right font-medium">
              操作
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-[#e5e5e5]">
          <tr
            v-for="offering in offerings"
            :key="offering.id"
            class="text-[#737373] hover:bg-[#fafafa] transition-colors"
          >
            <td class="px-4 py-3 font-medium text-black">
              {{ courseName(offering.course_id) }}
            </td>
            <td class="px-4 py-3">
              {{ semesterLabel(offering.semester_id) }}
            </td>
            <td class="px-4 py-3">
              {{ offering.teacher_name || '待安排' }}
            </td>
            <td class="px-4 py-3">
              {{ offering.class_scope }}
            </td>
            <td class="px-4 py-3 text-right">
              {{ offering.capacity ?? '不限' }}
            </td>
            <td class="px-4 py-3">
              <Badge :variant="offering.status === 'active' ? 'default' : 'secondary'">
                {{ offering.status === 'active' ? '开课中' : '已结课' }}
              </Badge>
            </td>
            <td class="px-4 py-3">
              <div class="flex justify-end gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  class="hover:bg-[#fafafa]"
                  @click="openRosterDialog(offering)"
                >
                  <Users class="mr-1 h-4 w-4" />
                  名单
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  class="hover:bg-[#fafafa]"
                  data-testid="edit-offering-btn"
                  @click="openEditDialog(offering)"
                >
                  <Pencil class="h-4 w-4" />
                </Button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Empty state -->
      <div
        v-else
        class="flex h-64 flex-col items-center justify-center text-[#737373]"
      >
        <Presentation class="mb-4 h-12 w-12 opacity-50" />
        <p>当前学期暂无教学班</p>
        <p class="mt-1 text-sm text-[#a3a3a3]">
          点击右上角按钮创建教学班
        </p>
      </div>
    </Card>

    <!-- Create Dialog -->
    <Dialog
      v-model:open="showCreateDialog"
      title="创建教学班"
      description="一门课程在一个学期的开课安排"
    >
      <div class="space-y-4">
        <div>
          <label class="text-sm text-[#737373]">课程</label>
          <Select
            v-model="createForm.course_id"
            :options="courses.map((c) => ({ value: c.id, label: `${c.name}（${c.code}）` }))"
            placeholder="选择课程"
            class="mt-1"
          />
        </div>
        <div>
          <label class="text-sm text-[#737373]">学期</label>
          <Select
            v-model="createForm.semester_id"
            :options="semesters.map((s) => ({ value: s.id, label: s.label }))"
            placeholder="选择学期"
            class="mt-1"
          />
        </div>
        <div>
          <label class="text-sm text-[#737373]">教师</label>
          <Select
            v-model="createForm.teacher_id"
            :options="[{ value: '', label: '待安排' }, ...teachers.map((t) => ({ value: t.id, label: t.name }))]"
            placeholder="选择教师"
            class="mt-1"
          />
        </div>
        <div>
          <div class="flex items-center justify-between">
            <label class="text-sm text-[#737373]">面向范围</label>
            <Button
              variant="outline"
              size="sm"
              data-testid="create-select-all-classes"
              @click="toggleAllClassIds(createForm.class_ids)"
            >
              {{ createForm.class_ids.length === classes.length && classes.length > 0 ? '清空' : '全选' }}
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
                    :checked="createForm.class_ids.includes(cls.id)"
                    @update:checked="(checked) => toggleClassId(createForm.class_ids, cls.id, checked)"
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
            :class="createForm.class_ids.length === 0 ? 'text-[#737373]' : 'text-[#a3a3a3]'"
          >
            {{ createForm.class_ids.length === 0
              ? '未选择班级 = 面向全部班级（通配）'
              : `已选 ${createForm.class_ids.length} 个班级` }}
          </p>
        </div>
        <div>
          <label class="text-sm text-[#737373]">容量</label>
          <Input
            v-model="createForm.capacity"
            type="number"
            min="1"
            placeholder="选课人数上限（可留空）"
            class="mt-1"
          />
        </div>
        <p
          v-if="createError"
          class="text-sm text-red-400"
        >
          {{ createError }}
        </p>
      </div>
      <template #footer>
        <Button
          variant="outline"
          @click="showCreateDialog = false"
        >
          取消
        </Button>
        <Button
          :disabled="isCreating"
          @click="handleCreate"
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
      title="编辑教学班"
      :description="`${courseName(editingOffering?.course_id ?? 0)} · ${semesterLabel(editingOffering?.semester_id ?? 0)}`"
    >
      <div class="space-y-4">
        <div>
          <label class="text-sm text-[#737373]">教师</label>
          <Select
            v-model="editForm.teacher_id"
            :options="[{ value: '', label: '待安排' }, ...teachers.map((t) => ({ value: t.id, label: t.name }))]"
            placeholder="选择教师"
            class="mt-1"
          />
        </div>
        <div>
          <div class="flex items-center justify-between">
            <label class="text-sm text-[#737373]">面向范围</label>
            <Button
              variant="outline"
              size="sm"
              data-testid="edit-select-all-classes"
              @click="toggleAllClassIds(editForm.class_ids)"
            >
              {{ editForm.class_ids.length === classes.length && classes.length > 0 ? '清空' : '全选' }}
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
                    :checked="editForm.class_ids.includes(cls.id)"
                    @update:checked="(checked) => toggleClassId(editForm.class_ids, cls.id, checked)"
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
            :class="editForm.class_ids.length === 0 ? 'text-[#737373]' : 'text-[#a3a3a3]'"
          >
            {{ editForm.class_ids.length === 0
              ? '未选择班级 = 面向全部班级（通配）'
              : `已选 ${editForm.class_ids.length} 个班级` }}
          </p>
        </div>
        <div>
          <label class="text-sm text-[#737373]">容量</label>
          <Input
            v-model="editForm.capacity"
            type="number"
            min="1"
            placeholder="选课人数上限（可留空）"
            class="mt-1"
          />
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
          @click="updateOffering()"
        >
          <Loader2
            v-if="isUpdating"
            class="mr-2 h-4 w-4 animate-spin"
          />
          保存
        </Button>
      </template>
    </Dialog>

    <!-- Roster Dialog -->
    <Dialog
      v-model:open="showRosterDialog"
      :title="rosterOffering ? `${courseName(rosterOffering.course_id)} · 选课名单` : '选课名单'"
      description="批量导入学号（每行一个），退课保留历史记录"
    >
      <div class="space-y-4">
        <div>
          <label class="text-sm text-[#737373]">按班级加入名单</label>
          <div class="mt-1 flex gap-2">
            <Select
              v-model="rosterClassId"
              :options="rosterClassOptions"
              placeholder="选择班级"
              class="flex-1"
            />
            <Button
              variant="outline"
              :disabled="!rosterClassId || isEnrollingByClass"
              data-testid="enroll-by-class"
              @click="enrollByClass()"
            >
              <Loader2
                v-if="isEnrollingByClass"
                class="mr-1 h-4 w-4 animate-spin"
              />
              加入名单
            </Button>
          </div>
          <p class="mt-1 text-xs text-[#a3a3a3]">
            加入所选班级的全部在读学生（已在名单中的会保留）
          </p>
        </div>

        <div>
          <label class="text-sm text-[#737373]">批量导入学号</label>
          <textarea
            v-model="importText"
            rows="3"
            placeholder="每行一个学号&#10;如：&#10;20260001&#10;20260002"
            class="mt-1 w-full rounded-xl border border-[#e5e5e5] bg-white px-3 py-2 text-sm text-black placeholder:text-[#a3a3a3] focus:outline-none focus:ring-2 focus:ring-[#3b82f6]/50 focus:border-black"
          />
          <Button
            variant="outline"
            size="sm"
            class="mt-2"
            :disabled="isImporting || !importText.trim()"
            @click="importEnrollments()"
          >
            <Loader2
              v-if="isImporting"
              class="mr-1 h-4 w-4 animate-spin"
            />
            导入
          </Button>
        </div>

        <!-- 名单列表 -->
        <div
          v-if="roster.length === 0"
          class="flex h-32 items-center justify-center text-sm text-[#a3a3a3]"
        >
          暂无选课学生
        </div>
        <div v-else class="max-h-72 overflow-y-auto rounded-xl border border-[#e5e5e5]">
          <table class="w-full text-sm">
            <thead class="bg-[#fafafa] text-[#737373] border-b border-[#e5e5e5]">
              <tr>
                <th class="px-3 py-2 text-left font-medium">
                  学号
                </th>
                <th class="px-3 py-2 text-left font-medium">
                  姓名
                </th>
                <th class="px-3 py-2 text-left font-medium">
                  班级
                </th>
                <th class="px-3 py-2 text-right font-medium">
                  平时成绩
                </th>
                <th class="px-3 py-2 text-right font-medium">
                  期末成绩
                </th>
                <th class="px-3 py-2 text-right font-medium">
                  操作
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-[#e5e5e5]">
              <tr
                v-for="row in roster"
                :key="row.enrollment_id"
                class="text-[#737373]"
              >
                <td class="px-3 py-2 font-mono text-xs">
                  {{ row.student_id }}
                </td>
                <td class="px-3 py-2 font-medium text-black">
                  {{ row.name }}
                </td>
                <td class="px-3 py-2">
                  {{ row.class_name }}
                </td>
                <td class="px-3 py-2 text-right">
                  {{ row.score }}
                </td>
                <td class="px-3 py-2 text-right">
                  {{ row.final_score ?? '—' }}
                </td>
                <td class="px-3 py-2 text-right">
                  <Button
                    variant="outline"
                    size="sm"
                    :disabled="isDropping"
                    class="hover:bg-red-500/10"
                    @click="dropEnrollment(row)"
                  >
                    退课
                  </Button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <template #footer>
        <Button
          variant="outline"
          @click="showRosterDialog = false"
        >
          关闭
        </Button>
      </template>
    </Dialog>
  </div>
</template>
