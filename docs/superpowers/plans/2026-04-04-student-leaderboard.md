# 学生排行榜功能实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 开发学生排行榜页面，支持班级/全校切换，显示前50名，并列排名，高亮当前登录学生

**架构:** 后端提供API按分数排序返回学生列表，前端展示排名表格，支持Tab切换和响应式设计

**Tech Stack:** FastAPI + Vue 3 + SQLModel + Tailwind CSS v4

---

## 文件结构

| 文件 | 职责 |
|------|------|
| `backend/app/api/routes/leaderboard.py` | 排行榜API端点 |
| `backend/app/crud/leaderboard.py` | 排行榜查询逻辑 |
| `tests/integration/test_leaderboard_api.py` | API集成测试 |
| `frontend-v3/src/views/student/Leaderboard.vue` | 排行榜页面 |
| `frontend-v3/src/composables/useLeaderboard.ts` | 排行榜数据获取 |
| `frontend-v3/src/types/api.ts` | 类型定义（如有新增） |
| `frontend-v3/test/views/Leaderboard.spec.ts` | 前端测试 |

---

## Task 1: 后端数据库索引

**Files:**
- Modify: `backend/app/models/student.py`
- Test: 手动验证索引存在

- [x] **Step 1: 给 score 字段添加索引**

```python
# backend/app/models/student.py
# 在 Student 类的 score 字段上添加 index=True
score: float = Field(default=70.0, index=True, description="分数")
```

- [x] **Step 2: 验证索引**

运行 SQL 检查索引:
```bash
cd backend && conda run -n student-manage python -c "
import sqlite3
conn = sqlite3.connect('app/data/class_system.db')
cursor = conn.cursor()
cursor.execute(\"SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='students'\")
print('Indexes:', [r[0] for r in cursor.fetchall()])
conn.close()
"
```

Expected: 包含 `idx_students_score`

---

## Task 2: 后端 CRUD 层

**Files:**
- Create: `backend/app/crud/leaderboard.py`
- Modify: `backend/app/crud/__init__.py`

- [x] **Step 1: 创建 leaderboard CRUD 文件**

```python
# backend/app/crud/leaderboard.py
from typing import List, Optional, Dict, Any
from sqlmodel import Session, select
from app.models import Student


def get_leaderboard(
    session: Session,
    scope: str = "class",
    class_name: Optional[str] = None,
    limit: int = 50,
    current_student_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    获取排行榜数据

    Args:
        session: 数据库会话
        scope: "class" 或 "school"
        class_name: 班级名称（scope=class 时必填）
        limit: 返回数量限制
        current_student_id: 当前登录学生ID（用于获取个人排名）

    Returns:
        {
            "scope": str,
            "students": List[dict],
            "total": int,
            "my_rank": Optional[dict]
        }
    """
    # 构建查询
    query = select(Student).where(Student.is_account_enabled == True)

    if scope == "class" and class_name:
        query = query.where(Student.class_name == class_name)

    # 按分数降序排序
    query = query.order_by(Student.score.desc())

    # 获取前 limit 条
    students = session.exec(query.limit(limit)).all()

    # 计算排名（并列排名）
    ranked_students = []
    current_rank = 0
    previous_score = None

    for student in students:
        if student.score != previous_score:
            current_rank += 1
            previous_score = student.score

        ranked_students.append({
            "rank": current_rank,
            "student_id": student.student_id,
            "name": student.name,
            "class_name": student.class_name,
            "score": student.score
        })

    # 获取当前学生的排名
    my_rank = None
    if current_student_id:
        my_rank = _get_student_rank(session, current_student_id, scope, class_name)

    return {
        "scope": scope,
        "students": ranked_students,
        "total": len(ranked_students),
        "my_rank": my_rank
    }


def _get_student_rank(
    session: Session,
    student_id: str,
    scope: str,
    class_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """获取单个学生的排名信息"""
    # 先获取目标学生
    student = session.exec(
        select(Student).where(Student.student_id == student_id)
    ).first()

    if not student:
        return None

    # 计算该学生的排名
    query = select(Student).where(
        Student.is_account_enabled == True,
        Student.score > student.score
    )

    if scope == "class" and class_name:
        query = query.where(Student.class_name == class_name)

    # 分数更高的学生数量 + 1 = 排名
    higher_count = len(session.exec(query).all())

    return {
        "rank": higher_count + 1,
        "student_id": student.student_id,
        "name": student.name,
        "score": student.score
    }
```

