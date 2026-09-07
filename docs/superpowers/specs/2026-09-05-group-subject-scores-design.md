# 小组科目分数子项目设计文档

---

**文档版本**: v1.0  
**生成时间**: 2026-09-05  
**状态**: ✅ 已获用户确认  
**子项目**: 2/2（小组科目分数；子项目 1 为学生科目分数）  
**关联文档**: [学生科目分数设计](2026-09-05-student-subject-scores-design.md)

---

## 1. 背景与目标

子项目 1 已实现学生按科目独立管理分数（subjects + student_subject_scores 表）。本子项目实现小组层面的科目分数：

- 小组按科目划分（groups 表加 subject_id）
- 小组有平时分（可加减分，复用学生分数模式）
- 小组排行榜（按科目+班级排小组）

**目标**：教师可以按科目管理小组，给小组加减分，查看小组排行榜。

## 2. 已确认的决策

| 决策点 | 结论 |
|--------|------|
| 小组科目划分 | groups 表加 subject_id（外键 subjects.id，子项目 1 已建） |
| 小组分数 | groups 表加 score（默认 0） |
| 小组分数独立性 | 小组分数独立于学生个人分（不影响） |
| 小组分数默认 | **0 分** |
| 小组排行榜 | 需要（按科目+班级排小组） |
| 默认分变更 | **config.py default_score 70 → 0**（学生个人分和科目分数都从 0 开始） |

## 3. 数据模型

### 3.1 groups 表改造

```python
class Group(SQLModel, table=True):
    """小组表"""
    __tablename__ = "groups"

    id: Optional[int] = Field(default=None, primary_key=True)
    semester: Optional[str] = Field(default_factory=get_current_term, ..., index=True)
    class_name: str = Field(..., description="班级名称", max_length=100, index=True)
    subject_id: Optional[int] = Field(default=None, foreign_key="subjects.id", description="科目ID（小组按科目划分）", index=True)  # 新增
    name: str = Field(..., description="小组名称", max_length=100)
    leader_student_id: str = Field(..., description="组长学号", max_length=50, index=True)
    score: float = Field(default=0.0, description="小组平时分", index=True)  # 新增
    version: int = Field(default=1, description="乐观锁版本号")  # 新增
    is_active: bool = Field(default=True, description="是否有效")
    created_at: datetime = Field(default_factory=get_now, description="创建时间")
```

说明：
- `subject_id` 可空（旧小组回填 null，新小组创建时必填）
- `score` 默认 0（与改后的学生默认分一致）
- `version` 乐观锁（复用学生分数模式，避免 CAS 的 ABA 问题）

### 3.2 group_score_logs 表（新建）

```python
class GroupScoreLog(SQLModel, table=True):
    """小组分数变更日志表"""
    __tablename__ = "group_score_logs"
    __table_args__ = (
        Index('idx_group_score_logs_group_created_at', 'group_id', desc('created_at')),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    group_id: int = Field(..., description="小组ID")
    subject_id: Optional[int] = Field(default=None, description="科目ID")
    old_score: Optional[float] = Field(default=None, description="旧分数")
    new_score: Optional[float] = Field(default=None, description="新分数")
    delta: Optional[float] = Field(default=None, description="变化值")
    reason: Optional[str] = Field(default=None, description="原因")
    operator: Optional[str] = Field(default=None, description="操作人")
    semester: str = Field(default_factory=get_current_term, description="学期标识", max_length=20)
    created_at: datetime = Field(default_factory=get_now, description="创建时间")
```

## 4. 分数管理逻辑

### 4.1 update_group_score（复用学生分数模式）

```python
def update_group_score(
    session: Session,
    group_id: int,
    delta: float,
    reason: str,
    operator: str,
) -> Optional[Group]:
    """更新小组分数（乐观锁 + 日志，复用学生分数逻辑）"""
    # 查当前小组
    group = session.get(Group, group_id)
    if not group:
        return None

    # 计算新分数（0-100 范围）
    old_score = group.score
    new_score = max(min_score, min(max_score, old_score + delta))

    # 乐观锁（version）
    # ... 原生 UPDATE WHERE version=expected_version ...

    # 写日志
    log = GroupScoreLog(...)

    # 发布事件
    # ...

    session.commit()
    return group
```

## 5. API 接口

```python
# 小组分数管理
PUT /api/v1/groups/{group_id}/score
body: {"score_change": 5, "reason": "课堂表现"}
→ {success: true, message: "分数已更新"}

# 小组分数日志
GET /api/v1/groups/{group_id}/score-logs
→ {success: true, data: [{old_score, new_score, delta, reason, operator, created_at}]}

# 小组排行榜
GET /api/v1/groups/leaderboard?subject_id=1&class_name=1班
→ {success: true, data: {groups: [{rank, group_id, group_name, class_name, score}], total}}
```

## 6. 前端改造

- 小组管理页加科目筛选器（从 useSubjects 获取）
- 小组创建时选科目（下拉选 subjects）
- 小组分数展示 + 加减分按钮（复用学生分数管理模式）
- 小组排行榜页（按科目+班级）

## 7. 默认分变更（config.py）

```python
# backend/app/core/config.py
class ScoreSettings(BaseSettings):
    min_score: float = Field(default=0, description="最低分数")
    max_score: float = Field(default=100, description="最高分数")
    default_score: float = Field(default=0, description="学生默认分数")  # 70 → 0
```

影响：
- 学生个人分（students.score）新建时默认 0（create_student 用 default_score）
- 学生科目分数（student_subject_scores.score）默认 0（子项目 1 用 get_settings().score.default_score，自动跟随）
- 需同步更新相关测试断言（原来断言 70.0 的改为 0.0）

## 8. 范围外（本次不做）

- 小组分数与学生个人分的关联（独立，不影响）
- 小组任务的评分机制改造（已有 GroupEvaluationScore，不动）

## 9. 成功标准

1. 小组按科目划分（groups.subject_id）
2. 小组有平时分（score，默认 0），可加减分
3. 小组分数日志可查
4. 小组排行榜（按科目+班级）
5. 默认分变更生效（学生个人分和科目分数默认 0）
6. 全量测试回归通过
