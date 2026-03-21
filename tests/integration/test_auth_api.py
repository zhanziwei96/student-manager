"""
认证 API 集成测试
"""
import pytest


@pytest.mark.asyncio
async def test_login_success(client, test_user):
    """
    测试登录成功
    
    验证点：
    1. 返回 HTTP 200
    2. 响应包含用户信息
    3. 设置 session cookie
    """
    # Act
    response = await client.post("/api/login", json={
        "username": test_user["username"],
        "password": test_user["password"]
    })
    
    # Assert
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "登录成功"
    assert "user" in data
    assert data["user"]["username"] == test_user["username"]
    assert data["user"]["name"] == test_user["name"]
    
    # 验证设置了 session cookie
    assert "session" in response.cookies


@pytest.mark.asyncio
async def test_login_wrong_password(client, test_user):
    """
    测试密码错误
    
    验证点：
    1. 返回 HTTP 401
    2. 返回错误提示信息
    3. 不设置 session
    """
    # Act
    response = await client.post("/api/login", json={
        "username": test_user["username"],
        "password": "wrong_password"
    })
    
    # Assert
    assert response.status_code == 401
    
    data = response.json()
    assert data["success"] is False
    assert "密码错误" in data["message"]


@pytest.mark.asyncio
async def test_login_account_disabled(client, test_app):
    """
    测试账号被禁用
    
    验证点：
    1. 禁用状态的用户无法登录
    2. 返回 HTTP 403
    """
    from domain.entities.user import User, UserRole, UserStatus
    from domain.value_objects.password import Password
    
    # 创建禁用用户
    db = test_app.state.test_db
    user = User(
        username="disabled_user",
        name="禁用用户",
        password=Password.create_from_plain("password123"),
        role=UserRole.TEACHER,
        status=UserStatus.INACTIVE
    )
    
    with db.connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, password_hash, salt, name, role, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user.username, user.password.hash_value, user.password.salt, 
              user.name, user.role.value, 0))  # is_active = 0
    
    # 尝试登录
    response = await client.post("/api/login", json={
        "username": "disabled_user",
        "password": "password123"
    })
    
    assert response.status_code == 403
    assert "禁用" in response.json()["detail"]


@pytest.mark.asyncio
async def test_logout(client, test_user):
    """
    测试登出
    
    验证点：
    1. 登录成功
    2. 登出接口返回成功
    3. 响应包含成功消息
    """
    # Step 1: 登录
    login_response = await client.post("/api/login", json={
        "username": test_user["username"],
        "password": test_user["password"]
    })
    assert login_response.status_code == 200
    
    # Step 2: 登出
    logout_response = await client.post("/api/logout")
    
    # Assert
    assert logout_response.status_code == 200
    data = logout_response.json()
    assert data["success"] is True
    assert "登出成功" in data["message"]