- [x] **Step 2: 导出 CRUD 函数**

```python
# backend/app/crud/__init__.py
# 添加导出
from app.crud.leaderboard import get_leaderboard

__all__ = [
    # ... existing exports ...
    "get_leaderboard",
]
```

- [x] **Step 3: Commit**

```bash
git add backend/app/crud/leaderboard.py backend/app/crud/__init__.py
git commit -m "feat: add leaderboard CRUD functions"
```

---

## Task 3: 后端 API 端点

**Files:**
- Create: `backend/app/api/routes/leaderboard.py`
- Modify: `backend/app/api/routes/__init__.py`

- [x] **Step 1: 创建 API 路由文件**

```python
# backend/app/api/routes/leaderboard.py
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from app.core.db import get_session
from app.core.jwt import get_current_user
from app.crud import get_leaderboard
from app.models.constants import ApiResponseConst, ApiResponse

router = APIRouter(tags=["leaderboard"])


class LeaderboardResponse(ApiResponse[dict]):
    """排行榜响应"""
    pass


@router.get("/students/leaderboard", response_model=LeaderboardResponse)
def get_student_leaderboard(
    scope: str = Query("class", description="范围: class 或 school"),
    class_name: Optional[str] = Query(None, description="班级名称（scope=class 时）"),
    limit: int = Query(50, ge=1, le=100, description="返回数量限制"),
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """
    获取学生排行榜

    - scope=class: 返回同班级排名
    - scope=school: 返回全校排名
    """
    # 获取当前学生ID
    current_student_id = None
    if user.get("role") == "student":
        current_student_id = user.get("sub")

    # 如果 scope=class 但没有提供 class_name，尝试从学生信息获取
    if scope == "class" and not class_name and current_student_id:
        from app.crud import get_student
        student = get_student(session, current_student_id)
        if student:
            class_name = student.class_name

    data = get_leaderboard(
        session,
        scope=scope,
        class_name=class_name,
        limit=limit,
        current_student_id=current_student_id
    )

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: data
    }
```

- [x] **Step 2: 注册路由**

```python
# backend/app/api/routes/__init__.py
from app.api.routes.leaderboard import router as leaderboard_router

# 在 include_router 部分添加
app.include_router(leaderboard_router, prefix="/api/v1")
```

- [x] **Step 3: Commit**

```bash
git add backend/app/api/routes/leaderboard.py backend/app/api/routes/__init__.py
git commit -m "feat: add leaderboard API endpoint"
```

---

## Task 4: 后端集成测试

**Files:**
- Create: `tests/integration/test_leaderboard_api.py`

- [x] **Step 1: 编写测试**

```python
# tests/integration/test_leaderboard_api.py
import pytest


class TestLeaderboardAPI:
    """排行榜 API 集成测试"""

    def test_get_class_leaderboard(self, student_client, sample_students):
        """测试获取班级排行榜"""
        # 学生登录
        student_client.post("/api/v1/login", json={
            "username": "S001",
            "password": "student123",
            "role": "student"
        })

        response = student_client.get("/api/v1/students/leaderboard?scope=class")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["scope"] == "class"
        assert len(data["data"]["students"]) > 0
        assert "my_rank" in data["data"]

    def test_get_school_leaderboard(self, student_client, sample_students):
        """测试获取全校排行榜"""
        student_client.post("/api/v1/login", json={
            "username": "S001",
            "password": "student123",
            "role": "student"
        })

        response = student_client.get("/api/v1/students/leaderboard?scope=school")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["scope"] == "school"

    def test_leaderboard_ranking_order(self, student_client, sample_students):
        """测试排行榜按分数降序排列"""
        student_client.post("/api/v1/login", json={
            "username": "S001",
            "password": "student123",
            "role": "student"
        })

        response = student_client.get("/api/v1/students/leaderboard?scope=school")
        data = response.json()

        students = data["data"]["students"]
        scores = [s["score"] for s in students]

        # 验证分数降序
        assert scores == sorted(scores, reverse=True)

    def test_leaderboard_limit_parameter(self, student_client, sample_students):
        """测试 limit 参数限制返回数量"""
        student_client.post("/api/v1/login", json={
            "username": "S001",
            "password": "student123",
            "role": "student"
        })

        response = student_client.get("/api/v1/students/leaderboard?limit=5")
        data = response.json()

        assert len(data["data"]["students"]) <= 5

    def test_leaderboard_unauthorized(self, client):
        """测试未登录无法访问排行榜"""
        response = client.get("/api/v1/students/leaderboard")
        assert response.status_code == 401
```

