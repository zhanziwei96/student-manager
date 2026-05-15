# 失物招领功能设计规格

**日期**: 2026-05-15
**状态**: 已批准

---

## 1. 概述

失物招领（Lost and Found）功能允许教师发布校园失物/招领信息，学生可以浏览、留言评论、认领物品，教师确认认领后流程闭环。

### 核心角色

- **教师**：发布物品信息、管理认领、查看认领者真实信息
- **学生**：浏览物品、匿名评论、认领物品

### 关键约束

- 全校共享，不按班级隔离
- 教师发布无需管理员审核
- 认领者姓名和联系方式仅教师可见，其他学生看到匿名
- 评论者姓名仅教师可见，其他学生看到「匿名用户」
- 支持图片上传
- 多个学生可同时认领同一物品

---

## 2. 数据模型

### 2.1 `lost_found_items` — 物品主表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, autoincrement | 自增主键 |
| title | VARCHAR(200) | NOT NULL | 物品名称 |
| description | TEXT | NOT NULL | 详细描述 |
| location | VARCHAR(200) | NULLABLE | 丢失/拾获地点 |
| image_url | VARCHAR(500) | NULLABLE | 图片存储路径 |
| status | VARCHAR(20) | NOT NULL, default 'open' | 状态：open/claiming/closed |
| publisher_id | INTEGER | FK → users.id, NOT NULL | 发布教师 ID |
| created_at | DATETIME | NOT NULL | 创建时间（Asia/Shanghai） |
| updated_at | DATETIME | NOT NULL | 更新时间 |

**索引**: `publisher_id`, `status`, `created_at`

### 2.2 `lost_found_comments` — 评论/留言表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, autoincrement | 自增主键 |
| item_id | INTEGER | FK → lost_found_items.id, NOT NULL | 关联物品 |
| user_id | INTEGER | FK → users.id, NOT NULL | 留言用户 |
| content | TEXT | NOT NULL | 留言内容 |
| created_at | DATETIME | NOT NULL | 创建时间 |

**索引**: `item_id`, `user_id`

### 2.3 `lost_found_claims` — 认领记录表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, autoincrement | 自增主键 |
| item_id | INTEGER | FK → lost_found_items.id, NOT NULL | 关联物品 |
| student_id | INTEGER | FK → users.id, NOT NULL | 认领学生 |
| contact | VARCHAR(200) | NOT NULL | 联系方式 |
| message | TEXT | NULLABLE | 认领说明 |
| status | VARCHAR(20) | NOT NULL, default 'pending' | 状态：pending/confirmed/rejected |
| created_at | DATETIME | NOT NULL | 创建时间 |

**索引**: `item_id`, `student_id`, `status`

**唯一约束**: `(item_id, student_id)` — 同一学生对同一物品只能认领一次

---

## 3. 状态流转

```
物品状态:
  open ──(学生认领)──→ claiming ──(教师确认任一认领)──→ closed

认领状态:
  pending ──(教师确认)──→ confirmed
  pending ──(教师拒绝)──→ rejected
```

- 物品状态为 `open` 时，学生可以认领
- 第一个学生认领后，物品状态变为 `claiming`
- 物品状态为 `claiming` 时，其他学生仍可认领
- 教师确认任一认领后，该认领状态变为 `confirmed`，物品状态变为 `closed`
- 确认操作同时将同一物品的其他所有 `pending` 认领自动变为 `rejected`（在 CRUD 层事务中完成）
- 物品状态为 `closed` 时，不再接受新的认领和评论

---

## 4. 隐私规则

| 信息 | 教师看到 | 学生看到 |
|------|----------|----------|
| 物品信息 | 完整 | 完整 |
| 评论内容 | 可见 | 可见 |
| 评论者姓名 | 真实姓名 | 「匿名用户」 |
| 认领者姓名 | 真实姓名 | 不可见 |
| 认领联系方式 | 可见 | 不可见 |
| 认领状态 | 可见 | 可见（仅状态，不含认领者信息） |

实现方式：
- 学生端 API 返回数据时，剥离 `user_name`、`contact` 等敏感字段
- 教师端 API 返回完整数据
- 前端根据角色决定显示内容

---

## 5. API 设计

### 5.1 教师端 API

