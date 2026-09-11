# ClassHub API 使用示例

---

**文档版本**: v1.2  
**最后更新**: 2026-09-11  
**适用版本**: v3.1.0+  
**API 前缀**: `/api/v1`  
**状态**: ✅ 已同步代码

---

本文档提供 ClassHub API 的详细使用示例，包括 cURL、Python 和 TypeScript 调用方式。

> ⚠️ **v3.1.0 破坏性变更**：班级维度参数已由 `class_name`（裸班级名）改为 `class_id`（行政班 ID），班级 ID 可通过 `GET /api/v1/classes` 获取。响应中的 `class_name` 键保留，值改为完整展示名（如 `2026届软件工程1班`），不可用于逻辑判断或回传。详见 `docs/API_CHANGELOG.md` v3.1.0。

## 目录

1. [认证接口](#认证接口)
2. [学生管理](#学生管理)
3. [签到系统](#签到系统)
4. [用户管理](#用户管理)
5. [课堂管理](#课堂管理)
6. [统计数据](#统计数据)
7. [课程表](#课程表)
8. [系统管理](#系统管理)
9. [错误处理](#错误处理)

---

## 认证接口

### 登录

**接口**: `POST /api/v1/login`

**请求参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |
| role | string | 是 | 角色 (admin/teacher/student) |

#### cURL 示例

```bash
curl -X POST http://localhost:8000/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123",
    "role": "admin"
  }' \
  -c cookies.txt
```

#### Python 示例

```python
import requests

# 登录
response = requests.post(
    "http://localhost:8000/api/v1/login",
    json={
        "username": "admin",
        "password": "admin123",
        "role": "admin"
    }
)

# 保存 Cookie
session = requests.Session()
session.post(
    "http://localhost:8000/api/v1/login",
    json={"username": "admin", "password": "admin123", "role": "admin"}
)

# 后续请求使用 session
stats = session.get("http://localhost:8000/api/v1/stats")
print(stats.json())
```

#### TypeScript 示例

```typescript
// 使用 ofetch
import { ofetch } from 'ofetch'

const login = async () => {
  const response = await ofetch('/api/v1/login', {
    method: 'POST',
    body: {
      username: 'admin',
      password: 'admin123',
      role: 'admin'
    },
    credentials: 'include'  // 携带 Cookie
  })
  
  // 注意: 后端返回格式为 {success, data, message}
  if (response.success) {
    console.log('登录成功:', response.data)
  }
}
```

**成功响应**:

```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "admin",
    "name": "管理员",
    "role": "admin",
    "is_admin": true
  },
  "message": "登录成功"
}
```

**错误响应** (401):

```json
{
  "success": false,
  "message": "用户名或密码错误"
}
```

**限流响应** (429):

```json
{
  "success": false,
  "message": "请求过于频繁，请稍后再试"
}
```

---

### 获取当前用户信息

**接口**: `GET /api/v1/me`

#### cURL 示例

```bash
curl http://localhost:8000/api/v1/me \
  -b cookies.txt
```

#### Python 示例

```python
me = session.get("http://localhost:8000/api/v1/me")
print(me.json())
```

---

### 登出

**接口**: `POST /api/v1/logout`

#### cURL 示例

```bash
curl -X POST http://localhost:8000/api/v1/logout \
  -b cookies.txt
```

---

### 修改密码

**接口**: `POST /api/v1/change-password`

**请求参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| old_password | string | 是 | 旧密码 |
| new_password | string | 是 | 新密码 |

#### cURL 示例

```bash
curl -X POST http://localhost:8000/api/v1/change-password \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "old_password": "admin123",
    "new_password": "newpassword123"
  }'
```

---

## 学生管理

### 获取学生列表

**接口**: `GET /api/v1/students`

**查询参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| class_id | int | 否 | 班级 ID 筛选 |
| keyword | string | 否 | 姓名/学号搜索 |

#### cURL 示例

```bash
# 获取所有学生
curl http://localhost:8000/api/v1/students \
  -b cookies.txt

# 按班级筛选（班级 ID 由 GET /api/v1/classes 获取）
curl "http://localhost:8000/api/v1/students?class_id=1" \
  -b cookies.txt

# 搜索学生
curl "http://localhost:8000/api/v1/students?keyword=张三" \
  -b cookies.txt
```

#### Python 示例

```python
# 获取学生列表
response = session.get("http://localhost:8000/api/v1/students")
students = response.json()["data"]

# 带参数查询
response = session.get(
    "http://localhost:8000/api/v1/students",
    params={"class_id": 1, "keyword": "张三"}
)
```

**成功响应**:

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "student_id": "2024001",
      "name": "张三",
      "class_id": 1,
      "class_name": "2026届软件工程1班",
      "score": 85.5,
      "version": 1
    }
  ],
  "message": "获取成功"
}
```

---

### 添加学生

**接口**: `POST /api/v1/students`

**请求参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| student_id | string | 是 | 学号 |
| name | string | 是 | 姓名 |
| class_id | int | 否 | 班级 ID（未分班可不传） |
| score | number | 否 | 初始分数 (默认70) |

#### cURL 示例

```bash
curl -X POST http://localhost:8000/api/v1/students \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "student_id": "2024002",
    "name": "李四",
    "class_id": 1,
    "score": 80
  }'
```

#### TypeScript 示例

```typescript
const createStudent = async (studentData: {
  student_id: string
  name: string
  class_id?: number
  score?: number
}) => {
  const response = await ofetch('/api/v1/students', {
    method: 'POST',
    body: studentData,
    credentials: 'include'
  })
  
  // 访问 data 字段
  return response.data
}
```

---

### 更新学生分数

**接口**: `PUT /api/v1/students/{student_id}/score`

**请求参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| score_change | number | 是 | 分数变化值 (+/-) |
| reason | string | 是 | 变更原因 |
| version | number | 是 | 乐观锁版本号 |

#### cURL 示例

```bash
curl -X PUT http://localhost:8000/api/v1/students/2024001/score \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "score_change": 10,
    "reason": "课堂表现优秀",
    "version": 1
  }'
```

#### Python 示例

```python
# 更新分数（乐观锁保护）
response = session.put(
    "http://localhost:8000/api/v1/students/2024001/score",
    json={
        "score_change": 10,
        "reason": "课堂表现优秀",
        "version": 1  # 当前版本号
    }
)

# 处理并发冲突
if response.status_code == 409:
    print("数据已被修改，请刷新后重试")
```

**并发冲突响应** (409):

```json
{
  "success": false,
  "message": "数据已被修改，请刷新后重试"
}
```

---

### 删除学生

**接口**: `DELETE /api/v1/students/{student_id}`

#### cURL 示例

```bash
curl -X DELETE http://localhost:8000/api/v1/students/2024001 \
  -b cookies.txt
```

---

### 导入学生 (Excel)

**接口**: `POST /api/v1/students/import`

**Content-Type**: `multipart/form-data`

**模板列**: `学号` / `姓名` / `所属届` / `专业` / `班级名`（班级按「所属届 + 专业 + 班级名」三元组定位：已存在则复用，不存在则自动建班）

#### cURL 示例

```bash
curl -X POST http://localhost:8000/api/v1/students/import \
  -b cookies.txt \
  -F "file=@students.xlsx"
```

#### Python 示例

```python
with open("students.xlsx", "rb") as f:
    response = session.post(
        "http://localhost:8000/api/v1/students/import",
        files={"file": ("students.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )
    
print(response.json())
```

---

### 获取分数历史

**接口**: `GET /api/v1/students/{student_id}/scores`

#### cURL 示例

```bash
curl http://localhost:8000/api/v1/students/2024001/scores \
  -b cookies.txt
```

**成功响应**:

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "old_score": 70,
      "new_score": 80,
      "delta": 10,
      "reason": "课堂表现优秀",
      "operator": "张老师",
      "created_at": "2026-04-05T10:30:00"
    }
  ],
  "message": "获取成功"
}
```

---

### 获取班级列表

**接口**: `GET /api/v1/classes`

**说明**: 响应中的 `id` 即其它接口所需的 `class_id`；`display_name` 为完整展示名。班级唯一键为 `(name, major, cohort_year)`，裸班名（如 `1班`）可跨专业/跨届重复，**不可**作为接口参数。

#### cURL 示例

```bash
curl http://localhost:8000/api/v1/classes \
  -b cookies.txt
```

**成功响应**:

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "1班",
      "major": "软件工程",
      "cohort_year": "2026",
      "display_name": "2026届软件工程1班",
      "student_count": 50
    },
    {
      "id": 2,
      "name": "2班",
      "major": "软件工程",
      "cohort_year": "2026",
      "display_name": "2026届软件工程2班",
      "student_count": 48
    }
  ],
  "message": "获取成功"
}
```

---

## 签到系统

### 学生签到

**接口**: `POST /api/v1/checkin`

**请求参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| student_id | string | 是 | 学号 |
| name | string | 是 | 姓名 |
| device_fingerprint | string | 否 | 设备指纹 |

#### cURL 示例

```bash
curl -X POST http://localhost:8000/api/v1/checkin \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "2024001",
    "name": "张三",
    "device_fingerprint": "abc123"
  }'
```

#### TypeScript 示例

```typescript
const checkin = async (studentId: string, name: string) => {
  const response = await ofetch('/api/v1/checkin', {
    method: 'POST',
    body: {
      student_id: studentId,
      name: name,
      device_fingerprint: await generateDeviceFingerprint()
    }
  })
  
  return response.data
}
```

**成功响应**:

```json
{
  "success": true,
  "data": {
    "checkin_id": 1,
    "student_id": "2024001",
    "student_name": "张三",
    "checkin_time": "2026-04-05T08:30:00",
    "checkin_type": "normal"
  },
  "message": "签到成功"
}
```

**重复签到响应**:

```json
{
  "success": false,
  "message": "今日已签到"
}
```

---

### 教师代签

**接口**: `POST /api/v1/teacher-checkin`

**请求参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| student_id | string | 是 | 学号 |
| reason | string | 否 | 代签原因 |

#### cURL 示例

```bash
curl -X POST http://localhost:8000/api/v1/teacher-checkin \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "student_id": "2024001",
    "reason": "设备故障"
  }'
```

---

### 获取签到记录

**接口**: `GET /api/v1/checkin/records`

**查询参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| student_id | string | 否 | 学号筛选 |
| class_id | int | 否 | 班级 ID 筛选 |
| date | string | 否 | 日期 (YYYY-MM-DD) |

#### cURL 示例

```bash
# 获取今日签到记录
curl "http://localhost:8000/api/v1/checkin/records?date=2026-04-05" \
  -b cookies.txt

# 获取某学生签到记录
curl "http://localhost:8000/api/v1/checkin/records?student_id=2024001" \
  -b cookies.txt
```

---

### 获取今日签到列表

**接口**: `GET /api/v1/checkins/today`

#### cURL 示例

```bash
curl http://localhost:8000/api/v1/checkins/today \
  -b cookies.txt
```

---

### 获取签到统计

**接口**: `GET /api/v1/checkins/stats`

#### cURL 示例

```bash
curl http://localhost:8000/api/v1/checkins/stats \
  -b cookies.txt
```

**成功响应**:

```json
{
  "success": true,
  "data": {
    "total_students": 50,
    "checked_in": 45,
    "not_checked_in": 5,
    "checkin_rate": 90.0
  },
  "message": "获取成功"
}
```

---

## 用户管理

### 获取用户列表 (管理员)

**接口**: `GET /api/v1/admin/users`

#### cURL 示例

```bash
curl http://localhost:8000/api/v1/admin/users \
  -b cookies.txt
```

---

### 创建用户 (管理员)

**接口**: `POST /api/v1/admin/users`

**请求参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名 |
| name | string | 是 | 显示名称 |
| password | string | 是 | 密码 |
| role | string | 是 | 角色 (admin/teacher) |
| assigned_class | string | 否 | 负责班级 |

#### cURL 示例

```bash
curl -X POST http://localhost:8000/api/v1/admin/users \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "username": "teacher1",
    "name": "王老师",
    "password": "teacher123",
    "role": "teacher",
    "assigned_class": "软件1班"
  }'
```

---

### 重置用户密码 (管理员)

**接口**: `PUT /api/v1/admin/users/{user_id}/reset-password`

**请求参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| new_password | string | 是 | 新密码 |

#### cURL 示例

```bash
curl -X PUT http://localhost:8000/api/v1/admin/users/2/reset-password \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "new_password": "newpassword123"
  }'
