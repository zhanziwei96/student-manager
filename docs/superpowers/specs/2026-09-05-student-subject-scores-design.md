# 学生科目分数子项目设计文档

---

**文档版本**: v1.0  
**生成时间**: 2026-09-05  
**状态**: ✅ 已获用户确认（基于代码分析验证）  
**子项目**: 1/2（学生科目分数；子项目 2 为小组科目分数）  
**关联文档**: [学期 P0 设计文档](2026-09-04-semester-archive-p0-design.md)

---

## 1. 背景与目标

当前系统只有单一分数（`students.score`），无法支持"学生按科目独立管理分数"的需求。本子项目引入科目维度，实现：

- 学生按科目独立管理分数（数学、语文、英语等各科目独立）
- 小组按科目划分（子项目 2 实现）
- 排行榜按教师+科目聚合（如"张老师的数学"）

**目标**：开学后学生可以按科目查看自己的分数和排名，教师可以按科目给学生加减分。

## 2. 已确认的决策（需求澄清记录）

| 决策点 | 结论 | 验证方式 |
|--------|------|---------|
| 范围拆分 | 拆分为两个子项目（先做学生科目分数，后做小组科目分数） | 用户确认 |
| 科目来源 | 从课表自动推导（course_schedules.course_name）+ 可手动修改（科目管理页面） | 用户确认 |
| 科目隔离 | **全局共享**（subjects 表无 class_name）+ 教师维度（student_subject_scores 加 teacher_id） | 用户确认 + 代码验证 |
| 教师关联 | 学生分数表加 teacher_id（记录哪个老师教的） | 用户确认 |
| 分数继承 | **每学期清零**；学期中换老师继承当前分数 | 用户确认 |
| 排行榜 | 按教师+科目聚合（如"张老师的数学"） | 用户确认 |
| 科目管理 | 需要科目管理页面（admin/教师可查看/修改科目名称） | 用户确认 |

## 3. 基于代码分析的验证

### 3.1 关键假设验证

| 假设 | 验证结果 | 代码证据 |
|------|---------|---------|
| 课表有 teacher_id | ✅ 成立 | `backend/app/models/course_schedule.py:15` |
| 同一班级同一科目可能有多个老师 | ⚠️ 成立（正课+实验） | 课表查重键含 teacher_name（`backend/app/crud/schedule.py:220-228`） |
| 学生分数更新有乐观锁 | ✅ 成立 | `backend/app/crud/student.py:166-209` |
| 排行榜接口可改造 | ✅ 成立 | `backend/app/api/routes/leaderboard.py:18-56` |
| 学生 Dashboard 可改造 | ✅ 成立 | `frontend-v3/src/views/student/Dashboard.vue:19` |

### 3.2 修正点

| 问题 | 修正方案 |
|------|---------|
| 同一班级同一科目可能有多个老师 | 取第一个课表的 teacher_id（正课老师） |
| 课表无 PUT 接口（换老师触发点） | 科目管理页手动触发（不换课表） |
| 学期切换初始化 | rollover 脚本扩展（本学期不需要，未来学期需要） |

## 4. 设计

### 4.1 数据模型

**新建 subjects 表**（全局科目）：

```python
class Subject(SQLModel, table=True):
    """科目表（全局共享，从课表推导）"""
    __tablename__ = "subjects"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(..., description="科目名称（如'数学'）", max_length=100)
    semester: str = Field(default_factory=get_current_term, description="学期标识", max_length=20, index=True)
    created_at: datetime = Field(default_factory=get_now, description="创建时间")

    __table_args__ = (
        sa.UniqueConstraint("name", "semester", name="uix_subject_name_semester"),
    )
```

**新建 student_subject_scores 表**（学生-科目-教师-分数-学期）：

```python
class StudentSubjectScore(SQLModel, table=True):
    """学生科目分数表（按科目独立管理）"""
    __tablename__ = "student_subject_scores"

    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str = Field(..., description="学号", max_length=50, index=True)
    subject_id: int = Field(..., foreign_key="subjects.id", description="科目ID", index=True)
    teacher_id: int = Field(..., foreign_key="users.id", description="教师ID", index=True)
    score: float = Field(default=70.0, description="分数", index=True)
    semester: str = Field(default_factory=get_current_term, description="学期标识", max_length=20, index=True)
    created_at: datetime = Field(default_factory=get_now, description="创建时间")
    updated_at: datetime = Field(default_factory=get_now, description="更新时间")

    __table_args__ = (
        sa.UniqueConstraint("student_id", "subject_id", "teacher_id", "semester", name="uix_student_subject_teacher_semester"),
    )
```

