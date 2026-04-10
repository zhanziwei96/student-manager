# 修改密码功能 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为教师和学生角色添加修改密码的 UI 入口和对话框组件。

**Architecture:** 在 DashboardLayout 侧边栏用户头像区域添加下拉菜单（修改密码/退出登录），新建 ChangePasswordDialog 模态对话框组件，使用 useMutation 调用已有的 authApi.changePassword。移动端在 MobileDrawer 中添加同样的入口。

**Tech Stack:** Vue 3.5, TypeScript, TanStack Vue Query (useMutation), lucide-vue-next, @vueuse/core (onClickOutside)

---

### Task 1: 创建 ChangePasswordDialog 组件

**Files:**
- Create: `frontend-v3/src/components/ui/ChangePasswordDialog.vue`

- [ ] **Step 1: 创建 ChangePasswordDialog.vue 组件**

```vue
<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useMutation } from '@tanstack/vue-query'
import { authApi } from '@/api'
import { useToast } from '@/composables'
import { getErrorMessage } from '@/lib/error'
import { Dialog, Input, Label, Button } from '@/components/ui'
import { KeyRound } from 'lucide-vue-next'

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
```

- [ ] **Step 2: 验证组件文件无语法错误**

Run: `cd frontend-v3 && npx vue-tsc --noEmit --pretty 2>&1 | head -30`

Expected: 无与 ChangePasswordDialog 相关的错误（可能存在已有的不相关错误）

- [ ] **Step 3: Commit**

```bash
git add frontend-v3/src/components/ui/ChangePasswordDialog.vue
git commit -m "feat(ui): 添加 ChangePasswordDialog 修改密码对话框组件"
```

---

### Task 2: 导出 ChangePasswordDialog 并更新导出测试

**Files:**
- Modify: `frontend-v3/src/components/ui/index.ts`
- Modify: `frontend-v3/test/components/ui-exports.spec.ts`

- [ ] **Step 1: 在 index.ts 添加导出**

在 `frontend-v3/src/components/ui/index.ts` 末尾添加：

```ts
export { default as ChangePasswordDialog } from './ChangePasswordDialog.vue'
```

- [ ] **Step 2: 更新 ui-exports.spec.ts 测试**

在 `frontend-v3/test/components/ui-exports.spec.ts` 中更新两个测试：

在第一个测试 `should export all required components` 中添加：
```ts
expect(UI.ChangePasswordDialog).toBeDefined()
```

在第二个测试的 `componentNames` 数组中添加 `'ChangePasswordDialog'`：
```ts
const componentNames = ['Button', 'Checkbox', 'Dialog', 'Input', 'Label', 'Card', 'Badge', 'Select', 'Toast', 'DataContainer', 'SearchableSelect', 'StatCard', 'ChangePasswordDialog']
```

- [ ] **Step 3: 运行导出测试**

Run: `cd frontend-v3 && pnpm test:run -- test/components/ui-exports.spec.ts`

Expected: PASS（所有导出测试通过）

- [ ] **Step 4: Commit**

```bash
git add frontend-v3/src/components/ui/index.ts frontend-v3/test/components/ui-exports.spec.ts
git commit -m "feat(ui): 导出 ChangePasswordDialog 组件并更新测试"
```

---

### Task 3: DashboardLayout 添加用户头像下拉菜单

**Files:**
- Modify: `frontend-v3/src/layouts/DashboardLayout.vue`

DashboardLayout 当前状态：
- 第 95-109 行：侧边栏用户信息区域（静态展示，无交互）
- 第 129-139 行：底部退出登录按钮

需要：
1. 用户头像区域变为可点击（点击展开下拉菜单）
2. 下拉菜单包含"修改密码"和"退出登录"
3. 移除底部独立的退出登录按钮
4. 点击外部关闭下拉菜单

- [ ] **Step 1: 修改 DashboardLayout.vue**

完整替换 `<script setup>` 和 `<template>` 内容：

**Script setup 部分** — 添加以下导入和逻辑：

在现有 import 行后添加：
```ts
import { KeyRound } from 'lucide-vue-next'
import { onClickOutside } from '@vueuse/core'
import { ChangePasswordDialog } from '@/components/ui'
```

添加新的 ref：
```ts
const showDropdown = ref(false)
const showChangePassword = ref(false)
const dropdownRef = ref<HTMLElement | null>(null)
```

