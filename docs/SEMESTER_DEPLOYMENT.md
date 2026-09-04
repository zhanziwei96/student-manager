# 第二学期生产部署操作手册

---

**适用时间**: 2026-09-07 开学前（建议上课前 1-2 天的维护窗口）  
**前置条件**: 代码已合并 main 并推送（98b1e92）、第二学期 P0 全部交付  
**开发环境演练**: ✅ 已于 2026-09-04 在本地 PG 完整通过

---

## ⚠️ 执行前检查清单（务必逐项确认）

- [ ] 我已完整读本手册
- [ ] 我已确认当前日期在 2026-09-07 之前
- [ ] 我已准备 pg_dump 可访问生产库（Docker 内）
- [ ] 我已有回滚预案（若中途失败如何恢复）
- [ ] 维护窗口内不会有用户使用系统（通知相关方）

---

## 部署步骤（按顺序执行，每步有验证点）

### 步骤 1：生产数据库备份（强制）

**目的**：任何操作前的安全网，若后续步骤失败可完整回滚。

```bash
# 进入生产服务器
cd /path/to/student-manager

# 全库快照（包含所有表数据）
docker exec classhub-postgres pg_dump -U classhub classhub > \
  backups/postgres/classhub_pre_semester_$(date +%Y%m%d_%H%M%S).sql

# 验证备份文件非空且可读
ls -lh backups/postgres/classhub_pre_semester_*.sql | tail -1
head -5 backups/postgres/classhub_pre_semester_*.sql | tail -1
# 预期: 应看到 "-- PostgreSQL database dump"
```

**验证点**：备份文件大小 > 1MB（上学期 465 学生 + 895 签到 + 1176 分数日志，约 1.5MB）；文件可读。

**若失败**：停止部署，排查 pg_dump 权限/连接问题。

---

### 步骤 2：检查生产库迁移状态（关键）

**目的**：确认生产库的 alembic_version 与 schema 一致，无 create_all 漂移。

```bash
# 进入后端容器
docker exec -it classhub-backend bash

# 检查当前 alembic 版本
alembic current
# 预期输出: 20260904161715 (head)

# 若版本不是 20260904161715，检查漂移
python -c "
import psycopg2, os
url = os.environ.get('DATABASE__URL', 'postgresql+psycopg2://classhub:classhub_secret@postgres:5432/classhub')
# 转为 psycopg2 格式
url = url.replace('postgresql+psycopg2://', 'postgresql://')
conn = psycopg2.connect(url)
cur = conn.cursor()
cur.execute('SELECT version_num FROM alembic_version')
print('alembic_version:', cur.fetchone())
cur.execute(\"SELECT COUNT(*) FROM information_schema.tables WHERE table_name='lost_found_items'\")
print('lost_found_items 存在:', cur.fetchone()[0])
cur.execute(\"SELECT COUNT(*) FROM information_schema.columns WHERE table_name='course_schedules' AND column_name='semester'\")
print('course_schedules.semester 存在:', cur.fetchone()[0])
conn.close()
"
```

**判断分支**：
- ✅ 若 `alembic_version == 20260904161715` 且 `semester 列存在`：跳到步骤 3
- ⚠️ 若 `alembic_version != 20260904161715` 但表结构已对（create_all 漂移）：参考开发库的处理方式 `alembic stamp 20260904161715` 后跳到步骤 3
- ❌ 若表结构不一致：停止部署，先手动处理漂移（参考 [backend/README.md](backend/README.md) 的迁移指南）

**验证点**：`alembic current` 返回 `20260904161715 (head)`。

---

### 步骤 3：应用 semester 迁移

```bash
# 在后端容器内
alembic upgrade head
# 预期: 无报错输出

# 验证迁移结果
python -c "
import psycopg2, os
url = os.environ.get('DATABASE__URL', 'postgresql+psycopg2://classhub:classhub_secret@postgres:5432/classhub')
url = url.replace('postgresql+psycopg2://', 'postgresql://')
conn = psycopg2.connect(url)
cur = conn.cursor()
cur.execute(\"SELECT semester, COUNT(*) FROM course_schedules GROUP BY semester\")
print('课表学期分布:', cur.fetchall())
cur.execute(\"SELECT indexname FROM pg_indexes WHERE tablename='course_sessions' AND indexname='uix_active_class_semester'\")
print('唯一索引存在:', cur.fetchone() is not None)
conn.close()
"
# 预期: 课表全部回填 ('2025-2026-2', N)；索引存在
```

**验证点**：9 张表（course_schedules/course_sessions/schedule_adjustments/checkin_records/score_logs/groups/group_tasks/group_evaluation_scores/questions）都有 semester 列且历史数据回填 `'2025-2026-2'`。

**若失败**：检查数据库权限；从步骤 1 的备份恢复后重试。

---

### 步骤 4：翻新 TERM_CFG__ 配置

**目的**：切换系统当前学期到 2026-2027-1。

```bash
# 编辑生产环境配置
vi backend/.env.production
```

添加或修改以下三行：

```bash
# 学期配置（第二学期）
# 注意：env 键是 TERM_CFG__（validation_alias="term_cfg"），不是 TERM__
TERM_CFG__LABEL=2026-2027-1
TERM_CFG__START_DATE=2026-09-07
TERM_CFG__TOTAL_WEEKS=20
```

