# Features 目录

> 版本: 1.1.0  
> 更新日期: 2026-03-27  
> 设计模式: Feature-based Architecture

---

## 概述

Features 目录按功能域组织代码，实现高内聚、低耦合的代码结构。每个 feature 包含该功能所需的所有组件、逻辑和类型定义。

---

## 目录结构

### 标准 Feature 结构

```
feature-name/
├── components/          # 该功能专用组件
│   ├── FeatureList.vue      # 列表组件
│   ├── FeatureForm.vue      # 表单组件
│   ├── FeatureDialog.vue    # 对话框组件
│   └── ...
├── composables/         # 该功能专用 composables
│   ├── useFeatureList.ts    # 列表逻辑
│   ├── useFeatureForm.ts    # 表单逻辑
│   └── ...
├── types.ts            # 该功能专用类型
├── constants.ts        # 该功能常量
└── index.ts            # 统一导出（门面模式）
```

---

## 现有 Features

| Feature | 说明 | 组件 | Composables | 状态 |
|---------|------|------|-------------|------|
| `students/` | 学生管理 | StudentList, StudentForm, ScoreDialog | useStudentList, useScoreUpdate | ✅ 已实施 |

---

## 创建新 Feature

### 步骤 1: 创建目录结构

```bash
mkdir -p src/features/new-feature/{components,composables}
touch src/features/new-feature/types.ts
touch src/features/new-feature/constants.ts
touch src/features/new-feature/index.ts
```

### 步骤 2: 定义类型

```typescript
// features/new-feature/types.ts

/**
 * 新功能相关类型定义
 */

// 实体类型
export interface FeatureEntity {
  id: string
  name: string
  description: string
  status: 'active' | 'inactive'
  createdAt: string
  updatedAt: string
}

// 表单数据类型
export interface FeatureFormData {
  name: string
  description: string
}

// 查询参数类型
export interface FeatureQueryParams {
  page?: number
  pageSize?: number
  status?: 'active' | 'inactive'
}

// API 响应类型
export interface FeatureListResponse {
  items: FeatureEntity[]
  total: number
  page: number
  pageSize: number
}
```

### 步骤 3: 编写 Composables

```typescript
// features/new-feature/composables/useFeatureList.ts

import { ref, computed } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import type { FeatureEntity, FeatureQueryParams } from '../types'

const FEATURES_QUERY_KEY = 'features'

/**
 * 功能列表管理
 * 
 * @example
 * ```ts
 * const { 
 *   features, 
 *   isLoading, 
 *   pagination, 
 *   refresh 
 * } = useFeatureList()
 * ```
 */
export function useFeatureList(initialParams: FeatureQueryParams = {}) {
  const params = ref<FeatureQueryParams>({
    page: 1,
    pageSize: 10,
    ...initialParams
  })

  const { data, isLoading, refetch } = useQuery({
    queryKey: [FEATURES_QUERY_KEY, params],
    queryFn: () => fetchFeatures(params.value),
    staleTime: 30 * 1000
  })

  const features = computed(() => data.value?.items || [])
  const total = computed(() => data.value?.total || 0)

  const pagination = computed(() => ({
    page: params.value.page || 1,
    pageSize: params.value.pageSize || 10,
    total: total.value
  }))

  const setPage = (page: number) => {
    params.value = { ...params.value, page }
  }

  const setPageSize = (pageSize: number) => {
    params.value = { ...params.value, pageSize, page: 1 }
  }

  return {
    features,
    isLoading,
    pagination,
    setPage,
    setPageSize,
    refresh: refetch
  }
}
```

### 步骤 4: 编写组件

```vue
<!-- features/new-feature/components/FeatureList.vue -->
<template>
  <div class="feature-list">
    <DataTable
      :data="features"
      :loading="isLoading"
      :columns="columns"
      @row-click="handleRowClick"
    />
    <Pagination
      v-bind="pagination"
      @change="setPage"
      @size-change="setPageSize"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useFeatureList } from '../composables/useFeatureList'
import type { FeatureEntity } from '../types'

const props = defineProps<{
  status?: 'active' | 'inactive'
}>()

const { features, isLoading, pagination, setPage, setPageSize } = useFeatureList({
  status: props.status
})

const columns = computed(() => [
  { key: 'name', title: '名称' },
  { key: 'description', title: '描述' },
  { key: 'status', title: '状态' }
])

const emit = defineEmits<{
  'row-click': [feature: FeatureEntity]
}>()

const handleRowClick = (row: FeatureEntity) => {
  emit('row-click', row)
}
</script>
```

### 步骤 5: 统一导出

```typescript
// features/new-feature/index.ts

/**
 * New Feature Module
 * 
 * 新功能模块，提供完整的功能组件和逻辑
 * 
 * @example
 * ```vue
 * <script setup lang="ts">
 * import { FeatureList, useFeatureList } from '@/features/new-feature'
 * 
 * const { features, isLoading } = useFeatureList()
 * </script>
 * 
 * <template>
 *   <FeatureList :data="features" :loading="isLoading" />
 * </template>
 * ```
 */

// 导出组件
export { default as FeatureList } from './components/FeatureList.vue'
export { default as FeatureForm } from './components/FeatureForm.vue'
export { default as FeatureDialog } from './components/FeatureDialog.vue'

// 导出 composables
export { useFeatureList } from './composables/useFeatureList'
export { useFeatureForm } from './composables/useFeatureForm'

// 导出类型
export type {
  FeatureEntity,
  FeatureFormData,
  FeatureQueryParams,
  FeatureListResponse
} from './types'

// 导出常量
export { FEATURE_STATUS, FEATURE_STATUS_LABELS } from './constants'
```

