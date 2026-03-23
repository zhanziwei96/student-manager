# 前端代码问题汇总

> ⚠️ **本文档已归档** - 大部分问题已修复，frontend-v3 已稳定运行
> 
> **最后更新**: 2026-03-23

---

## ✅ 已修复的问题汇总

### API 集成 (全部完成)
| 模块 | 状态 | 说明 |
|------|------|------|
| 认证模块 | ✅ | 登录/登出/用户信息获取 |
| 学生管理 | ✅ | 学生列表/分数更新 |
| 统计模块 | ✅ | 首页统计数据 |
| 签到模块 | ✅ | 签到/签到记录 |
| 教师模块 | ✅ | 教师列表 |
| 班级模块 | ✅ | 班级列表获取 |

### UI 组件修复
| 问题 | 状态 | 修复内容 |
|------|------|----------|
| Tailwind v4 配置 | ✅ | 使用 `@theme inline` 保留默认主题 |
| Button loading 状态 | ✅ | 支持 `loading` prop |
| Input number 类型 | ✅ | 支持 `v-model.number` |
| Label forId | ✅ | 改为标准 `for` 属性 |
| DataContainer 组件 | ✅ | 统一处理 loading/error/空数据状态 |

### 代码风格修复
| 问题 | 状态 | 修复内容 |
|------|------|----------|
| 注释语言统一 | ✅ | 全部翻译为中文 |
| 类型定义位置 | ✅ | 统一放在 `types/api.ts` |
| Composable 命名 | ✅ | 统一为 `use` + 名词 + 动作 |
| 未使用导入 | ✅ | 清理所有未使用的导入 |

---

## 📁 项目结构 (frontend-v3)

```
frontend-v3/
├── src/
│   ├── api/              # API 客户端
│   │   ├── auth.ts
│   │   ├── students.ts
│   │   ├── checkin.ts
│   │   ├── stats.ts
│   │   ├── classes.ts
│   │   └── classSession.ts
│   ├── components/ui/    # UI 组件库
│   │   ├── Button.vue
│   │   ├── Card.vue
│   │   ├── Input.vue
│   │   ├── Dialog.vue
│   │   ├── Badge.vue
│   │   ├── Toast.vue
│   │   ├── DataContainer.vue
│   │   └── SearchableSelect.vue
│   ├── composables/      # 组合式函数
│   │   ├── useStudents.ts
│   │   ├── useClasses.ts
│   │   ├── useStats.ts
│   │   ├── useClassSession.ts
│   │   └── useToast.ts
│   ├── views/            # 页面视图
│   │   ├── LandingPage.vue
│   │   ├── LoginPage.vue
│   │   ├── admin/
│   │   │   ├── Dashboard.vue
│   │   │   ├── Students.vue
│   │   │   ├── Teachers.vue
│   │   │   └── Classes.vue
│   │   ├── teacher/
│   │   │   ├── Dashboard.vue
│   │   │   ├── Students.vue
│   │   │   └── ClassSession.vue
│   │   └── student/
│   │       └── Dashboard.vue
│   ├── stores/           # Pinia 状态管理
│   ├── router/           # 路由配置
│   ├── types/            # TypeScript 类型
│   └── styles/           # 全局样式
├── package.json
├── vite.config.ts
└── tsconfig.json
```

---

## 🔧 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue | 3.5.13 | 框架 |
| TypeScript | 5.8.2 | 类型系统 |
| Vite | 6.2.2 | 构建工具 |
| Tailwind CSS | 4.2.2 | CSS 框架 |
| Pinia | 3.0.1 | 状态管理 |
| TanStack Query | 5.69.0 | 服务端状态管理 |
| Vue Router | 4.5.0 | 路由 |
| Lucide Vue | 0.483.0 | 图标库 |
| Zod | 3.24.2 | 数据验证 |

---

## 📝 历史问题记录

<details>
<summary>点击查看历史问题（已修复）</summary>

### 1. API 路径不匹配
**文件**: `src/api/classSession.ts`  
**问题**: `useStartClassSession` 调用 `classSessionApi.start(className)` 但 API 期望 `{ class_name: string }` 对象  
**修复**: 改为 `classSessionApi.start({ class_name: className })`

### 2. 教师管理页面使用了原生 input
**文件**: `src/views/admin/Teachers.vue`  
**修复**: 使用 `<Input>` 组件替代原生 `<input>`

### 3. Input 组件不支持 number 类型的 v-model
**文件**: `src/components/ui/Input.vue`  
**修复**: emit 根据 type 返回 number 或 string

### 4. 硬编码的 Mock 数据
**修复**: 已替换为真实 API 调用

### 5. 缺少 Error 状态处理
**修复**: 添加 `DataContainer` 组件统一处理

### 6. 重复的代码模式
**修复**: 创建 `DataContainer.vue` 组件

</details>

---

**注**: 本文档不再更新，如有新问题请在对应代码文件中添加 TODO 注释。