在 `handleLogout` 函数后添加：
```ts
// 点击外部关闭下拉菜单
onClickOutside(dropdownRef, () => {
  showDropdown.value = false
})

const handleChangePassword = () => {
  showDropdown.value = false
  showChangePassword.value = true
}
```

**Template 部分** — 替换用户信息区域（第 94-109 行）为可点击下拉菜单：

```html
      <!-- User info - clickable dropdown -->
      <div ref="dropdownRef" class="relative border-b border-[#e5e5e5] p-4">
        <button
          class="flex w-full items-center gap-3 rounded-xl p-1 hover:bg-[#fafafa]"
          @click="showDropdown = !showDropdown"
        >
          <div class="flex h-10 w-10 items-center justify-center rounded-full bg-[#fafafa]">
            <User class="h-5 w-5 text-[#737373]" />
          </div>
          <div class="flex-1 min-w-0 text-left">
            <p class="truncate text-sm font-medium text-black">
              {{ user?.name }}
            </p>
            <p class="truncate text-xs text-[#a3a3a3] capitalize">
              {{ user?.role === 'admin' ? '管理员' : user?.role === 'teacher' ? '教师' : '学生' }}
            </p>
          </div>
        </button>

        <!-- Dropdown menu -->
        <div
          v-if="showDropdown"
          class="absolute left-4 right-4 top-full mt-1 rounded-xl border border-[#e5e5e5] bg-white py-1 z-10"
        >
          <button
            class="flex w-full items-center gap-3 px-4 py-2.5 text-sm font-medium text-[#737373] hover:bg-[#fafafa] hover:text-black"
            @click="handleChangePassword"
          >
            <KeyRound class="h-4 w-4" />
            修改密码
          </button>
          <button
            class="flex w-full items-center gap-3 px-4 py-2.5 text-sm font-medium text-[#737373] hover:bg-[#fafafa] hover:text-black"
            @click="handleLogout"
          >
            <LogOut class="h-4 w-4" />
            退出登录
          </button>
        </div>
      </div>
```

移除底部退出登录区域（第 129-139 行），替换为空：
```html
      <!-- Bottom spacer -->
      <div class="absolute bottom-0 left-0 right-0 p-4">
      </div>
```

在模板末尾（`<ToastContainer />` 后）添加对话框：
```html
    <!-- Change Password Dialog -->
    <ChangePasswordDialog v-model:open="showChangePassword" />
```

- [ ] **Step 2: 验证编译通过**

Run: `cd frontend-v3 && npx vue-tsc --noEmit --pretty 2>&1 | head -30`

Expected: 无与 DashboardLayout 相关的错误

- [ ] **Step 3: Commit**

```bash
git add frontend-v3/src/layouts/DashboardLayout.vue
git commit -m "feat(layout): DashboardLayout 侧边栏添加用户头像下拉菜单"
```

---

### Task 4: MobileDrawer 添加修改密码入口

**Files:**
- Modify: `frontend-v3/src/components/ui/MobileDrawer.vue`

MobileDrawer 当前状态：
- 第 117-131 行：用户信息区域（静态展示）
- 第 152-164 行：底部退出登录按钮

需要：
1. 在用户信息下方添加"修改密码"菜单项
2. 保留退出登录按钮
3. 需要接收 showChangePassword 状态或 emit 事件（由 DashboardLayout 管理 ChangePasswordDialog）

由于 MobileDrawer 由 DashboardLayout 管理（`v-model:open`），最佳方式是 emit 事件让父组件处理。

- [ ] **Step 1: 修改 MobileDrawer.vue**

在 `<script setup>` 部分添加导入和 emit：

在现有 import 后添加：
```ts
import { KeyRound } from 'lucide-vue-next'
```

添加 emit（在现有 emits 声明中追加）：
```ts
const emit = defineEmits<{
  'update:open': [value: boolean]
  'changePassword': []
}>()
```

添加处理函数：
```ts
const handleChangePassword = () => {
  emit('changePassword')
  handleClose()
}
```

在导航列表后（第 150 行 `</nav>` 后），底部按钮前添加修改密码按钮：
```html
      <!-- Change password -->
      <div class="px-2 pt-2 border-t border-[#e5e5e5] mx-2">
        <button
          class="flex w-full items-center gap-4 rounded-full px-4 py-3.5 text-base font-medium text-[#737373] hover:bg-[#fafafa] hover:text-black"
          @click="handleChangePassword"
        >
          <KeyRound class="h-6 w-6" />
          修改密码
        </button>
      </div>
```

