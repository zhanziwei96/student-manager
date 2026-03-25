# 分数更新后 UI 不刷新 - 已尝试方案记录

## 问题描述
教师页面点击加分/减分后，学生分数在 UI 上不会立即更新，需要刷新浏览器才能看到变化。

---

## 已尝试方案（按时间顺序）

### 方案 1: invalidateQueries → refetchQueries
**时间**: 第一次尝试
**修改文件**: `useStudents.ts`
**修改内容**: 将 `invalidateQueries` 改为 `refetchQueries`
**结果**: ❌ 失败
**原因**: `refetchQueries` 是异步的，`onSuccess` 不会等待它完成

---

### 方案 2: 组件中手动调用 refetch()
**时间**: 第二次尝试
**修改文件**: `teacher/Students.vue`
**修改内容**: 在 `handleQuickScore` 和 `handleUpdateScore` 中添加 `await refetch()`
**结果**: ❌ 失败
**原因**: `refetch()` 可能由于 Reactivity 或缓存问题没有立即刷新 UI

---

### 方案 3: 乐观更新 - 直接修改组件中的 students.value
**时间**: 第三次尝试
**修改文件**: `teacher/Students.vue`
**修改内容**: 使用 `students.value.splice(index, 1, newStudent)` 直接更新本地数据
**结果**: ❌ 失败
**原因**: Vue Query 的 `data` 是 readonly 的，直接修改不会触发响应式更新

---

### 方案 4: 使用 setQueryData 更新缓存（composable 层）
**时间**: 第四次尝试
**修改文件**: `useStudents.ts`
**修改内容**: 在 `useScoreUpdate` 的 `onSuccess` 中使用 `queryClient.setQueryData` 更新缓存
**结果**: ❌ 失败
**原因**: `setQueryData` 的回调函数中 `oldStudents` 为 `undefined`，缓存中没有数据

---

### 方案 5: 添加 structuralSharing: false
**时间**: 第五次尝试
**修改文件**: `useStudents.ts`
**修改内容**: 在 `useQuery` 配置中添加 `structuralSharing: false`
**结果**: ❌ 失败
**原因**: 单独设置此项不能解决问题，需要配合其他方案

---

### 方案 6: 本地 ref + watch 同步
**时间**: 第六次尝试
**修改文件**: `teacher/Students.vue`
**修改内容**: 
1. 创建本地 `const students = ref<Student[]>([])`
2. 使用 `watch` 监听 `studentsData.value` 并同步到本地
3. 更新时直接修改 `students.value`
**结果**: ❌ 失败
**原因**: 调试日志显示 `onSuccess` 回调中缓存数据为 `undefined`，可能 queryClient 实例不一致

---

### 方案 7: staleTime: 0
**时间**: 第七次尝试
**修改文件**: `useStudents.ts`
**修改内容**: 设置 `staleTime: 0`
**结果**: ❌ 失败
**原因**: 单独设置此项不能解决问题

---

### 方案 8: onSettled + invalidateQueries
**时间**: 第八次尝试
**修改文件**: `useStudents.ts`
**修改内容**: 使用 `onSettled` 回调确保最终数据一致性
**结果**: ❌ 失败
**原因**: 仍然是异步更新，UI 不会立即响应

---

### 方案 9: 组件内使用 queryClient.setQueryData
**时间**: 第九次尝试
**修改文件**: `teacher/Students.vue`
**修改内容**: 直接在组件处理函数中使用 `queryClient.setQueryData` 更新缓存
**结果**: ❌ 失败
**原因**: 缓存数据为 `undefined`，queryClient 获取不到数据

---

### 方案 10: 本地 ref + splice 更新
**时间**: 第十次尝试
**修改文件**: `teacher/Students.vue`
**修改内容**: 
1. 创建本地 `students` ref
2. 使用 `splice` 方法更新数组（确保 Vue 响应式）
3. 后台调用 `refetch()` 同步数据
**结果**: ❌ 失败
**原因**: 等待测试结果...

---

## 根本原因分析（进行中）

### 发现的问题：
1. **缓存数据为 undefined**: `queryClient.getQueryData(['students'])` 返回 `undefined`
   - 可能原因 1: queryClient 实例不一致（组件中创建的 vs composable 中创建的）
   - 可能原因 2: queryKey 不匹配
   - 可能原因 3: Vue Query 版本问题

2. **structuralSharing 优化**: Vue Query 默认启用结构共享，可能导致数据被认为是"相同的"而不触发更新

3. **响应式丢失**: Vue Query 的 `data` 是 readonly 的 immutable 数据

---

## 待尝试方案

### 方案 A: 确保 queryClient 实例一致
**思路**: 在组件中通过 `useQueryClient()` 获取的实例可能与 composable 中的不一致
**实现**: 统一使用同一个 queryClient 实例

### 方案 B: 不使用 Vue Query 缓存，完全使用本地状态
**思路**: 放弃 Vue Query 的缓存管理，完全使用 Vue 的响应式系统
**实现**: 
1. 使用独立的 API 调用获取数据
2. 存储在本地 ref 中
3. 更新时直接修改本地 ref

### 方案 C: 使用 Pinia 管理状态
**思路**: 使用 Pinia 替代 Vue Query 管理学生列表状态
**实现**: 创建 students store，组件和 composable 都使用 store

### 方案 D: 检查 Vue Query 版本兼容性
**思路**: 当前使用 v5.69.0，可能存在已知 bug
**实现**: 降级到稳定版本或升级到最新版本

### 方案 E: 使用 invalidateQueries + 强制重新渲染
**思路**: 使用 `invalidateQueries` 后，强制组件重新渲染
**实现**: 使用 `key` 属性或 `v-if` 控制重新渲染

---

## 调试记录

### 2026-03-25 调试发现：
1. `[ScoreUpdate] currentData from cache: undefined` - 缓存中确实没有数据
2. `[ScoreUpdate] No data in cache to update` - 无法更新缓存
3. `[Students] Sync from Vue Query: 140` - 但组件能正常获取到数据（140条学生记录）

**矛盾点**: 组件能获取到数据，但 `queryClient.getQueryData` 返回 `undefined`

**可能解释**: 
- 组件和 composable 使用的是不同的 QueryClient 实例
- 或者存在多个 QueryClientProvider

---

## 下一步行动计划

1. ✅ 检查项目中是否存在多个 QueryClient 实例
2. ✅ 检查 queryKey 是否完全一致
3. ⏳ 尝试方案 B（完全使用本地状态）
4. ⏳ 尝试方案 C（使用 Pinia）