- [x] **Step 2: 运行测试**

```bash
cd /home/yufeng/student-manager
pytest tests/integration/test_leaderboard_api.py -v
```

Expected: 5 passed

- [x] **Step 3: Commit**

```bash
git add tests/integration/test_leaderboard_api.py
git commit -m "test: add leaderboard API integration tests"
```

---

## Task 5: 前端类型定义

**Files:**
- Modify: `frontend-v3/src/types/api.ts`

- [x] **Step 1: 添加排行榜类型**

```typescript
// frontend-v3/src/types/api.ts

// 排行榜学生项
export interface LeaderboardStudent {
  rank: number
  student_id: string
  name: string
  class_name: string
  score: number
}

// 排行榜响应数据
export interface LeaderboardData {
  scope: 'class' | 'school'
  students: LeaderboardStudent[]
  total: number
  my_rank: {
    rank: number
    student_id: string
    name: string
    score: number
  } | null
}
```

- [x] **Step 2: Commit**

```bash
git add frontend-v3/src/types/api.ts
git commit -m "types: add leaderboard types"
```

---

## Task 6: 前端 API 层

**Files:**
- Create: `frontend-v3/src/api/leaderboard.ts`
- Modify: `frontend-v3/src/api/index.ts`

- [x] **Step 1: 创建 API 文件**

```typescript
// frontend-v3/src/api/leaderboard.ts
import { get } from '@/lib/api'
import type { LeaderboardData } from '@/types'

export interface LeaderboardParams {
  scope?: 'class' | 'school'
  class_name?: string
  limit?: number
}

export const leaderboardApi = {
  getLeaderboard: (params: LeaderboardParams = {}): Promise<LeaderboardData> => {
    const query = new URLSearchParams()
    if (params.scope) query.append('scope', params.scope)
    if (params.class_name) query.append('class_name', params.class_name)
    if (params.limit) query.append('limit', params.limit.toString())

    return get(`/students/leaderboard?${query.toString()}`)
  }
}
```

- [x] **Step 2: 导出 API**

```typescript
// frontend-v3/src/api/index.ts
export { leaderboardApi } from './leaderboard'
```

- [x] **Step 3: Commit**

```bash
git add frontend-v3/src/api/leaderboard.ts frontend-v3/src/api/index.ts
git commit -m "feat: add leaderboard API client"
```

---

## Task 7: 前端 Composable

**Files:**
- Create: `frontend-v3/src/composables/useLeaderboard.ts`

- [x] **Step 1: 创建 Composable**

```typescript
// frontend-v3/src/composables/useLeaderboard.ts
import { useQuery } from '@tanstack/vue-query'
import { computed, type Ref } from 'vue'
import { leaderboardApi, type LeaderboardParams } from '@/api/leaderboard'

export function useLeaderboard(params?: LeaderboardParams | Ref<LeaderboardParams>) {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['leaderboard', params],
    queryFn: async () => {
      const resolvedParams = params && 'value' in params ? params.value : params
      return await leaderboardApi.getLeaderboard(resolvedParams || {})
    },
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  })

  return {
    data,
    isPending,
    error,
    refetch,
    students: computed(() => data.value?.students || []),
    myRank: computed(() => data.value?.my_rank || null),
    total: computed(() => data.value?.total || 0),
  }
}
```

- [x] **Step 2: Commit**

```bash
git add frontend-v3/src/composables/useLeaderboard.ts
git commit -m "feat: add useLeaderboard composable"
```

---

## Task 8: 前端排行榜页面

**Files:**
- Create: `frontend-v3/src/views/student/Leaderboard.vue`
- Modify: `frontend-v3/src/router/index.ts`

- [x] **Step 1: 创建页面组件**

