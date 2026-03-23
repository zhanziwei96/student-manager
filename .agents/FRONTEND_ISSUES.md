# 前端代码问题汇总

## 🔴 严重问题 (P0)

### 1. API 路径不匹配
**文件**: `src/api/classSession.ts`
**问题**: `useStartClassSession` 调用 `classSessionApi.start(className)` 但 API 期望 `{ class_name: string }` 对象
**代码**:
```typescript
// composable 中
const res = await classSessionApi.start(className)  // 直接传字符串

// API 中
start: (data: StartClassRequest): Promise<ApiResponse<ClassSession>> =>
    api('/class-session/start', { method: 'POST', body: data }),  // 期望对象
```
**修复**: 改为 `classSessionApi.start({ class_name: className })`

---

### 2. CheckInResponse 接口未使用但存在
**文件**: `src/types/api.ts`
**问题**: `CheckInResponse` 接口定义了但代码中使用的是 `CheckinRecord`
**代码**:
```typescript
export interface CheckInResponse {  // 未使用
  success: boolean
  message: string
  ...
}
```
**修复**: 删除未使用的接口或统一使用

---

## 🟡 中等问题 (P1)

### 3. 未使用的导入 ✅ 已修复
**文件**: `src/views/NotFound.vue`
**问题**: ~~导入了 `Search` 但未使用~~
**状态**: 经检查，Search 确实在模板中使用了，不是问题

---

### 4. 教师管理页面使用了原生 input 而非组件 ✅ 已修复
**文件**: `src/views/admin/Teachers.vue`
**问题**: ~~使用了原生 `<input>` 而非项目的 `<Input>` 组件~~
```vue
<input
  v-model="searchQuery"
  type="text"
  placeholder="搜索教师..."
  class="w-full rounded-lg border border-white/20 bg-transparent py-2 pl-10 pr-4 text-sm text-white placeholder:text-white/50 focus:border-primary focus:outline-none"
/>
```
**修复**: 应使用 `<Input v-model="searchQuery" placeholder="搜索教师..." class="pl-10" />`

---

### 5. Label 组件 forId prop 使用不一致 ✅ 已修复
**文件**: `src/components/ui/Label.vue`
**问题**: ~~Label 组件定义了 `forId` prop，使用不一致~~
**修复**: 将 `forId` 改为 `for`，更符合 HTML 标准
```vue
<!-- Label.vue -->
<label :class="classes" :for="forId">

<!-- LoginPage.vue 实际使用 -->
<Label for="username">用户名</Label>  <!-- 这里的 for 会传到 forId 吗？-->
```
**修复**: Label 组件应该将 `forId` 映射到 `for` 属性

---

### 6. Input 组件不支持 number 类型的 v-model ✅ 已修复
**文件**: `src/components/ui/Input.vue`
**问题**: ~~`modelValue` 可以是 `string | number`，但 emit 只发送 `string`~~
**修复**: emit 现在也会根据 type 返回 number
```typescript
interface Props {
  modelValue?: string | number  // 接受 number
}
const onInput = (event: Event) => {
  emit('update:modelValue', target.value)  // 但只返回 string
}
```
**修复**: 需要根据 type 决定是否转换

---

## 🟢 轻微问题 (P2)

### 7. 硬编码的 Mock 数据 ✅ 已标记
**修复**: 在所有 mock 数据处添加了 `// TODO:` 注释，标记需要替换为真实 API
**文件**: 
- `src/views/admin/Classes.vue` - 班级数据
- `src/views/admin/Teachers.vue` - 教师数据
- `src/views/teacher/Dashboard.vue` - 统计卡片中的 '2' 和 '24小时'
- `src/views/admin/Dashboard.vue` - trend 数据 '+12%', '+5%' 等
- `src/views/student/Dashboard.vue` - 最近活动数据

**问题**: 大量使用硬编码的 mock 数据

---

### 8. 缺少 Error 状态处理 ✅ 已修复
**文件**: `src/views/student/Dashboard.vue`
**修复**: 添加了 error 状态和空数据状态处理
**文件**: `src/views/student/Dashboard.vue`
**问题**: 只有 `isPending` 状态，没有 `error` 状态处理
```typescript
const { data: students, isPending } = useStudents()  // 缺少 error
```

---

### 9. 学生查找逻辑 ⚠️ 已标记
**文件**: `src/views/student/Dashboard.vue`
**修复**: 添加了 `// FIXME:` 注释，说明应该通过 student_id 而非 name 匹配
**说明**: 需要后端支持返回用户关联的 student_id可能不准确
**文件**: `src/views/student/Dashboard.vue`
**问题**: 通过 `name` 匹配当前学生，但可能有重名
```typescript
const currentStudent = computed(() => {
  return students.value.find(s => s.name === authStore.user?.name) || null
})
```
**建议**: 应使用 `student_id` 或 `user_id` 匹配

---

### 10. Toast 组件可能有多个实例问题
**文件**: 多个视图文件
**问题**: 每个页面都有自己的 Toast 实例和状态管理
**建议**: 使用全局 Toast 服务

---

### 11. 重复的代码模式 ✅ 已修复
**修复**: 创建了 `DataContainer.vue` 组件统一处理 loading、error、空数据状态
**使用**:
```vue
<DataContainer
  :loading="isPending"
  :error="error"
  :has-data="filteredStudents.length > 0"
  empty-text="未找到匹配的学生"
  @retry="refetch"
>
  <!-- 数据展示内容 -->
</DataContainer>
```
**文件**: 多个视图文件
**问题**: 每个视图都有相同的 Loading/Error/Toast 模式，可以抽象

---

### 12. Button loading 状态未使用
**文件**: `src/components/ui/Button.vue`
**问题**: Button 组件支持 `loading` prop，但实际使用中都用 `v-if="isPending"` 在外部处理
```vue
<!-- 实际使用 -->
<Button :disabled="isPending">
  <Loader2 v-if="isPending" class="animate-spin" />
  提交
</Button>

<!-- 可以简化为 -->
<Button :loading="isPending">提交</Button>
```

---

## 📋 代码风格问题 (P3)

### 13. 注释语言混合 ✅ 已修复
**修复**: 所有英文注释已翻译为中文
部分文件使用英文注释，部分使用中文，建议统一

### 14. 类型定义位置不一致 ✅ 已修复
**修复**: `ClassInfo` 类型从组件内部移到 `types/api.ts`
- 有些接口定义在 `types/api.ts`
- 有些定义在组件内部（如 `ClassInfo` 在 Classes.vue）

### 15. Composable 命名不一致 ✅ 已修复
**修复**: 
- `useUpdateScore` → `useScoreUpdate`
- `useStartClassSession` → `useClassSessionStart`
- `useEndClassSession` → `useClassSessionEnd`
- `useCheckIn` → `useStudentCheckIn`

现在统一使用 `use` + 名词 + 动作 的命名方式
- `useStudents` - 复数
- `useStats` - 复数
- `useClassSession` - 单数
- `useUpdateScore` - 动词开头

建议统一为名词复数或统一为 `useXxxQuery/useXxxMutation` 模式

---

## ✅ 已修复的问题

以下问题已在之前修复：

1. ✅ API 路径错误 (`/login` → `/auth/login`)
2. ✅ 登录角色验证逻辑
3. ✅ 全局 margin 重置覆盖问题 (Tailwind)
4. ✅ `isPending.value` 访问方式修复
5. ✅ CheckinRequest 重复定义
6. ✅ DashboardLayout slot 重复渲染
7. ✅ TypeScript 未使用变量错误