**新建 student_subject_score_logs 表**（分数变更日志）：

```python
class StudentSubjectScoreLog(SQLModel, table=True):
    """学生科目分数变更日志表"""
    __tablename__ = "student_subject_score_logs"
    __table_args__ = (
        Index('idx_subject_score_logs_student_created_at', 'student_id', desc('created_at')),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str = Field(..., description="学号")
    subject_id: int = Field(..., description="科目ID")
    teacher_id: int = Field(..., description="教师ID（操作时的授课教师）")
    old_score: Optional[float] = Field(default=None, description="旧分数")
    new_score: Optional[float] = Field(default=None, description="新分数")
    delta: Optional[float] = Field(default=None, description="变化值")
    reason: Optional[str] = Field(default=None, description="原因")
    operator: Optional[str] = Field(default=None, description="操作人")
    semester: str = Field(default_factory=get_current_term, description="学期标识", max_length=20)
    created_at: datetime = Field(default_factory=get_now, description="创建时间")
```

### 4.2 科目推导与管理

**从课表自动推导**（开学时手动触发）：

```python
def derive_subjects_and_teachers(session: Session) -> Dict[str, Dict[str, int]]:
    """从课表推导科目和教师（当前学期）

    Returns:
        Dict[class_name, Dict[subject_name, teacher_id]]
        如：{"1班": {"数学": 张老师id, "语文": 李老师id}}
    """
    schedules = session.exec(
        select(CourseSchedule).where(CourseSchedule.semester == get_current_term())
    ).all()

    result = {}
    for schedule in schedules:
        if schedule.class_name not in result:
            result[schedule.class_name] = {}
        # 同一班级同一科目可能有多个老师（正课+实验），取第一个
        if schedule.course_name not in result[schedule.class_name]:
            result[schedule.class_name][schedule.course_name] = schedule.teacher_id

    return result
```

**科目管理页面**（admin/教师）：
- 列表：显示当前学期所有科目
- 修改：改科目名称（不影响学生分数记录）
- 从课表推导：手动触发（开学时）

### 4.3 分数管理逻辑

**学生分数初始化**（学期切换时，rollover 脚本扩展）：

```python
def init_student_subject_scores(session: Session, new_semester: str):
    """学期切换时初始化学生科目分数（清零）

    前提：新学期课表已导入
    """
    # 推导科目和教师
    subject_teachers = derive_subjects_and_teachers(session)

    # 为每个学生每个科目新建记录（score=0，teacher_id 从课表推导）
    for student in get_students(session, include_disabled=False):
        class_name = student.class_name
        if class_name in subject_teachers:
            for subject_name, teacher_id in subject_teachers[class_name].items():
                # 查科目 ID
                subject = session.exec(
                    select(Subject).where(Subject.name == subject_name, Subject.semester == new_semester)
                ).first()
                if subject:
                    # 新建记录
                    score_record = StudentSubjectScore(
                        student_id=student.student_id,
                        subject_id=subject.id,
                        teacher_id=teacher_id,
                        score=70.0,  # 默认分数
                        semester=new_semester,
                    )
                    session.add(score_record)

    session.commit()
```

**学期中换老师**（继承当前分数，手动触发）：

```python
def transfer_student_to_new_teacher(
    session: Session,
    subject_id: int,
    old_teacher_id: int,
    new_teacher_id: int,
):
    """学期中换老师（继承当前分数）"""
    # 查当前学期该科目该老师的所有学生
    students = session.exec(
        select(StudentSubjectScore).where(
            StudentSubjectScore.subject_id == subject_id,
            StudentSubjectScore.teacher_id == old_teacher_id,
            StudentSubjectScore.semester == get_current_term(),
        )
    ).all()

    for record in students:
        # 新建记录（新老师，继承当前分数）
        new_record = StudentSubjectScore(
            student_id=record.student_id,
            subject_id=subject_id,
            teacher_id=new_teacher_id,
            score=record.score,  # 继承当前分数
            semester=get_current_term(),
        )
        session.add(new_record)

    session.commit()
```

**加减分**（复用学生分数乐观锁逻辑）：

```python
def update_student_subject_score(
    session: Session,
    student_id: str,
    subject_id: int,
    delta: float,
    reason: str,
    operator: str,
) -> Optional[StudentSubjectScore]:
    """更新学生科目分数（乐观锁 + 日志，复用学生分数逻辑）"""
    # 查当前记录（当前学期）
    # 计算新分数
    # 乐观锁更新
    # 写日志
    # 发布事件
    pass
```

