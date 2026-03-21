# ClassHub 测试套件

**测试框架**: pytest  
**测试范围**: 冒烟测试、功能测试、接口测试

---

## 目录结构

```
tests/
├── README.md              # 本文档
├── conftest.py            # pytest 配置和 fixtures
├── requirements-test.txt  # 测试依赖
└── smoke/                 # 冒烟测试
    └── test_smoke.py      # 核心流程冒烟测试
```

---

## 快速开始

### 1. 安装测试依赖

```bash
cd /home/yufeng/student-manage-v3-security/student-manager

# 安装测试依赖
pip install pytest pytest-asyncio requests redis

# 或使用 requirements 文件（后续创建）
pip install -r tests/requirements-test.txt
```

### 2. 确保服务已启动

```bash
# 检查后端
curl http://localhost:8000/health

# 检查前端
curl http://localhost:3000

# 检查 Redis
redis-cli ping
```

### 3. 运行冒烟测试

```bash
# 运行所有冒烟测试
cd /home/yufeng/student-manage-v3-security/student-manager
python -m pytest tests/smoke/ -v

# 只运行后端测试
python -m pytest tests/smoke/ -v -m backend

# 只运行前端测试
python -m pytest tests/smoke/ -v -m frontend

# 只运行 Redis 测试
python -m pytest tests/smoke/ -v -m redis
```

---

## 测试标记说明

| 标记 | 说明 | 使用示例 |
|------|------|----------|
| `smoke` | 冒烟测试 | `pytest -m smoke` |
| `backend` | 后端服务测试 | `pytest -m backend` |
| `frontend` | 前端服务测试 | `pytest -m frontend` |
| `redis` | Redis 测试 | `pytest -m redis` |
| `auth` | 认证相关测试 | `pytest -m auth` |

---

## 冒烟测试检查清单

根据 TEST_PLAN.md，冒烟测试验证以下核心流程：

### ✅ 1. 服务启动检查
- [ ] 后端服务运行正常
- [ ] 前端服务运行正常
- [ ] Redis 运行正常

### ✅ 2. 健康检查
- [ ] GET /health 返回 healthy
- [ ] GET /ready 返回 ready
- [ ] GET /live 返回 alive

### ✅ 3. 用户登录
- [ ] admin 能正常登录
- [ ] 错误密码登录失败
- [ ] 不存在的用户登录失败

### ✅ 4. 学生列表
- [ ] 已认证用户能获取学生列表
- [ ] 未认证用户无法获取学生列表

### ✅ 5. 签到功能
- [ ] 签到端点可访问
- [ ] 课堂状态端点可访问

### ✅ 6. 页面导航
- [ ] 首页能正常加载
- [ ] 登录页能正常加载

---

## 测试结果解读

### 全部通过 🎉
```
========================== 9 passed in 2.34s ===========================
🎉 所有冒烟测试通过！核心流程正常。
```

### 部分失败 ⚠️
```
========================== 6 passed, 3 failed ==========================
⚠️  部分测试失败，请检查服务状态。

排查建议:
1. 检查后端: curl http://localhost:8000/health
2. 检查前端: curl http://localhost:3000
3. 检查 Redis: redis-cli ping
4. 查看日志: tail -f backend/backend.log
```

### 全部跳过 ⊘
```
========================== 9 skipped ==========================
⚠️  所有测试都被跳过，请确保服务已启动。
```

---

## 故障排查

### 问题：后端连接失败
```
FAILED tests/smoke/test_smoke.py::TestServiceStartup::test_backend_service_running
后端服务未启动，请运行: cd backend && python main.py
```

**解决**:
```bash
cd backend
source /home/yufeng/miniconda3/bin/activate student-manage
python main.py
```

### 问题：前端连接失败
```
FAILED tests/smoke/test_smoke.py::TestServiceStartup::test_frontend_service_running
前端服务未启动，请运行: cd frontend && pnpm dev
```

**解决**:
```bash
cd frontend
pnpm dev
```

### 问题：Redis 连接失败
```
FAILED tests/smoke/test_smoke.py::TestServiceStartup::test_redis_service_running
Redis 未启动，请运行: redis-server
```

**解决**:
```bash
redis-server
```

---

## 扩展测试

### 添加新的冒烟测试

在 `tests/smoke/test_smoke.py` 中添加：

```python
class TestNewFeature:
    """新功能冒烟测试"""
    
    @pytest.mark.smoke
    @pytest.mark.backend
    @backend_required
    def test_new_feature_works(self):
        """测试新功能是否正常工作"""
        response = requests.get(f"{BASE_URL}/api/new-feature")
        assert response.status_code == 200
```

### 添加功能测试目录

```bash
mkdir tests/functional        # 功能测试
mkdir tests/integration       # 集成测试
mkdir tests/performance       # 性能测试
mkdir tests/security          # 安全测试
```

---

## 参考文档

- [TEST_PLAN.md](../TEST_PLAN.md) - 完整测试方案
- [DEPLOYMENT.md](../DEPLOYMENT.md) - 环境部署指南
- [AGENTS.md](../AGENTS.md) - AI 助手注意事项

---

**维护者**: Kimi Code CLI  
**最后更新**: 2025-03-21