```

---

## 课堂管理

### 获取课堂状态

**接口**: `GET /api/v1/class-session`

#### cURL 示例

```bash
curl http://localhost:8000/api/v1/class-session \
  -b cookies.txt
```

**成功响应**:

```json
{
  "success": true,
  "data": {
    "active": true,
    "class_name": "2026届软件工程1班",
    "start_time": "2026-04-05T08:00:00",
    "teacher_name": "张老师"
  },
  "message": "获取成功"
}
```

---

### 开始上课

**接口**: `POST /api/v1/class-session/start`

**请求参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| class_id | int | 是 | 班级 ID |

#### cURL 示例

```bash
curl -X POST http://localhost:8000/api/v1/class-session/start \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "class_id": 1
  }'
```

---

### 结束上课

**接口**: `POST /api/v1/class-session/end`

#### cURL 示例

```bash
curl -X POST http://localhost:8000/api/v1/class-session/end \
  -b cookies.txt
```

#### Python 示例

```python
# 开始上课
response = session.post(
    "http://localhost:8000/api/v1/class-session/start",
    json={"class_id": 1}
)
print(response.json())

# 结束上课
response = session.post("http://localhost:8000/api/v1/class-session/end")
print(response.json())
```

#### TypeScript 示例

```typescript
const startClass = async (classId: number) => {
  const response = await ofetch('/api/v1/class-session/start', {
    method: 'POST',
    body: { class_id: classId },
    credentials: 'include'
  })
  return response.data
}