**重启后端**（使配置生效）：

```bash
# 按 CLAUDE.md 完整流程：停止→等待3秒→检查残留→启动→等待5秒→验证
docker compose stop backend
sleep 3
docker compose ps backend  # 确认已停止
docker compose up -d backend
sleep 5

# 验证配置生效
curl -s --max-time 10 http://localhost:8000/api/v1/term/current
# 预期: {"success":true,"data":{"term":"2026-2027-1","start_date":"2026-09-07","current_week":0,"total_weeks":20}}
```

**验证点**：`/api/term/current` 返回 `term=2026-2027-1`、`current_week=0`（开学前）。

**若失败**：检查 `.env.production` 语法（JSON 数组格式、无引号）；查看容器日志 `docker logs classhub-backend --tail 50`。

---

### 步骤 5：执行学期切换脚本

**目的**：归档上学期数据（分数清零、课堂/小组收敛、可选毕业生软禁用）。

```bash
# 在后端容器内
cd /app

# （可选）准备毕业生名单文件
# 若有毕业/退学学生，创建名单文件（每行一个学号）
cat > /tmp/graduates.txt << 'EOF'
2513070201
2513070202
# ... 每行一个学号
EOF

# 执行切换脚本
python scripts/semester_rollover.py
# 若禁用毕业生: python scripts/semester_rollover.py --disable-graduates /tmp/graduates.txt

# 脚本会提示确认，输入 y 回车
# 预期输出:
#   [前置检查] 旧学期=2025-2026-2 新学年=2026-2027-1
#   [备份] PostgreSQL 快照已导出: backups/term-2025-2026-2/classhub_*.sql
#   [验证报告]
#     遗留课堂收敛: N
#     小组失效: N  任务关闭: N
#     分数归档: 465  跳过(幂等): 0
#     软禁用学生: N
```

**验证点**：
- 分数归档数 = 学生总数（465）
- 无"跳过(幂等)"（首次执行应为 0；若 >0 说明重复执行，幂等生效）
- 软禁用学生数与预期名单一致

**若失败**：检查 `--old-term` 推导是否正确（脚本会自动从当前 TERM_CFG__LABEL 推导）；若报错"旧学期无数据"，检查库内是否已有 2025-2026-2 标记的数据。

---

### 步骤 6：最终验证

```bash
# 1. 检查分数重置
python -c "
import psycopg2, os
url = os.environ.get('DATABASE__URL', 'postgresql+psycopg2://classhub:classhub_secret@postgres:5432/classhub')
url = url.replace('postgresql+psycopg2://', 'postgresql://')
conn = psycopg2.connect(url)
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM students WHERE score > 0')
print('分数>0 的学生:', cur.fetchone()[0])
cur.execute(\"SELECT COUNT(*) FROM score_logs WHERE reason LIKE '[学期归档]%'\")
print('归档日志数:', cur.fetchone()[0])
conn.close()
"
# 预期: 分数>0 = 0；归档日志数 = 465

# 2. 检查前端页面
curl -s --max-time 10 http://localhost/api/term/current | head -c 200
# 预期: 返回 2026-2027-1

# 3. 登录测试（教师账号）
# 访问前端，登录教师账号，检查课表页/小组页/签到页无上学期数据混入
```

**验证点**：全部通过则部署完成。

---

## 回滚方案

若任一步骤失败且无法修复：

1. **数据库回滚**：
   ```bash
   # 从步骤 1 的备份恢复
   docker exec -i classhub-postgres psql -U classhub -d classhub < \
     backups/postgres/classhub_pre_semester_*.sql
   ```

2. **配置回滚**：恢复 `.env.production` 的 TERM_CFG__ 三行为上学期值（或删除）

3. **代码回滚**：`git checkout <上一版本>` + 重新部署

**回滚后**：系统回到上学期状态，所有数据完整。

---

## 常见问题

**Q: 执行 rollover 时提示"旧学期=当前学期"？**  
A: 说明 TERM_CFG__LABEL 未翻新（步骤 4 未完成）。先完成配置翻新再执行。

**Q: 迁移后某些接口报 500？**  
A: 检查 `alembic current` 是否为 head；查看容器日志定位具体错误。

**Q: 学生登录后看到上学期数据？**  
A: 检查 rollover 是否成功执行（步骤 5）；检查 TERM_CFG__START_DATE 是否正确。

**Q: 需要回滚到上学期？**  
A: 按"回滚方案"执行；或仅回滚配置（TERM_CFG__LABEL 改回 2025-2026-2）即可恢复上学期视图（数据仍完整）。

---

## 部署完成标志

- [ ] 备份文件存在且可读
- [ ] `alembic current` = 20260904161715 (head)
- [ ] 9 张表 semester 列存在且回填 '2025-2026-2'
- [ ] `/api/term/current` 返回 2026-09-07/2026-2027-1
- [ ] 学生分数全部归 0，归档日志 465 条
- [ ] 前端登录正常，课表/小组/签到页无上学期数据

**全部勾选 = 部署成功，第二学期就绪。**

---

**文档版本**: v1.0  
**生成时间**: 2026-09-04  
**演练状态**: ✅ 开发环境已通过  
**关联文档**: [学期 P0 设计文档](docs/superpowers/specs/2026-09-04-semester-archive-p0-design.md)