基础路径: `/api/v1/teacher/lost-found`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/` | 创建物品 |
| GET | `/` | 获取物品列表（教师视角，含认领统计） |
| GET | `/{id}` | 获取物品详情（含评论+认领者真实信息） |
| PUT | `/{id}` | 编辑物品 |
| DELETE | `/{id}` | 删除物品 |
| PUT | `/{id}/claims/{claim_id}/confirm` | 确认认领 |
| PUT | `/{id}/claims/{claim_id}/reject` | 拒绝认领 |

**创建物品请求体**:
```json
{
  "title": "一串钥匙",
  "description": "在操场捡到的一串钥匙，上面有一个蓝色钥匙扣",
  "location": "操场篮球架附近"
}
```

**图片上传**: 通过 multipart/form-data 上传，返回 `image_url`。

**教师端物品详情响应**（含认领者信息）:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "一串钥匙",
    "description": "...",
    "location": "操场",
    "image_url": "/uploads/lost-found/xxx.jpg",
    "status": "claiming",
    "publisher_id": 5,
    "created_at": "2026-05-15T10:00:00",
    "comments": [
      {
        "id": 1,
        "content": "我好像看到有人在找钥匙",
        "user_name": "张三",
        "user_id": 10,
        "created_at": "2026-05-15T11:00:00"
      }
    ],
    "claims": [
      {
        "id": 1,
        "student_id": 10,
        "student_name": "张三",
        "contact": "微信: zhangsan123",
        "message": "这是我的钥匙，蓝色钥匙扣",
        "status": "pending",
        "created_at": "2026-05-15T12:00:00"
      }
    ]
  }
}
```

### 5.2 学生端 API

基础路径: `/api/v1/student/lost-found`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 浏览列表（支持搜索、状态筛选） |
| GET | `/{id}` | 查看详情（评论匿名，认领信息脱敏） |
| POST | `/{id}/comments` | 发表评论 |
| POST | `/{id}/claim` | 认领物品 |

**查询参数**:
- `keyword`: 搜索关键词（匹配 title、description、location）
- `status`: 筛选状态（open/claiming/closed）
- `page`: 页码，默认 1
- `page_size`: 每页数量，默认 20

**学生端物品详情响应**（匿名处理）:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "一串钥匙",
    "description": "...",
    "location": "操场",
    "image_url": "/uploads/lost-found/xxx.jpg",
    "status": "claiming",
    "publisher_name": "李老师",
    "created_at": "2026-05-15T10:00:00",
    "comments": [
      {
        "id": 1,
        "content": "我好像看到有人在找钥匙",
        "user_name": "匿名用户",
        "created_at": "2026-05-15T11:00:00"
      }
    ],
    "claim_status": "pending",
    "my_claim": {
      "id": 1,
      "status": "pending",
      "created_at": "2026-05-15T12:00:00"
    }
  }
}
```

**认领请求体**:
```json
{
  "contact": "微信: zhangsan123",
  "message": "这是我的钥匙，蓝色钥匙扣"
}
```

**评论请求体**:
```json
{
  "content": "我好像看到有人在找钥匙"
}
```

---

## 6. 前端设计

### 6.1 教师页面

**LostFound.vue** — 物品管理列表
- 卡片/列表视图展示物品
- 显示状态标签（open/claiming/closed）
- 显示认领数量统计
- 创建新物品按钮
- 搜索和状态筛选

**LostFoundDetail.vue** — 详情 + 认领管理
- 物品完整信息 + 图片展示
- 评论区（显示真实姓名）
- 认领列表（显示认领者姓名、联系方式、认领说明）
- 确认/拒绝认领按钮
- 编辑/删除物品

**LostFoundForm.vue** — 创建/编辑表单
- 标题、描述、地点输入
- 图片上传
- 表单验证

### 6.2 学生页面

**LostFound.vue** — 浏览列表
- 卡片视图展示物品
- 搜索框 + 状态筛选
- 分页

**LostFoundDetail.vue** — 详情 + 评论 + 认领
- 物品信息 + 图片展示
- 评论区（匿名显示）
- 认领按钮（弹窗填写联系方式和说明）
- 查看自己的认领状态

### 6.3 路由

```typescript
// 教师路由
{
  path: 'lost-found',
  component: () => import('@/views/teacher/LostFound.vue'),
  meta: { role: UserRoleConst.TEACHER }
},
{
  path: 'lost-found/:id',
  component: () => import('@/views/teacher/LostFoundDetail.vue'),
  meta: { role: UserRoleConst.TEACHER }
},
{
  path: 'lost-found/create',
  component: () => import('@/views/teacher/LostFoundForm.vue'),
  meta: { role: UserRoleConst.TEACHER }
},
{
  path: 'lost-found/:id/edit',
  component: () => import('@/views/teacher/LostFoundForm.vue'),
  meta: { role: UserRoleConst.TEACHER }
}