const endClass = async () => {
  const response = await ofetch('/api/v1/class-session/end', {
    method: 'POST',
    credentials: 'include'
  })
  return response.data
}
```

---

## 统计数据

### 获取首页统计

**接口**: `GET /api/v1/stats`

#### cURL 示例

```bash
curl http://localhost:8000/api/v1/stats \
  -b cookies.txt
```

**成功响应**:

```json
{
  "success": true,
  "data": {
    "total_students": 150,
    "total_classes": 5,
    "today_checkins": 120,
    "active_sessions": 3
  },
  "message": "获取成功"
}
```

---

### 获取仪表盘数据 (公开)

**接口**: `GET /api/v1/dashboard`

#### cURL 示例

```bash
# 无需认证
curl http://localhost:8000/api/v1/dashboard
```

**成功响应**:

```json
{
  "success": true,
  "data": {
    "total_students": 150,
    "total_classes": 5,
    "top_students": [
      {"rank": 1, "name": "学生A", "score": 95}
    ]
  },
  "message": "获取成功"
}
```

---

### 获取分数日志

**接口**: `GET /api/v1/score/logs`

**查询参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| student_id | string | 否 | 学号筛选 |
| limit | number | 否 | 返回条数 (默认50) |

#### cURL 示例

```bash
curl "http://localhost:8000/api/v1/score/logs?limit=10" \
  -b cookies.txt
