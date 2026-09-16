# 班级可见性改造实施计划（课堂问答 + 失物招领）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 课堂问答和失物招领支持"发布时勾选班级"，只有被勾选班级的学生才能看到；未勾选的看不到。

**Architecture:** 与 `course_offering_classes` 同构的关联表方案——`question_classes(question_id, class_id)` + `lost_found_classes(item_id, class_id)`，**无关联行 = 所有班级可见**（兼容现有数据，无需回填）。问答废弃 `questions.class_id` 单班级字段（硬切换到关联表）。前端复用教学班多选的分组勾选 UI。

**Tech Stack:** FastAPI + SQLModel + Alembic（后端）；Vue 3.5 + TS + Tailwind v4（前端）

**Spec:** 用户决策（已确认）：1A 关联表 + 2A 问答硬切换 + 3A 失物招领默认全可见 + 复用教学班多选 UI

## 用户决策（已确认）

| 决策项 | 结论 |
|---|---|
| 可见性模型 | **关联表**（`question_classes` / `lost_found_classes`，复合主键，FK CASCADE），无关联行=所有班级可见 |
| 问答单班级字段 | **废弃 `questions.class_id`**，硬切换到关联表（不留双写） |
| 失物招领默认 | **默认所有班级可见**（不勾=全可见，教师按需收窄） |
| 前端控件 | 复用教学班多选的分组勾选 UI（届/专业分组 + 全选/清空） |

## 关键现状（已核实）

**问答**：
- 模型 `questions.class_id: Optional[int]`（None=所有班级）
- 学生端 `get_questions_by_class(class_id)` 过滤逻辑：`class_id == X OR class_id IS NULL`
- 教师发布：`POST /teacher/questions` body `class_id?: int`
- 前端 `TeacherQuestion.vue` 单选下拉（'' = 所有班级）

**失物招领**：
- 模型 `lost_found_items` **无班级字段**，所有学生可见
- 发布：`POST /teacher/lost-found`（Form 表单，无班级参数）
- 学生列表：`GET /student/lost-found`（无过滤）

**教学班多选 UI 参照**：`frontend-v3/src/views/admin/Offerings.vue`（分组勾选 + 全选/清空 + classGroups computed）

## Global Constraints

- 后端测试：`conda run -n student-manage python -m pytest tests/ -q -p no:randomly`（分片库 `PYTEST_XDIST_WORKER=gwN` + `-n 0`）
- 前端测试：`pnpm test:run`；类型 `pnpm exec vue-tsc --noEmit`（必须退出码 0）
- 硬切换：问答 `class_id` 字段废弃，不留双写/兼容分支
- 无关联行 = 所有班级可见（与教学班通配语义一致，不引入新字段/开关）
- 每个 Task 完成必须：相关测试全绿 + vue-tsc 通过
- 提交粒度：每个 Task 一个 commit

## 任务清单

- [x] **Task 1 — 后端：关联表模型 + 迁移**：✅ fc21cba（spec 通过；12 迁移测试绿）：新增 `QuestionClass(question_id, class_id)` 复合主键表 + `LostFoundClass(item_id, class_id)` 复合主键表（均 FK CASCADE）；迁移建两表 + 从 `questions.class_id` 回填 `question_classes` + 删 `questions.class_id` 列；模型注册 `models/__init__.py`；含迁移测试（回填验证：有 class_id 的问题→关联行，NULL→无行=全可见）
- [x] **Task 2 — 后端：问答可见性改造**：✅ 01eb039（spec 通过；46 测试绿；顺带修 classes.py 的 _CLASS_REFERENCES 引用已删字段）：`create_question` 收 `class_ids: List[int]`（空=所有班级）写关联行；`get_questions_by_class` 改为「关联表含本班 OR 无关联行」过滤；`POST /teacher/questions` body `class_ids`；`GET /teacher/questions` 返回各问题的可见班级列表；学生端 `/student/questions` 过滤不变（逻辑在 crud 层）；更新相关测试
- [x] **Task 3 — 后端：失物招领可见性改造**：✅ 63f5b4c + 43344b5（spec 通过；42 测试绿；spec 评审抓出评论/认领端点越权已补校验 + 回归测试）：`create_lost_found_item` 收 `class_ids`（空=所有班级）写关联行；`get_lost_found_items` 学生端按「关联表含本班 OR 无关联行」过滤（教师端不过滤）；发布端点 Form 加 `class_ids` 参数；详情端点加可见性校验（学生无权访问未授权班级物品→404）；更新相关测试
- [ ] **Task 4 — 前端：问答发布多选班级**：`TeacherQuestion.vue` 单选下拉 → 分组多选（复用 Offerings 的 classGroups 模式 + 全选/清空 + 已选计数）；提交 `class_ids: number[]`（空数组=所有班级）；问题列表显示可见班级（多个时"N 个班级"）；`api/question.ts` 类型同步
- [ ] **Task 5 — 前端：失物招领发布/编辑多选班级**：`LostFoundForm.vue` 加分组多选班级（默认全不勾=所有班级，提示"未选择=所有班级可见"）；编辑时从详情加载已勾选班级；Form 提交加 `class_ids`；`api/lostFound.ts` 类型同步
- [ ] **Task 6 — 前端：学生端类型与展示适配**：学生端问答/失物招领列表无需改（后端已过滤）；检查详情页是否有"可见范围"展示需求（如有则显示可见班级）；类型文件同步
- [ ] **Task 7 — 测试与端到端验证**：后端全量 + 前端全量全绿；起服务手工验证：教师发问答勾 2 个班→只有这 2 个班学生能看到；教师发失物招领勾 1 个班→只有该班学生能看到；不勾→所有学生能看到

## 风险与注意事项

| 风险 | 缓解 |
|---|---|
| 问答现有数据有 `class_id` 的问题 | Task 1 迁移回填到关联表；NULL 的→无关联行=全可见（行为不变） |
| 失物招领现有数据 | 无班级字段，迁移后全部无关联行=全可见（行为不变） |
| 学生端过滤漏判 | crud 层统一「关联表含本班 OR 无关联行」子查询，含单测覆盖三种情况（勾选含本班/勾选不含本班/未勾选） |
