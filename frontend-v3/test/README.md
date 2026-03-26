# 前端组件测试

使用 Vitest + @vue/test-utils + jsdom 进行单元测试。

## 安装依赖

```bash
pnpm add -D vitest @vue/test-utils jsdom @vitejs/plugin-vue
```

## 配置

已配置 `vitest.config.ts`:

```typescript
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'jsdom',
    globals: true,
    include: ['test/**/*.{test,spec}.{js,ts}']
  }
})
```

## 运行测试

```bash
# 运行所有测试
pnpm test:run

# 开发模式（监听文件变化）
pnpm test
```

## 测试文件

### Toast 内存泄漏测试

文件：`test/components/Toast.spec.ts`

测试内容：
- ✅ 组件卸载时清理 setTimeout timer
- ✅ 多次触发时清理旧 timer
- ✅ 快速切换不泄漏内存
- ✅ 卸载时调用 clearTimers

**关键修复验证**：
```typescript
// 验证 timer 被清理
expect(wrapper.vm.timeoutId).toBeTruthy()
wrapper.unmount()
expect(wrapper.vm.timeoutId).toBeNull()
```

### Dialog 内存泄漏测试

文件：`test/components/Dialog.spec.ts`

测试内容：
- ✅ 多次打开关闭循环无错误
- ✅ 打开状态卸载不报错
- ✅ 关闭状态卸载不报错

**关键修复验证**：
```typescript
// 验证 onUnmounted 钩子不抛出错误
expect(() => wrapper.unmount()).not.toThrow()
```

## 测试覆盖的修复

| 组件 | 修复内容 | 测试验证 |
|------|----------|----------|
| Toast.vue | 添加 `onUnmounted` 清理 setTimeout | 4 个测试 |
| Dialog.vue | 添加 `onUnmounted` 重置 body overflow | 3 个测试 |

## 手动验证方法

### 浏览器 DevTools 验证

1. 打开 Chrome DevTools
2. 切换到 Memory 面板
3. 点击 "Take heap snapshot"
4. 快速显示/隐藏 Toast 10 次
5. 点击 "Take heap snapshot"
6. 对比内存占用，应无明显增长

### 样式泄漏验证

```javascript
// 在控制台执行
// 1. 打开 Dialog
document.body.style.overflow  // 应为 "hidden"

// 2. 刷新页面（不关闭 Dialog）
document.body.style.overflow  // 应为 ""（空字符串）
```