```

---

## 系统管理

### 获取审计日志 (管理员)

**接口**: `GET /api/v1/audit/logs`

**查询参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | number | 否 | 用户ID筛选 |
| action | string | 否 | 操作类型筛选 |
| limit | number | 否 | 返回条数 (默认50) |

#### cURL 示例

```bash
curl "http://localhost:8000/api/v1/audit/logs?limit=10" \
  -b cookies.txt
```

**成功响应**:

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "user_id": 1,
      "action": "UPDATE_SCORE",
      "resource_type": "student",
      "resource_id": "2024001",
      "details": "分数从 70 更新到 80",
      "ip_address": "127.0.0.1",
      "created_at": "2026-04-05T10:30:00"
    }
  ],
  "message": "获取成功"
}
```

---

## 课程表

### 获取课程表

**接口**: `GET /api/v1/schedules`

**查询参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| class_id | int | 否 | 班级 ID 筛选 |
| teacher_id | number | 否 | 教师筛选 |

#### cURL 示例

```bash
curl "http://localhost:8000/api/v1/schedules?class_id=1" \
  -b cookies.txt
```

---

### 创建课程 (管理员)

**接口**: `POST /api/v1/schedules`

**请求参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| course_name | string | 是 | 课程名称 |
| class_id | int | 是 | 班级 ID |
| teacher_id | number | 是 | 教师ID |
| day_of_week | string | 是 | 星期 (1-7) |
| start_time | string | 是 | 开始时间 (HH:MM) |
| end_time | string | 是 | 结束时间 (HH:MM) |
| classroom | string | 否 | 教室 |

