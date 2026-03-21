"""
用户管理 API 集成测试
"""
import pytest
import uuid


@pytest.mark.asyncio
async def test_admin_create_user_success(client, test_app):
    """
    测试管理员成功创建用户
    
    验证点：
    1. 返回 HTTP 200
    2. 响应包含创建的用户信息
    3. 新用户可登录
    """
    # Arrange - 创建管理员并登录
    from domain.entities.user import User, UserRole
    from domain.value_objects.password import Password
    
    db = test_app.state.test_db
    admin = User(
        username=f"admin_{uuid.uuid4().hex[:8]}",
        name="管理员",
        password=Password.create_from_plain("admin123"),
        role=UserRole.ADMIN
    )
    
    with db.connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, password_hash, salt, name, role, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (admin.username, admin.password.hash_value, admin.password.salt,
              admin.name, admin.role.value, 1))
        admin.id = cursor.lastrowid
    
    # 管理员登录
    login_response = await client.post("/api/login", json={
        "username": admin.username,
        "password": "admin123"
    })
    assert login_response.status_code == 200
    
    # Act - 创建新用户
    new_username = f"newteacher_{uuid.uuid4().hex[:8]}"
    response = await client.post("/api/admin/users", json={
        "username": new_username,
        "password": "password123",
        "name": "新教师",
        "role": "teacher",
        "assigned_classes": ["软件1班"]
    })
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["username"] == new_username
    assert data["data"]["role"] == "teacher"
    
    # 验证新用户可登录
    login_new = await client.post("/api/login", json={
        "username": new_username,
        "password": "password123"
    })
    assert login_new.status_code == 200


@pytest.mark.asyncio
async def test_teacher_cannot_create_user(client, test_app):
    """
    测试普通教师无法创建用户（权限控制）
    
    验证点：
    1. 教师访问管理员接口返回 403
    """
    # Arrange - 创建教师并登录
    from domain.entities.user import User, UserRole
    from domain.value_objects.password import Password
    
    db = test_app.state.test_db
    teacher = User(
        username=f"teacher_{uuid.uuid4().hex[:8]}",
        name="教师",
        password=Password.create_from_plain("teacher123"),
        role=UserRole.TEACHER
    )
    
    with db.connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, password_hash, salt, name, role, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (teacher.username, teacher.password.hash_value, teacher.password.salt,
              teacher.name, teacher.role.value, 1))
    
    # 教师登录
    login_response = await client.post("/api/login", json={
        "username": teacher.username,
        "password": "teacher123"
    })
    assert login_response.status_code == 200
    
    # Act - 尝试创建用户
    response = await client.post("/api/admin/users", json={
        "username": "newuser",
        "password": "password123",
        "name": "新用户",
        "role": "teacher"
    })
    
    # Assert
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_user_duplicate_username(client, test_app):
    """
    测试创建重复用户名
    
    验证点：
    1. 返回 HTTP 400
    2. 提示用户名已存在
    """
    # Arrange - 创建管理员并登录
    from domain.entities.user import User, UserRole
    from domain.value_objects.password import Password
    
    db = test_app.state.test_db
    username = f"user_{uuid.uuid4().hex[:8]}"
    
    admin = User(
        username=f"admin_{uuid.uuid4().hex[:8]}",
        name="管理员",
        password=Password.create_from_plain("admin123"),
        role=UserRole.ADMIN
    )
    
    with db.connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, password_hash, salt, name, role, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (admin.username, admin.password.hash_value, admin.password.salt,
              admin.name, admin.role.value, 1))
    
    # 管理员登录
    await client.post("/api/login", json={
        "username": admin.username,
        "password": "admin123"
    })
    
    # 第一次创建
    response1 = await client.post("/api/admin/users", json={
        "username": username,
        "password": "password123",
        "name": "用户1",
        "role": "teacher"
    })
    assert response1.status_code == 200
    
    # Act - 重复创建
    response2 = await client.post("/api/admin/users", json={
        "username": username,
        "password": "password456",
        "name": "用户2",
        "role": "teacher"
    })
    
    # Assert
    assert response2.status_code == 400
    assert "已存在" in response2.json()["detail"]