- [ ] **Step 2: 在 DashboardLayout.vue 中处理 MobileDrawer 的 changePassword 事件**

在 DashboardLayout.vue 的 MobileDrawer 使用处更新：
```html
<MobileDrawer v-model:open="showMobileMenu" @change-password="showChangePassword = true" />
```

- [ ] **Step 3: 验证编译通过**

Run: `cd frontend-v3 && npx vue-tsc --noEmit --pretty 2>&1 | head -30`

Expected: 无相关错误

- [ ] **Step 4: Commit**

```bash
git add frontend-v3/src/components/ui/MobileDrawer.vue frontend-v3/src/layouts/DashboardLayout.vue
git commit -m "feat(mobile): MobileDrawer 添加修改密码入口"
```

---

### Task 5: ChangePasswordDialog 组件测试

**Files:**
- Create: `frontend-v3/test/components/ChangePasswordDialog.spec.ts`

- [ ] **Step 1: 编写 ChangePasswordDialog 测试**

```ts
/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ChangePasswordDialog from '../../src/components/ui/ChangePasswordDialog.vue'

// Mock authApi
vi.mock('@/api', () => ({
  authApi: {
    changePassword: vi.fn(),
  },
}))

// Mock useToast
vi.mock('@/composables', () => ({
  useToast: () => ({
    success: vi.fn(),
    error: vi.fn(),
    showToast: vi.fn(),
    hideToast: vi.fn(),
    clearAll: vi.fn(),
    warning: vi.fn(),
    info: vi.fn(),
    toasts: { value: [] },
  }),
}))

// Mock @vueuse/core
vi.mock('@vueuse/core', () => ({
  useScrollLock: () => ref(false),
}))

import { ref } from 'vue'
import { authApi } from '@/api'

describe('ChangePasswordDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders form fields when open', async () => {
    const wrapper = mount(ChangePasswordDialog, {
      props: { open: true },
      global: {
        stubs: {
          Dialog: {
            template: '<div v-if="open"><slot /><slot name="footer" /></div>',
            props: ['open', 'title', 'description', 'asForm', 'onSubmit'],
          },
          Input: {
            template: '<input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
            props: ['modelValue', 'type', 'placeholder', 'id', 'autocomplete'],
          },
          Label: {
            template: '<label><slot /></label>',
            props: ['for'],
          },
          Button: {
            template: '<button><slot /></button>',
            props: ['variant', 'type', 'loading'],
          },
        },
      },
    })

    // Should show three input fields
    const inputs = wrapper.findAll('input')
    expect(inputs.length).toBe(3)
  })

  it('shows error when old password is empty', async () => {
    const wrapper = mount(ChangePasswordDialog, {
      props: { open: true },
      global: {
        stubs: {
          Dialog: {
            template: '<div v-if="open"><slot /><slot name="footer" /></div>',
            props: ['open', 'title', 'description', 'asForm', 'onSubmit'],
            methods: {
              close() { this.$emit('update:open', false) },
            },
          },
          Input: {
            template: '<input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
            props: ['modelValue', 'type', 'placeholder', 'id', 'autocomplete'],
          },
          Label: {
            template: '<label><slot /></label>',
            props: ['for'],
          },
          Button: {
            template: '<button :type="type"><slot /></button>',
            props: ['variant', 'type', 'loading'],
          },
        },
      },
    })

    // Find submit button and click (simulate form submit)
    const onSubmit = wrapper.findComponent({ name: 'Dialog' }).vm.onSubmit
    if (onSubmit) {
      onSubmit(new Event('submit'))
    } else {
      // Direct submit via handleSubmit - we need to trigger the form
      const form = wrapper.find('form')
      if (form.exists()) {
        await form.trigger('submit')
      }
    }

    await flushPromises()

    // Should show validation error
    expect(wrapper.text()).toContain('请输入旧密码')
  })

  it('shows error when passwords do not match', async () => {
    const wrapper = mount(ChangePasswordDialog, {
      props: { open: true },
      global: {
        stubs: {
          Dialog: {
            template: '<form v-if="open" @submit.prevent="onSubmit($event)"><slot /><slot name="footer" /></form>',
            props: ['open', 'title', 'description', 'asForm', 'onSubmit'],
          },
          Input: {
            template: '<input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
            props: ['modelValue', 'type', 'placeholder', 'id', 'autocomplete'],
          },
          Label: {
            template: '<label><slot /></label>',
            props: ['for'],
          },
          Button: {
            template: '<button :type="type"><slot /></button>',
            props: ['variant', 'type', 'loading'],
          },
        },
      },
    })

    // Fill in form fields via Input stubs
    const inputs = wrapper.findAll('input')
    await inputs[0].setValue('oldpass123')
    await inputs[1].setValue('newpass123')
    await inputs[2].setValue('different123')

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('两次输入的新密码不一致')
  })

  it('calls changePassword API on valid submission', async () => {
    const mockChangePassword = vi.mocked(authApi.changePassword).mockResolvedValue(undefined)

    const wrapper = mount(ChangePasswordDialog, {
      props: { open: true },
      global: {
        stubs: {
          Dialog: {
            template: '<form v-if="open" @submit.prevent="onSubmit($event)"><slot /><slot name="footer" /></form>',
            props: ['open', 'title', 'description', 'asForm', 'onSubmit'],
          },
          Input: {
            template: '<input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
            props: ['modelValue', 'type', 'placeholder', 'id', 'autocomplete'],
          },
          Label: {
            template: '<label><slot /></label>',
            props: ['for'],
          },
          Button: {
            template: '<button :type="type"><slot /></button>',
            props: ['variant', 'type', 'loading'],
          },
        },
      },
    })

    // Fill in all fields correctly
    const inputs = wrapper.findAll('input')
    await inputs[0].setValue('oldpass123')
    await inputs[1].setValue('newpass123')
    await inputs[2].setValue('newpass123')

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(mockChangePassword).toHaveBeenCalledWith({
      old_password: 'oldpass123',
      new_password: 'newpass123',
    })
  })

  it('emits update:open false on successful change', async () => {
    vi.mocked(authApi.changePassword).mockResolvedValue(undefined)

    const wrapper = mount(ChangePasswordDialog, {
      props: { open: true },
      global: {
        stubs: {
          Dialog: {
            template: '<form v-if="open" @submit.prevent="onSubmit($event)"><slot /><slot name="footer" /></form>',
            props: ['open', 'title', 'description', 'asForm', 'onSubmit'],
          },
          Input: {
            template: '<input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
            props: ['modelValue', 'type', 'placeholder', 'id', 'autocomplete'],
          },
          Label: {
            template: '<label><slot /></label>',
            props: ['for'],
          },
          Button: {
            template: '<button :type="type"><slot /></button>',
            props: ['variant', 'type', 'loading'],
          },
        },
      },
    })

    const inputs = wrapper.findAll('input')
    await inputs[0].setValue('oldpass123')
    await inputs[1].setValue('newpass123')
    await inputs[2].setValue('newpass123')

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.emitted('update:open')).toBeTruthy()
    expect(wrapper.emitted('update:open')![0]).toEqual([false])
  })
})
```