### 4.4 API 接口

**科目管理**（admin/教师）：

```python
GET /api/v1/subjects
→ {success: true, data: [{id: 1, name: "数学", semester: "2026-2027-1"}, ...]}

PUT /api/v1/subjects/{id}
body: {"name": "新名称"}
→ {success: true, message: "科目已更新"}

POST /api/v1/subjects/derive
→ {success: true, message: "已推导 X 个科目"}

POST /api/v1/subjects/{id}/transfer-teacher
body: {"old_teacher_id": 1, "new_teacher_id": 2}
→ {success: true, message: "已转移 X 名学生"}
```

**学生科目分数**（教师/学生）：

```python
GET /api/v1/students/{student_id}/subjects
→ {success: true, data: [{subject_id: 1, subject_name: "数学", score: 85, teacher_name: "张老师"}, ...]}

GET /api/v1/students/{student_id}/subjects/{subject_id}/score
→ {success: true, data: {score: 85, teacher_name: "张老师"}}

PUT /api/v1/students/{student_id}/subjects/{subject_id}/score
body: {"score_change": 5, "reason": "课堂表现"}
→ {success: true, message: "分数已更新"}

GET /api/v1/students/{student_id}/subjects/{subject_id}/logs
→ {success: true, data: [{old_score: 80, new_score: 85, delta: 5, reason: "课堂表现", ...}]}
```

**排行榜**（按教师+科目聚合）：

```python
GET /api/v1/students/leaderboard?subject_id=1&teacher_id=2
→ {success: true, data: {students: [...], my_rank: {...}}}

GET /api/v1/students/leaderboard?subject_id=1
→ {success: true, data: {students: [...], my_rank: {...}}}

GET /api/v1/students/leaderboard?teacher_id=2
→ {success: true, data: {subjects: [{subject_id: 1, subject_name: "数学", students: [...]}]}}
```

### 4.5 前端改造

**科目管理页**（新建 `views/admin/Subjects.vue` 或 `views/teacher/Subjects.vue`）：
- 列表：当前学期所有科目（卡片式）
- 修改科目名称（弹窗）
- 换老师（弹窗：选旧老师 + 新老师）
- 从课表推导（按钮，开学时手动触发）

**学生管理页**（改造 `views/admin/Students.vue` 和 `views/teacher/Students.vue`）：
- 学生列表加"科目分数"展开列（点击展开该学生所有科目分数）
- 分数管理改为按科目（下拉选科目 + 加减分）

**学生 Dashboard**（改造 `views/student/Dashboard.vue`）：
- "我的科目"卡片列表（每个科目一张卡片：科目名 + 分数 + 排名）
- 点击卡片进入科目详情页（该科目的分数历史）

**排行榜页**（改造 `views/student/Leaderboard.vue`）：
- 加科目筛选器（下拉选科目）
- 加教师筛选器（下拉选教师）
- 默认显示当前学期第一个科目

### 4.6 测试策略

**后端测试**：
- 单元测试：科目推导、分数初始化、换老师继承、加减分乐观锁
- 集成测试：科目管理 API、学生科目分数 API、排行榜按教师+科目聚合
- 学期切换测试：rollover 脚本扩展（学生科目分数初始化）

**前端测试**：
- 科目管理页组件测试
- 学生管理页科目分数展示测试
- 学生 Dashboard 多科目展示测试
- 排行榜筛选器测试

**回归**：
- 全量测试（现有 765+225 用例必须全绿）
- 学生分数更新、排行榜、Dashboard 排名等现有功能不受影响

## 5. 范围外（本次不做）

- **小组科目分数**（子项目 2，后续实施）
- **rollover 脚本的学生科目分数初始化**（本学期不需要，未来学期需要时再实现）
- **课表修改时自动换老师**（手动触发，避免误操作）
- **学生个人分数与科目分数的关联**（独立管理，不影响）

## 6. 成功标准

1. 学生可以按科目查看自己的分数和排名（Dashboard"我的科目"卡片列表）
2. 教师可以按科目给学生加减分（学生管理页科目筛选 + 加减分）
3. 排行榜按教师+科目聚合（如"张老师的数学"排名）
4. 学期切换时学生科目分数清零（新学期从 0 开始）
5. 学期中换老师时继承当前分数（科目管理页手动触发）
6. 全量测试回归通过（765+225 用例全绿）

---

**设计确认**：基于代码分析验证，所有假设已确认，修正点已补充。
