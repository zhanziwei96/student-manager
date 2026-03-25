# 前端架构指南

> FE-005 修复: 视图层组织改进

## 当前结构

当前视图层按角色组织（admin/teacher/student），这在项目初期是合理的，但随着功能增加，会导致以下问题：

1. **功能分散**: 学生管理功能分散在 `admin/Students.vue` 和 `teacher/Students.vue`
2. **难以复用**: 同一功能的不同角色视图需要重复实现
3. **维护困难**: 修改学生功能需要同时修改多个文件

## 推荐的视图层组织（Feature-based）

```
frontend-v3/src/
├── views/                    # 页面入口（保持简单，仅作为路由入口）
│   ├── admin/
│   │   └── index.ts          # 导出所有管理员页面
│   ├── teacher/
│   │   └── index.ts
│   ├── student/
│   │   └── index.ts
│   ├── LandingPage.vue
│   ├── LoginPage.vue
│   └── NotFound.vue
├── features/                 # 按功能域组织（推荐）
│   ├── students/
│   │   ├── components/       # 学生相关组件
│   │   │   ├── StudentList.vue
│   │   │   ├── StudentForm.vue
│   │   │   └── ScoreDialog.vue
│   │   ├── composables/      # 学生相关逻辑
│   │   │   ├── useStudentForm.ts
│   │   │   └── useScoreUpdate.ts
│   │   ├── types.ts          # 学生相关类型
│   │   └── index.ts          # 统一导出
│   ├── checkin/
│   │   ├── components/
│   │   ├── composables/
│   │   └── types.ts
│   ├── classes/
│   └── teachers/
├── shared/                   # 共享资源
│   ├── components/           # 通用组件 (Button, Input, Card 等)
│   ├── composables/          # 通用逻辑 (useToast, useAuth 等)
│   └── utils/                # 工具函数
└── types/                    # 全局类型定义
```

## Feature 目录结构规范

每个 feature 目录应遵循以下结构：

```
features/feature-name/
├── components/          # 该功能专用组件
│   ├── ComponentA.vue
│   └── ComponentB.vue
├── composables/         # 该功能专用 composables
│   ├── useFeatureA.ts
│   └── useFeatureB.ts
├── types.ts            # 该功能专用类型
└── index.ts            # 统一导出（门面模式）
```

### index.ts 示例

```typescript
/**
 * Feature Name
 * 
 * 功能描述
 * 
 * 使用方式:
 * ```ts
 * import { ComponentA, useFeatureA } from '@/features/feature-name'
 * ```
 */

// 导出组件
export { default as ComponentA } from './components/ComponentA.vue'
export { default as ComponentB } from './components/ComponentB.vue'

// 导出 composables
export { useFeatureA } from './composables/useFeatureA'
export { useFeatureB } from './composables/useFeatureB'

// 导出类型
export type { FeatureAData, FeatureBData } from './types'
```

## 迁移建议

### 阶段1: 新功能使用 Feature-based（立即开始）

新建功能按功能域组织，例如：

```
features/
├── reports/              # 报表功能（新功能）
├── attendance/           # 考勤功能（新功能）
└── notifications/        # 通知功能（新功能）
```

### 阶段2: 逐步迁移现有功能（按需进行）

按优先级逐步迁移现有功能：

1. **students** - 学生管理功能（使用频率高，值得优先迁移）
2. **checkin** - 签到功能
3. **classes** - 班级管理功能
4. **teachers** - 教师管理功能

迁移步骤：
1. 创建新的 feature 目录
2. 将相关组件/逻辑移动到新目录
3. 更新引用路径
4. 验证功能正常
5. 删除旧文件

### 阶段3: 清理旧结构（未来进行）

当所有功能迁移完成后：
1. 清理 views/ 目录中重复的实现
2. 保留 views/ 作为简单的路由入口
3. 更新路由配置，使用新的 feature 组件

## 优势

1. **高内聚**: 同一功能的相关代码放在一起
2. **易复用**: 组件和逻辑可以在不同角色间复用
3. **易维护**: 修改功能只需在一个地方修改
4. **可扩展**: 新增功能不会影响现有代码

## 参考

- [Vue.js Style Guide - Component Naming](https://vuejs.org/style-guide/rules-strongly-recommended.html#component-names)
- [Feature-Sliced Design](https://feature-sliced.design/)