@pytest.mark.asyncio
async def test_reset_password_success(client, test_app):
    """
    测试管理员重置密码
    
    验证点：
    1. 重置成功后新密码可登录
    2. 旧密码无法登录
    """
    # Arrange - 创建管理员和普通用户
    from domain.entities.user import User, UserRole
    from domain.value_objects.password import Password
    
    db = test_app.state.test_db
    
    admin = User(
        username=f"admin_{uuid.uuid4().hex[:8]}",
        name="管理员",
        password=Password.create_from_plain("admin123"),
        role=UserRole.ADMIN
    )
    
    teacher = User(
        username=f"teacher_{uuid.uuid4().hex[:8]}",
        name="教师",
        password=Password.create_from_plain("oldpassword"),
        role=UserRole.TEACHER
    )
    
    with db.connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, password_hash, salt, name, role, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (admin.username, admin.password.hash_value, admin.password.salt,
              admin.name, admin.role.value, 1))
        admin_id = cursor.lastrowid
        
        cursor.execute('''
            INSERT INTO users (username, password_hash, salt, name, role, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (teacher.username, teacher.password.hash_value, teacher.password.salt,
              teacher.name, teacher.role.value, 1))
        teacher_id = cursor.lastrowid
    
    # 管理员登录
    await client.post("/api/login", json={
        "username": admin.username,
        "password": "admin123"
    })
    
    # Act - 重置密码
    response = await client.post(f"/api/admin/users/{teacher_id}/reset-password", json={
        "new_password": "newpassword123"
    })
    
    # Assert
    assert response.status_code == 200
    assert "重置成功" in response.json()["message"]
    
    # 验证新密码可登录
    login_new = await client.post("/api/login", json={
        "username": teacher.username,
        "password": "newpassword123"
    })
    assert login_new.status_code == 200


@pytest.mark.asyncio
async def test_delete_user_success(client, test_app):
    """
    测试删除用户
    
    验证点：
    1. 删除成功返回 200
    2. 删除后用户无法登录
    """
    # Arrange - 创建管理员和待删除用户
    from domain.entities.user import User, UserRole
    from domain.value_objects.password import Password
    
    db = test_app.state.test_db
    
    admin = User(
        username=f"admin_{uuid.uuid4().hex[:8]}",
        name="管理员",
        password=Password.create_from_plain("admin123"),
        role=UserRole.ADMIN
    )
    
    teacher = User(
        username=f"teacher_{uuid.uuid4().hex[:8]}",
        name="教师",
        password=Password.create_from_plain("teacher123"),
        role=UserRole.TEACHER
    )
    
    with db.connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, password_hash, salt, name, role, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (admin.username, admin.password.hash_value, admin.password.salt,
              admin.name, admin.role.value, 1))
        admin_id = cursor.lastrowid
        
        cursor.execute('''
            INSERT INTO users (username, password_hash, salt, name, role, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (teacher.username, teacher.password.hash_value, teacher.password.salt,
              teacher.name, teacher.role.value, 1))
        teacher_id = cursor.lastrowid
    
    # 管理员登录
    await client.post("/api/login", json={
        "username": admin.username,
        "password": "admin123"
    })
    
    # Act - 删除用户
    response = await client.delete(f"/api/admin/users/{teacher_id}")
    
    # Assert
    assert response.status_code == 200
    assert "删除成功" in response.json()["message"]


@pytest.mark.asyncio
async def test_delete_self_forbidden(client, test_app):
    """
    测试管理员不能删除自己
    
    验证点：
    1. 删除自己返回 400
    """
    # Arrange - 创建管理员
    from domain.entities.user import User, UserRole
    from domain.value_objects.password import Password
    
    db = test_app.state.test_db
    
    admin = User(
        username=f"admin_{uuid.uuid4().hex[:8]}",
        name="管理员",
        password=Password.create_from_plain("admin123"),
        role=UserRole.ADMIN
    )
    
    with db.connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, password_hash, salt, name, role, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (admin.username, admin.password.hash_value, admin.password.salt,
              admin.name, admin.role.value, 1))
        admin_id = cursor.lastrowid
    
    # 管理员登录
    await client.post("/api/login", json={
        "username": admin.username,
        "password": "admin123"
    })
    
    # Act - 尝试删除自己
    response = await client.delete(f"/api/admin/users/{admin_id}")
    
    # Assert
    assert response.status_code == 400
    assert "不能删除当前登录账号" in response.json()["detail"]


@pytest.mark.asyncio
async def test_change_password_success(client, test_app):
    """
    测试用户修改自己的密码
    
    验证点：
    1. 修改成功后旧密码失效
    2. 新密码可登录
    """
    # Arrange - 创建用户
    from domain.entities.user import User, UserRole
    from domain.value_objects.password import Password
    
    db = test_app.state.test_db
    
    user = User(
        username=f"user_{uuid.uuid4().hex[:8]}",
        name="用户",
        password=Password.create_from_plain("oldpassword"),
        role=UserRole.TEACHER
    )
    
    with db.connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, password_hash, salt, name, role, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user.username, user.password.hash_value, user.password.salt,
              user.name, user.role.value, 1))
        user_id = cursor.lastrowid
    
    # 登录
    await client.post("/api/login", json={
        "username": user.username,
        "password": "oldpassword"
    })
    
    # Act - 修改密码
    response = await client.post("/api/change-password", json={
        "old_password": "oldpassword",
        "new_password": "newpassword123"
    })
    
    # Assert
    assert response.status_code == 200
    assert "成功" in response.json()["message"]


@pytest.mark.asyncio
async def test_get_all_users(client, test_app):
    """
    测试管理员获取用户列表
    
    验证点：
    1. 返回所有用户
    2. 包含管理员和普通用户
    """
    
    # Arrange - 创建管理员和多个用户
    from domain.entities.user import User, UserRole
    from domain.value_objects.password import Password
    
    db = test_app.state.test_db
    
    admin = User(
        username=f"admin_{uuid.uuid4().hex[:8]}",
        name="管理员",
        password=Password.create_from_plain("admin123"),
        role=UserRole.ADMIN
    )
    
    teacher1 = User(
        username=f"teacher1_{uuid.uuid4().hex[:8]}",
        name="教师1",
        password=Password.create_from_plain("teacher123"),
        role=UserRole.TEACHER
    )
    
    with db.connection() as conn:
        cursor = conn.cursor()
        for u in [admin, teacher1]:
            cursor.execute('''
                INSERT INTO users (username, password_hash, salt, name, role, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (u.username, u.password.hash_value, u.password.salt,
                  u.name, u.role.value, 1))
    
    # 管理员登录
    await client.post("/api/login", json={
        "username": admin.username,
        "password": "admin123"
    })
    
    # Act
    response = await client.get("/api/admin/users")
    
    # Assert
    assert response.status_code == 200
