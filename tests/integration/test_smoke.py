"""
冒烟测试 - 核心业务流程验证

快速验证系统主要功能是否通畅，不依赖外部服务。
运行: pytest tests/integration/test_smoke.py -v
"""
import pytest
import pytest_asyncio
import uuid


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_core_business_workflow(client, test_app):
    """
    核心业务流程冒烟测试
    
    完整流程:
    1. 创建管理员并登录
    2. 创建学生
    3. 查询学生列表
    4. 更新学生分数
    5. 创建教师用户
    6. 切换用户登录
    7. 登出
    
    验证: 全流程无异常，状态码正确
    """
    from domain.entities.user import User, UserRole
    from domain.value_objects.password import Password
    
    db = test_app.state.test_db
    
    # ==========================================
    # Step 1: 创建管理员并登录
    # ==========================================
    admin_username = f"admin_{uuid.uuid4().hex[:8]}"
    admin = User(
        username=admin_username,
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
    login_response = await client.post("/api/login", json={
        "username": admin_username,
        "password": "admin123"
    })
    assert login_response.status_code == 200, "管理员登录失败"
    assert login_response.json()["success"] is True
    print(f"  ✓ 管理员登录成功: {admin_username}")
    
    # ==========================================
    # Step 2: 创建学生
    # ==========================================
    student_id = f"2024{uuid.uuid4().hex[:6]}"
    create_response = await client.post("/api/students", json={
        "student_id": student_id,
        "name": "张三",
        "class_name": "软件1班"
    })
    assert create_response.status_code == 200, "创建学生失败"
    assert create_response.json()["success"] is True
    print(f"  ✓ 创建学生成功: {student_id}")
    
    # ==========================================
    # Step 3: 查询学生列表
    # ==========================================
    list_response = await client.get("/api/students")
    assert list_response.status_code == 200, "获取学生列表失败"
    data = list_response.json()
    assert data["success"] is True
    assert any(s["student_id"] == student_id for s in data["data"]), "新建学生不在列表中"
    print(f"  ✓ 查询学生列表成功，共 {len(data['data'])} 人")
    
    # ==========================================
    # Step 4: 更新学生分数
    # ==========================================
    score_response = await client.post(f"/api/students/{student_id}/score", json={
        "score_change": 10.0,
        "reason": "课堂表现优秀"
    })
    assert score_response.status_code == 200, "更新分数失败"
    assert score_response.json()["success"] is True
    new_score = score_response.json()["data"]["score"]
    assert new_score == 80.0, f"分数更新不正确: {new_score}"
    print(f"  ✓ 更新分数成功: 70.0 -> {new_score}")
    
    # ==========================================
    # Step 5: 创建教师用户
    # ==========================================
    teacher_username = f"teacher_{uuid.uuid4().hex[:8]}"
    create_user_response = await client.post("/api/admin/users", json={
        "username": teacher_username,
        "password": "teacher123",
        "name": "李老师",
        "role": "teacher",
        "assigned_classes": ["软件1班"]
    })
    assert create_user_response.status_code == 200, "创建教师失败"
    assert create_user_response.json()["success"] is True
    print(f"  ✓ 创建教师成功: {teacher_username}")
    
    # ==========================================
    # Step 6: 切换用户登录（验证新用户可用）
    # ==========================================
    logout_response = await client.post("/api/logout")
    assert logout_response.status_code == 200, "登出失败"
    
    teacher_login = await client.post("/api/login", json={
        "username": teacher_username,
        "password": "teacher123"
    })
    assert teacher_login.status_code == 200, "教师登录失败"
    assert teacher_login.json()["success"] is True
    print(f"  ✓ 教师登录成功")
    
    # ==========================================
    # Step 7: 验证教师权限（不能创建用户）
    # ==========================================
    forbidden_response = await client.post("/api/admin/users", json={
        "username": "test_user",
        "password": "password123",
        "name": "测试用户",
        "role": "teacher"
    })
    assert forbidden_response.status_code == 403, "教师应无权限创建用户"
    print(f"  ✓ 权限控制正常: 教师无法创建用户")
    
    # ==========================================
    # Step 8: 最终登出
    # ==========================================
    final_logout = await client.post("/api/logout")
    assert final_logout.status_code == 200
    print(f"  ✓ 最终登出成功")
    
    print("\n🎉 冒烟测试通过！核心业务流程正常。")


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_student_crud_workflow(client, test_app):
    """
    学生 CRUD 冒烟测试
    
    快速验证学生的增删改查功能
    """
    from domain.entities.user import User, UserRole
    from domain.value_objects.password import Password
    
    db = test_app.state.test_db
    
    # 创建教师
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
    
    # 登录
    login = await client.post("/api/login", json={
        "username": teacher.username,
        "password": "teacher123"
    })
    assert login.status_code == 200
    
    # 创建
    student_id = f"2024{uuid.uuid4().hex[:6]}"
    create = await client.post("/api/students", json={
        "student_id": student_id,
        "name": "测试学生",
        "class_name": "测试班级"
    })
    assert create.status_code == 200
    
    # 查询
    get = await client.get(f"/api/students/{student_id}")
    assert get.status_code == 200
    assert get.json()["data"]["name"] == "测试学生"
    
    # 更新分数
    update = await client.post(f"/api/students/{student_id}/score", json={
        "score_change": 5.0,
        "reason": "测试加分"
    })
    assert update.status_code == 200
    
    # 删除
    delete = await client.delete(f"/api/students/{student_id}")
    assert delete.status_code == 200
    
    # 验证删除
    get_after = await client.get(f"/api/students/{student_id}")
    assert get_after.status_code == 404
    
    print("✓ 学生 CRUD 流程正常")


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_auth_security(client, test_app):
    """
    认证安全冒烟测试
    
    验证认证和权限控制
    """
    from domain.entities.user import User, UserRole, UserStatus
    from domain.value_objects.password import Password
    
    db = test_app.state.test_db
    
    # 创建禁用用户
    disabled_user = User(
        username=f"disabled_{uuid.uuid4().hex[:8]}",
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
        ''', (disabled_user.username, disabled_user.password.hash_value, 
              disabled_user.password.salt, disabled_user.name, 
              disabled_user.role.value, 0))
    
    # 测试禁用用户登录
    login = await client.post("/api/login", json={
        "username": disabled_user.username,
        "password": "password123"
    })
    assert login.status_code == 403, "禁用用户应无法登录"
    
    # 测试错误密码
    wrong_pass = await client.post("/api/login", json={
        "username": disabled_user.username,
        "password": "wrongpassword"
    })
    assert wrong_pass.status_code in [401, 403], "错误密码应拒绝"
    
    # 测试未认证访问
    no_auth = await client.get("/api/students")
    assert no_auth.status_code in [302, 401, 403], "未认证应被拒绝"
    
    print("✓ 认证安全流程正常")