- [ ] **Step 2: 运行测试**

Run: `cd frontend-v3 && pnpm test:run -- test/components/ChangePasswordDialog.spec.ts`

Expected: 所有测试通过

- [ ] **Step 3: Commit**

```bash
git add frontend-v3/test/components/ChangePasswordDialog.spec.ts
git commit -m "test(ui): 添加 ChangePasswordDialog 组件测试"
```

---

### Task 6: 最终验证

- [ ] **Step 1: 运行全部前端测试**

Run: `cd frontend-v3 && pnpm test:run`

Expected: 所有测试通过（含新增的 ChangePasswordDialog 测试）

- [ ] **Step 2: 运行 TypeScript 类型检查**

Run: `cd frontend-v3 && npx vue-tsc --noEmit --pretty`

Expected: 无新增类型错误

- [ ] **Step 3: 启动前端 dev server 进行手动验证**

Run: `cd frontend-v3 && pnpm dev`

手动验证清单：
1. 以教师/学生身份登录
2. 侧边栏用户头像区域可点击，展开下拉菜单
3. 下拉菜单包含"修改密码"和"退出登录"
4. 点击"修改密码"弹出对话框
5. 表单校验：空值、密码长度、密码不一致
6. 输入正确密码后提交成功
7. 移动端 MobileDrawer 中有"修改密码"入口
8. 点击外部关闭下拉菜单