```vue
<!-- frontend-v3/src/views/student/Leaderboard.vue -->
<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores'
import { useLeaderboard } from '@/composables/useLeaderboard'
import { Card, Badge, Button } from '@/components/ui'
import { Trophy, Medal, Award, Users, School, Loader2, User } from 'lucide-vue-next'

const authStore = useAuthStore()
const currentStudentId = computed(() => authStore.user?.id)

const activeTab = ref<'class' | 'school'>('class')

const { data, isPending, students, myRank } = useLeaderboard(
  computed(() => ({ scope: activeTab.value, limit: 50 }))
)

// 前三名样式
const getRankStyle = (rank: number) => {
  switch (rank) {
    case 1: return { icon: Trophy, color: 'text-yellow-400', bg: 'bg-yellow-400/20' }
    case 2: return { icon: Medal, color: 'text-gray-300', bg: 'bg-gray-300/20' }
    case 3: return { icon: Award, color: 'text-amber-600', bg: 'bg-amber-600/20' }
    default: return { icon: null, color: 'text-white/60', bg: 'bg-white/10' }
  }
}

// 是否当前登录学生
const isCurrentStudent = (studentId: string) => {
  return studentId === currentStudentId.value
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-white">
        排行榜
      </h1>
      <p class="text-white/60">
        查看班级和全校排名
      </p>
    </div>

    <!-- Tab Switch -->
    <div class="flex gap-2">
      <Button
        :variant="activeTab === 'class' ? 'default' : 'outline'"
        @click="activeTab = 'class'"
      >
        <Users class="mr-2 h-4 w-4" />
        班级榜
      </Button>
      <Button
        :variant="activeTab === 'school' ? 'default' : 'outline'"
        @click="activeTab = 'school'"
      >
        <School class="mr-2 h-4 w-4" />
        全校榜
      </Button>
    </div>

    <!-- My Rank Card -->
    <Card
      v-if="myRank"
      class="border-primary/30 bg-primary/5 p-4"
    >
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-full bg-primary/20">
            <User class="h-5 w-5 text-primary" />
          </div>
          <div>
            <p class="text-sm text-white/60">我的排名</p>
            <p class="text-lg font-bold text-white">
              第 {{ myRank.rank }} 名
            </p>
          </div>
        </div>
        <div class="text-right">
          <p class="text-2xl font-bold text-primary">
            {{ myRank.score }}
          </p>
          <p class="text-sm text-white/40">分</p>
        </div>
      </div>
    </Card>

    <!-- Loading -->
    <div
      v-if="isPending"
      class="flex h-64 items-center justify-center"
    >
      <Loader2 class="h-8 w-8 animate-spin text-primary" />
    </div>

    <!-- Leaderboard Table -->
    <Card
      v-else
      class="border-white/10 bg-white/[0.02] overflow-hidden"
    >
      <table class="w-full">
        <thead>
          <tr class="border-b border-white/10">
            <th class="px-4 py-3 text-left text-sm font-medium text-white/60">排名</th>
            <th class="px-4 py-3 text-left text-sm font-medium text-white/60">姓名</th>
            <th
              v-if="activeTab === 'school'"
              class="px-4 py-3 text-left text-sm font-medium text-white/60"
            >
              班级
            </th>
            <th class="px-4 py-3 text-right text-sm font-medium text-white/60">分数</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="student in students"
            :key="student.student_id"
            :class="[
              'border-b border-white/5 last:border-0',
              isCurrentStudent(student.student_id) ? 'bg-primary/10' : 'hover:bg-white/[0.02]'
            ]"
          >
            <td class="px-4 py-3">
              <div class="flex items-center gap-2">
                <div
                  v-if="getRankStyle(student.rank).icon"
                  :class="['flex h-8 w-8 items-center justify-center rounded-full', getRankStyle(student.rank).bg]"
                >
                  <component
                    :is="getRankStyle(student.rank).icon"
                    class="h-4 w-4"
                    :class="getRankStyle(student.rank).color"
                  />
                </div>
                <span
                  v-else
                  class="flex h-8 w-8 items-center justify-center text-sm text-white/60"
                >
                  {{ student.rank }}
                </span>
              </div>
            </td>
            <td class="px-4 py-3">
              <div class="flex items-center gap-2">
                <span class="font-medium text-white">{{ student.name }}</span>
                <Badge
                  v-if="isCurrentStudent(student.student_id)"
                  variant="primary"
                  class="text-xs"
                >
                  我
                </Badge>
              </div>
            </td>
            <td
              v-if="activeTab === 'school'"
              class="px-4 py-3 text-white/60"
            >
              {{ student.class_name }}
            </td>
            <td class="px-4 py-3 text-right">
              <span class="text-lg font-bold text-primary">
                {{ student.score }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Empty State -->
      <div
        v-if="students.length === 0"
        class="py-12 text-center text-white/40"
      >
        暂无数据
      </div>
    </Card>
  </div>
</template>
```

- [x] **Step 2: 添加路由**

