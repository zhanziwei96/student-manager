# 课堂问答功能设计文档

**日期**: 2026-04-21
**状态**: 已批准

---

## 概述

新增独立「问答」模块，老师可在网页上向指定班级提问，学生匿名或实名回答。支持课堂实时互动和课后开放式问答，老师可追问学生回答并标记优秀。

## 需求

- **场景**: 实时课堂互动 + 开放式不限时问答
- **回答形式**: 文本问答 + 老师追问
- **匿名控制**: 学生自行选择是否匿名
- **可见性**: 所有人可见所有回答（匿名时其他学生看不到姓名，老师始终可见）
- **辅助功能**: 老师可对回答点赞/标记优秀

## 数据模型

### Question（问题）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int, PK | 主键 |
| teacher_id | int, FK → user.id | 提问老师 |
| class_name | str | 目标班级 |
| content | str | 问题内容 |
| status | str | `active` / `closed` |
| is_realtime | bool | 是否课堂实时提问 |
| created_at | datetime | 创建时间 |
| closed_at | datetime, nullable | 结束时间 |

### Answer（回答）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int, PK | 主键 |
| question_id | int, FK → question.id | 所属问题 |
| student_id | int, FK → user.id | 回答学生 |
| content | str | 回答内容 |
| is_anonymous | bool | 是否匿名 |
| is_starred | bool | 老师是否标记优秀 |
| parent_id | int, nullable, FK → answer.id | 追问的父回答 |
| created_at | datetime | 创建时间 |

### 约束

- 同一学生对同一问题只能有一条直接回答（`parent_id=NULL` 时 unique 约束）
- 追问通过 `parent_id` 自引用实现，不受上述约束
- 匿名回答 API 对其他学生隐藏 `student_id`，老师始终可见
- 老师追问的 Answer 记录 `student_id` 为老师 ID

## API 设计

### 老师端

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/questions` | 发布问题 |
| GET | `/api/v1/questions?class_name=&status=` | 获取问题列表 |
| PUT | `/api/v1/questions/{id}/close` | 结束问题 |
| POST | `/api/v1/answers/{id}/reply` | 追问某条回答 |
| PUT | `/api/v1/answers/{id}/star` | 标记/取消标记优秀 |

### 学生端

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/questions/class/{class_name}` | 获取本班问题列表 |
| GET | `/api/v1/questions/{id}/answers` | 获取某问题的所有回答 |
| POST | `/api/v1/answers` | 提交回答 |
| PUT | `/api/v1/answers/{id}` | 修改自己的回答 |

### 权限规则

- 老师路由需 `require_teacher` 权限
- 学生只能回答自己班级的活跃问题（`status=active`）
- 学生只能修改自己的回答
- 回答列表按时间排序，追问紧跟父回答下方

## 前端设计

### UI 布局

**老师端** — 列表式布局：
- Tab 切换「进行中/已结束」
- 问题以卡片列表展示，显示回答人数、状态、班级
- 点击「查看回答」展开回答详情，可追问和星标

**学生端** — 卡片式布局：
- 上方显示老师问题
- 中间是回答输入框（含匿名开关）
- 下方展示其他人的回答列表

### 文件结构

```
backend/app/
├── models/question.py          # Question + Answer 模型
├── crud/question.py            # CRUD 操作
├── api/routes/questions.py     # API 路由

frontend-v3/src/
├── api/question.ts             # API 客户端
├── types/api.ts                # 新增 Question/Answer 类型
├── features/question/
│   ├── components/
│   │   ├── QuestionCard.vue
│   │   ├── QuestionForm.vue
│   │   ├── AnswerList.vue
│   │   ├── AnswerItem.vue
│   │   └── AnswerInput.vue
│   ├── composables/
│   │   ├── useTeacherQuestions.ts
│   │   ├── useStudentQuestions.ts
│   │   ├── useAnswers.ts
│   │   └── useQuestionMutations.ts
│   └── types.ts

frontend-v3/src/views/
├── teacher/TeacherQuestion.vue
└── student/StudentQuestion.vue
```

### 路由

| 路径 | 组件 | 权限 |
|------|------|------|
| `/teacher/question` | TeacherQuestion.vue | teacher |
| `/student/question` | StudentQuestion.vue | student |

### queryKey 约定

```
['teacher-questions', className, status]   // 老师问题列表
['student-questions', className]           // 学生问题列表
['answers', questionId]                    // 某问题的回答
```

### 核心交互流程

1. **老师发布问题** → `createQuestion()` → invalidate `['teacher-questions']`
2. **老师查看回答** → 点击 QuestionCard → 展开回答详情 → 可追问/星标
3. **学生回答** → 进入问题页 → AnswerInput 填写+选择匿名 → 提交 → invalidate `['answers', questionId]`
4. **追问展示** → AnswerList 中追问紧跟父回答，视觉上缩进显示

## 测试策略

- **后端单元测试**: Question/Answer CRUD 操作，含匿名逻辑、追问逻辑
- **后端集成测试**: API 路由权限验证、业务流程（发布→回答→追问→星标→结束）
- **前端测试**: composables 逻辑、组件渲染（匿名显示/隐藏、星标交互）
