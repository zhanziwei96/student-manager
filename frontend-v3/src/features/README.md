# Features 目录

按功能域组织的模块。

## 目录结构

每个 feature 目录结构：

```
feature-name/
├── components/      # 该功能专用组件
├── composables/     # 该功能专用 composables
├── types.ts         # 该功能专用类型
└── index.ts         # 统一导出
```

## 现有 Features

- `students/` - 学生管理

## 计划中的 Features

- `checkin/` - 签到功能
- `classes/` - 班级管理
- `teachers/` - 教师管理

## 创建新 Feature

1. 创建目录结构：
```bash
mkdir -p src/features/new-feature/{components,composables}
touch src/features/new-feature/types.ts
 touch src/features/new-feature/index.ts
```

2. 编写 `index.ts` 统一导出
3. 在页面中导入使用

## 参考

详细架构说明见 `docs/ARCHITECTURE.md`