```typescript
// frontend-v3/src/router/index.ts
// 在 student routes 中添加
{
  path: '/student',
  component: () => import('@/layouts/DashboardLayout.vue'),
  meta: { role: UserRoleConst.STUDENT },
  children: [
    // ... existing routes ...
    {
      path: 'leaderboard',
      name: 'StudentLeaderboard',
      component: () => import('@/views/student/Leaderboard.vue'),
    },
  ],
}
```

- [x] **Step 3: Commit**

```bash
git add frontend-v3/src/views/student/Leaderboard.vue frontend-v3/src/router/index.ts
git commit -m "feat: add student leaderboard page"
```

---

## Task 9: 前端测试

**Files:**
- Create: `frontend-v3/test/views/Leaderboard.spec.ts`

- [x] **Step 1: 编写测试**

```typescript
/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import Leaderboard from '@/views/student/Leaderboard.vue'

// Mock auth store
vi.mock('@/stores', () => ({
  useAuthStore: () => ({
    user: { id: 'S001', name: '张三', role: 'student' }
  })
}))

// Mock composable
vi.mock('@/composables/useLeaderboard', () => ({
  useLeaderboard: () => ({
    data: ref({
      scope: 'class',
      students: [
        { rank: 1, student_id: 'S002', name: '李四', class_name: '一班', score: 95 },
        { rank: 2, student_id: 'S001', name: '张三', class_name: '一班', score: 88 },
        { rank: 3, student_id: 'S003', name: '王五', class_name: '一班', score: 82 },
      ],
      total: 3,
      my_rank: { rank: 2, student_id: 'S001', name: '张三', score: 88 }
    }),
    isPending: ref(false),
    students: ref([
      { rank: 1, student_id: 'S002', name: '李四', class_name: '一班', score: 95 },
      { rank: 2, student_id: 'S001', name: '张三', class_name: '一班', score: 88 },
      { rank: 3, student_id: 'S003', name: '王五', class_name: '一班', score: 82 },
    ]),
    myRank: ref({ rank: 2, student_id: 'S001', name: '张三', score: 88 })
  })
}))

describe('Leaderboard', () => {
  const createWrapper = () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } }
    })

    return mount(Leaderboard, {
      global: {
        plugins: [[VueQueryPlugin, { queryClient }]]
      }
    })
  }

  it('renders leaderboard title', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('排行榜')
  })

  it('displays tab buttons', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('班级榜')
    expect(wrapper.text()).toContain('全校榜')
  })

  it('shows my rank card', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('我的排名')
    expect(wrapper.text()).toContain('第 2 名')
  })

  it('displays student list', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('李四')
    expect(wrapper.text()).toContain('张三')
    expect(wrapper.text()).toContain('王五')
  })

  it('highlights current student', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('我')
  })
})
```

- [x] **Step 2: 运行测试**

```bash
cd frontend-v3
pnpm test:run test/views/Leaderboard.spec.ts
```

Expected: 测试通过

- [x] **Step 3: Commit**

```bash
git add frontend-v3/test/views/Leaderboard.spec.ts
git commit -m "test: add leaderboard page tests"
```

---

## Task 10: 验证完成 (superpowers:verification-before-completion)

**运行所有验证：**

- [x] **Step 1: 后端测试**

```bash
cd /home/yufeng/student-manager
pytest tests/integration/test_leaderboard_api.py -v
```

Expected: 5 passed

- [x] **Step 2: 前端类型检查**

```bash
cd frontend-v3
pnpm vue-tsc --noEmit
```

Expected: No errors

- [x] **Step 3: 前端测试**

```bash
pnpm test:run
```

Expected: All tests pass

- [x] **Step 4: 手动验证**

1. 启动后端: `make dev-backend`
2. 启动前端: `make dev-frontend`
3. 学生登录，访问 `/student/leaderboard`
4. 验证：
   - [ ] 班级榜显示正常
   - [ ] 全校榜显示正常
   - [ ] 排名前3有特殊图标
   - [ ] 当前学生高亮显示
   - [ ] 我的排名卡片显示正确

---

## Task 11: 代码优化 (code-simplifier)

可选：运行 code-simplifier 检查是否有优化空间

---

## Task 12: 代码审查 (superpowers:requesting-code-review)

提交前进行代码审查

---

## Summary

实施计划包含 12 个任务，按顺序执行：
1. 数据库索引
2. 后端 CRUD
3. 后端 API
4. 后端测试
5. 前端类型
6. 前端 API
7. 前端 Composable
8. 前端页面
9. 前端测试
10. 验证完成
11. 代码优化（可选）
12. 代码审查

每个任务都有明确的文件路径、代码示例和验证步骤。