// 学生路由
{
  path: 'lost-found',
  component: () => import('@/views/student/LostFound.vue'),
  meta: { role: UserRoleConst.STUDENT }
},
{
  path: 'lost-found/:id',
  component: () => import('@/views/student/LostFoundDetail.vue'),
  meta: { role: UserRoleConst.STUDENT }
}
```

### 6.4 侧边栏导航

在教师和学生的 DashboardLayout 侧边栏中添加「失物招领」入口。

---

## 7. 图片上传

复用现有 `app.core.upload.save_upload_file_securely` 函数（已在 students 和 schedules 中使用）。

- 存储路径: `backend/uploads/lost-found/`
- 文件命名: UUID 重命名（`use_uuid=True`）
- API: 图片随创建/编辑物品的请求一起上传（multipart/form-data）
- 前端: 表单中使用 `<input type="file">` + FormData
- 限制: 使用配置中的 `upload.max_file_size_mb`、`upload.allowed_extensions`

---

## 8. 测试策略

### 后端测试

**单元测试** (`tests/unit/crud/test_lost_found.py`):
- 创建物品
- 查询物品列表（含搜索、状态筛选）
- 更新物品状态
- 创建评论
- 创建认领
- 确认/拒绝认领
- 同一学生重复认领应失败
- closed 状态物品不可认领

**集成测试** (`tests/integration/test_lost_found_api.py`):
- 教师完整 CRUD 流程
- 学生浏览、评论、认领流程
- 隐私规则验证（学生端不返回认领者信息）
- 权限验证（学生不能访问教师端 API）

### 前端测试

**组件测试** (`frontend-v3/test/views/`):
- LostFound 列表渲染
- LostFoundDetail 详情展示
- LostFoundForm 表单验证
- 评论提交
- 认领提交

---

## 9. 文件清单

### 后端（新建）

| 文件 | 说明 |
|------|------|
| `backend/app/models/lost_found.py` | 数据模型 |
| `backend/app/crud/lost_found.py` | CRUD 操作 |
| `backend/app/api/routes/lost_found.py` | API 路由 |
| `backend/alembic/versions/xxx_add_lost_found_tables.py` | 数据库迁移 |
| `tests/unit/crud/test_lost_found.py` | 单元测试 |
| `tests/integration/test_lost_found_api.py` | 集成测试 |

### 后端（修改）

| 文件 | 说明 |
|------|------|
| `backend/app/models/__init__.py` | 注册模型 |
| `backend/app/crud/__init__.py` | 注册 CRUD |
| `backend/app/api/routes/__init__.py` | 注册路由 |
| `backend/main.py` | 注册路由器 |

### 前端（新建）

| 文件 | 说明 |
|------|------|
| `frontend-v3/src/types/lostFound.ts` | 类型定义 |
| `frontend-v3/src/api/lostFound.ts` | API 客户端 |
| `frontend-v3/src/composables/useLostFound.ts` | 组合式函数 |
| `frontend-v3/src/views/teacher/LostFound.vue` | 教师列表页 |
| `frontend-v3/src/views/teacher/LostFoundDetail.vue` | 教师详情页 |
| `frontend-v3/src/views/teacher/LostFoundForm.vue` | 教师表单页 |
| `frontend-v3/src/views/student/LostFound.vue` | 学生列表页 |
| `frontend-v3/src/views/student/LostFoundDetail.vue` | 学生详情页 |
| `frontend-v3/test/views/LostFound.spec.ts` | 前端测试 |

### 前端（修改）

| 文件 | 说明 |
|------|------|
| `frontend-v3/src/api/index.ts` | 注册 API |
| `frontend-v3/src/composables/index.ts` | 注册 composable |
| `frontend-v3/src/router/index.ts` | 注册路由 |
| `frontend-v3/src/layouts/DashboardLayout.vue` | 侧边栏导航 |
