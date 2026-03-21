"""
集成测试共享配置
"""
import sys
import os
import asyncio
import tempfile
import pytest
import pytest_asyncio

# 添加 backend 到路径
backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from httpx import AsyncClient, ASGITransport

# 必须在这些环境变量设置后才能导入 backend 模块
os.environ["ENV"] = "testing"

# 创建临时数据库文件
temp_db_fd, temp_db_path = tempfile.mkstemp(suffix=".db")
os.environ["DATABASE__PATH"] = temp_db_path
os.close(temp_db_fd)


@pytest.fixture(scope="session")
def setup_test_db():
    """初始化测试数据库"""
    from infrastructure.persistence.database import Database
    
    db = Database(temp_db_path, use_pool=False)
    db.init_tables()
    db.run_migrations()
    db.init_indexes()
    
    yield db
    
    # 清理临时文件
    try:
        os.unlink(temp_db_path)
    except:
        pass


@pytest_asyncio.fixture
async def test_app(setup_test_db):
    """创建测试用 FastAPI 应用"""
    from main import app
    
    app.state.test_db = setup_test_db
    
    yield app


@pytest_asyncio.fixture
async def client(test_app):
    """创建异步 HTTP 客户端"""
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
        follow_redirects=False
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def test_user(test_app):
    """创建测试用户并返回用户信息（如果不存在则创建）"""
    from domain.entities.user import User, UserRole
    from domain.value_objects.password import Password
    import uuid
    
    db = test_app.state.test_db
    
    # 使用随机用户名避免冲突
    username = f"teacher_{uuid.uuid4().hex[:8]}"
    
    # 创建用户实体
    user = User(
        username=username,
        name="测试教师",
        password=Password.create_from_plain("password123"),
        role=UserRole.TEACHER
    )
    
    # 保存到数据库
    with db.connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, password_hash, salt, name, role, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user.username,
            user.password.hash_value,
            user.password.salt,
            user.name,
            user.role.value,
            1
        ))
        user.id = cursor.lastrowid
    
    return {
        "id": user.id,
        "username": user.username,
        "password": "password123",
        "name": user.name,
        "role": user.role.value
    }