#### cURL 示例

```bash
curl -X POST http://localhost:8000/api/v1/schedules \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "course_name": "计算机应用基础",
    "class_id": 1,
    "teacher_id": 2,
    "day_of_week": "3",
    "start_time": "08:00",
    "end_time": "09:40",
    "classroom": "A101"
  }'
```

---

### 导入课程表 (管理员)

**接口**: `POST /api/v1/schedules/import`

**Content-Type**: `multipart/form-data`

**模板列**: `课程名称` / `所属届` / `专业` / `班级名` / `教师姓名` / `星期` / `开始时间` / `结束时间`（原单一「班级」列已拆为「所属届 + 专业 + 班级名」三列，班级不存在则自动建班）

#### cURL 示例

```bash
curl -X POST http://localhost:8000/api/v1/schedules/import \
  -b cookies.txt \
  -F "file=@schedules.xlsx"
```

---

### 获取今日课表

**接口**: `GET /api/v1/schedules/today`

#### cURL 示例

```bash
curl http://localhost:8000/api/v1/schedules/today \
  -b cookies.txt
```

**成功响应**:

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "course_name": "计算机应用基础",
      "class_id": 1,
      "class_name": "2026届软件工程1班",
      "teacher_name": "张老师",
      "day_of_week": 1,
      "start_time": "08:00",
      "end_time": "09:40",
      "classroom": "A101",
      "session_status": "active"
    }
  ],
  "message": "获取成功"
}
```

---

## 错误处理

### 通用错误码

| 状态码 | 说明 | 处理建议 |
|--------|------|----------|
| 400 | 请求参数错误 | 检查请求参数格式 |
| 401 | 未认证 | 重新登录获取 Token |
| 403 | 权限不足 | 检查用户角色权限 |
| 404 | 资源不存在 | 检查资源ID是否正确 |
| 409 | 并发冲突 | 刷新数据后重试 |
| 429 | 请求过于频繁 | 等待后重试 |
| 500 | 服务器错误 | 联系管理员 |

### 错误响应格式

```json
{
  "success": false,
  "message": "错误描述信息"
}
```

### 前端错误处理示例

```typescript
import { ofetch, FetchError } from 'ofetch'

const apiCall = async () => {
  try {
    const response = await ofetch('/api/v1/students', {
      credentials: 'include'
    })
    return response.data  // 注意访问 data 字段
  } catch (error) {
    if (error instanceof FetchError) {
      switch (error.response?.status) {
        case 401:
          // 未认证，跳转登录
          router.push('/login')
          break
        case 403:
          // 权限不足
          showToast('权限不足', 'error')
          break
        case 429:
          // 限流
          showToast('请求过于频繁，请稍后再试', 'warning')
          break
        case 409:
          // 并发冲突
          showToast('数据已被修改，请刷新后重试', 'warning')
          break
        default:
          showToast(error.data?.message || '请求失败', 'error')
      }
    }
    throw error
  }
}
```

---

## 相关文档

- [API 变更日志](./API_CHANGELOG.md) - API 版本变更记录
- [后端架构](../backend/README.md) - 后端架构设计
- [弃用说明](./DEPRECATIONS.md) - 弃用接口和迁移指南

---

**文档版本**: v1.1  
**最后更新**: 2026-04-13