---

## Composables 规范

### 命名规范

| 类型 | 命名格式 | 示例 |
|------|----------|------|
| 列表管理 | `use{Feature}List` | `useStudentList` |
| 表单管理 | `use{Feature}Form` | `useStudentForm` |
| 详情管理 | `use{Feature}Detail` | `useStudentDetail` |
| 操作逻辑 | `use{Action}{Feature}` | `useDeleteStudent` |
| 通用逻辑 | `use{Feature}` | `useStudent` |

### 返回值规范

```typescript
// 列表 composable 标准返回值
interface UseListReturn<T> {
  items: ComputedRef<T[]>      // 列表数据
  isLoading: Ref<boolean>      // 加载状态
  pagination: ComputedRef<Pagination>  // 分页信息
  setPage: (page: number) => void      // 设置页码
  setPageSize: (size: number) => void  // 设置每页数量
  refresh: () => Promise<void>         // 刷新数据
}

// 表单 composable 标准返回值
interface UseFormReturn<T> {
  form: Ref<T>                 // 表单数据
  isSubmitting: Ref<boolean>   // 提交状态
  errors: Ref<FormErrors>      // 表单错误
  submit: () => Promise<void>  // 提交方法
  reset: () => void            // 重置方法
}
```

### 错误处理

```typescript
// composables/useFeatureList.ts
import { useToast } from '@/composables/useToast'

export function useFeatureList() {
  const { showToast } = useToast()
  
  const { data, error, isLoading, refetch } = useQuery({
    queryKey: ['features'],
    queryFn: fetchFeatures,
    onError: (err: Error) => {
      showToast(err.message || '加载失败', 'error')
    }
  })
  
  return { data, error, isLoading, refresh: refetch }
}
```

### 参数传递

```typescript
// ✅ 推荐：使用对象参数
export function useFeatureList(options: UseFeatureListOptions) {
  const { 
    initialPage = 1, 
    pageSize = 10,
    filters = {}
  } = options
  // ...
}

// 使用
const { features } = useFeatureList({
  initialPage: 1,
  pageSize: 20,
  filters: { status: 'active' }
})
```

---

## 组件设计原则

### 1. 单一职责原则

每个组件只负责一个功能点。

```
✅ 正确拆分:
- StudentList.vue      # 只负责列表展示
- StudentForm.vue      # 只负责表单编辑
- StudentDialog.vue    # 只负责弹窗容器

❌ 避免:
- StudentManager.vue   # 包含列表、表单、删除等所有逻辑
```

### 2. Props 设计

#### 使用明确的类型

```vue
<script setup lang="ts">
import type { Student } from '../types'

interface Props {
  student: Student           // 必填
  readonly?: boolean        // 可选，默认 false
  showActions?: boolean     // 可选，默认 true
}

withDefaults(defineProps<Props>(), {
  readonly: false,
  showActions: true
})
</script>
```

#### 使用事件而非回调 Props

```vue
<script setup lang="ts">
// ✅ 推荐：使用 emit
const emit = defineEmits<{
  'update': [student: Student]
  'delete': [id: string]
}>()

const handleUpdate = () => {
  emit('update', student.value)
}

// ❌ 不推荐：回调 props
const props = defineProps<{
  onUpdate: (student: Student) => void
}>()
</script>
```

### 3. 使用 Slots 增强灵活性

```vue
<!-- BaseCard.vue -->
<template>
  <div class="card">
    <header v-if="$slots.header" class="card-header">
      <slot name="header" />
    </header>
    
    <div class="card-body">
      <slot />
    </div>
    
    <footer v-if="$slots.footer" class="card-footer">
      <slot name="footer" />
    </footer>
  </div>
</template>
```

### 4. 组件通信

#### Props Down, Events Up

```vue
<!-- 父组件 -->
<template>
  <StudentList 
    :students="students"
    :loading="isLoading"
    @edit="handleEdit"
    @delete="handleDelete"
  />
</template>

<!-- StudentList.vue -->
<template>
  <div 
    v-for="student in students" 
    :key="student.id"
    class="student-item"
  >
    <span>{{ student.name }}</span>
    <button @click="$emit('edit', student)">编辑</button>
    <button @click="$emit('delete', student.id)">删除</button>
  </div>
</template>
```

### 5. Teleport 使用规范

弹窗、Toast 等组件必须使用 Teleport 渲染到 body。

```vue
<template>
  <Teleport to="body">
    <div v-if="visible" class="dialog-overlay">
      <div class="dialog-content">
        <slot />
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

const isMounted = ref(false)

onMounted(() => {
  isMounted.value = true  // SSR 安全
})
</script>
```

---

## 计划中的 Features

| Feature | 优先级 | 说明 |
|---------|--------|------|
| `checkin/` | P1 | 签到功能完整模块 |
| `classes/` | P1 | 班级管理模块 |
| `teachers/` | P2 | 教师管理模块 |
| `reports/` | P2 | 报表统计模块 |
| `notifications/` | P3 | 通知消息模块 |

---

## 参考

- [详细架构说明](../../docs/ARCHITECTURE.md)
- [设计体系文档](../../DESIGN_SYSTEM.md)
- [Vue 风格指南](https://vuejs.org/style-guide/)
- [Feature-Sliced Design](https://feature-sliced.design/)

---

**最后更新**: 2026-03-27
