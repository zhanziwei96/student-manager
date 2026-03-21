# 测试速查

## 快速运行

```bash
# 全部测试
pytest tests/ -v

# 仅冒烟测试（3秒）
pytest tests/integration/test_smoke.py -v

# 仅单元测试
pytest tests/unit -v

# 仅集成测试
pytest tests/integration -v
```

## 测试结构

| 层级 | 数量 | 位置 |
|------|------|------|
| Domain | 100 | `tests/unit/domain/` |
| Application | 33 | `tests/unit/application/` |
| Infrastructure | 55 | `tests/unit/infrastructure/` |
| Integration | 24 | `tests/integration/` |
| **总计** | **212** | |

## 冒烟测试内容

```bash
pytest tests/integration/test_smoke.py -v
```

覆盖流程:
1. 管理员登录
2. 创建学生
3. 查询学生列表
4. 更新学生分数
5. 创建教师用户
6. 切换用户登录
7. 权限验证
8. 登出

## 系统测试步骤

详细步骤见 [tests/README.md](../tests/README.md)

简要流程:
1. 启动所有服务（后端、前端、Redis）
2. 访问 http://localhost:3000
3. 使用 admin/admin123 登录
4. 测试学生 CRUD
5. 测试签到功能
6. 测试用户管理

## 覆盖率

```bash
pip install pytest-cov
pytest tests/ --cov=backend --cov-report=html
open htmlcov/index.html
```
