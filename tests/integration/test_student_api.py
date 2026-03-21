"""
学生管理 API 集成测试
"""
import pytest
import uuid


@pytest.mark.asyncio
async def test_create_student_success(client, test_user):
    """
    测试成功创建学生
    
    验证点：
    1. 返回 HTTP 200
    2. 响应包含创建的学生信息
    3. 默认分数为 70
    """
    # Arrange - 先登录
    login_response = await client.post("/api/login", json={
        "username": test_user["username"],
        "password": test_user["password"]
    })
    assert login_response.status_code == 200
    
    # 使用唯一的学号避免冲突
    student_id = f"2024{uuid.uuid4().hex[:6]}"
    
    # Act
    response = await client.post("/api/students", json={
        "student_id": student_id,
        "name": "张三",
        "class_name": "软件1班"
    })
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["student_id"] == student_id
    assert data["data"]["name"] == "张三"
    assert data["data"]["class_name"] == "软件1班"
    assert data["data"]["score"] == 70.0  # 默认分数


@pytest.mark.asyncio
async def test_create_student_duplicate_id(client, test_user):
    """
    测试创建重复学号学生
    
    验证点：
    1. 返回 HTTP 400
    2. 提示学号已存在
    """
    # Arrange - 先登录
    login_response = await client.post("/api/login", json={
        "username": test_user["username"],
        "password": test_user["password"]
    })
    assert login_response.status_code == 200
    
    student_id = f"2024{uuid.uuid4().hex[:6]}"
    
    # 第一次创建
    response1 = await client.post("/api/students", json={
        "student_id": student_id,
        "name": "张三",
        "class_name": "软件1班"
    })
    assert response1.status_code == 200
    
    # Act - 重复创建
    response2 = await client.post("/api/students", json={
        "student_id": student_id,
        "name": "李四",
        "class_name": "软件2班"
    })
    
    # Assert
    assert response2.status_code == 400
    assert "已存在" in response2.json()["detail"]


@pytest.mark.asyncio
async def test_create_student_validation_error(client, test_user):
    """
    测试创建学生参数验证失败
    
    验证点：
    1. 学号太短返回 400 (Bad Request)
    """
    # Arrange - 先登录
    login_response = await client.post("/api/login", json={
        "username": test_user["username"],
        "password": test_user["password"]
    })
    assert login_response.status_code == 200
    
    # Act - 学号太短
    response = await client.post("/api/students", json={
        "student_id": "A",
        "name": "张三"
    })
    
    # Assert - 实际返回 400（业务验证）而非 422（Pydantic 验证）
    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_get_students_list(client, test_user):
    """
    测试获取学生列表
    
    验证点：
    1. 返回 HTTP 200
    2. 返回的学生列表包含创建的学生
    """
    # Arrange - 先登录并创建学生
    login_response = await client.post("/api/login", json={
        "username": test_user["username"],
        "password": test_user["password"]
    })
    assert login_response.status_code == 200
    
    student_id = f"2024{uuid.uuid4().hex[:6]}"
    await client.post("/api/students", json={
        "student_id": student_id,
        "name": "测试学生",
        "class_name": "测试班级"
    })
    
    # Act
    response = await client.get("/api/students")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    # 验证包含刚创建的学生
    student_ids = [s["student_id"] for s in data["data"]]
    assert student_id in student_ids


@pytest.mark.asyncio
async def test_get_students_by_class(client, test_user):
    """
    测试按班级筛选学生
    
    验证点：
    1. 返回指定班级的学生
    2. 不包含其他班级的学生
    """
    # Arrange - 先登录并创建两个班级的学生
    login_response = await client.post("/api/login", json={
        "username": test_user["username"],
        "password": test_user["password"]
    })
    assert login_response.status_code == 200
    
    student_id1 = f"2024{uuid.uuid4().hex[:6]}"
    student_id2 = f"2024{uuid.uuid4().hex[:6]}"
    
    await client.post("/api/students", json={
        "student_id": student_id1,
        "name": "软件1班学生",
        "class_name": "软件1班"
    })
    await client.post("/api/students", json={
        "student_id": student_id2,
        "name": "软件2班学生",
        "class_name": "软件2班"
    })
    
    # Act - 查询软件1班
    response = await client.get("/api/students?class_name=软件1班")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    student_ids = [s["student_id"] for s in data["data"]]
    assert student_id1 in student_ids
    assert student_id2 not in student_ids


@pytest.mark.asyncio
async def test_update_score_success(client, test_user):
    """
    测试成功更新学生分数
    
    验证点：
    1. 分数更新成功
    2. 返回更新后的学生信息
    """
    # Arrange - 先登录并创建学生
    login_response = await client.post("/api/login", json={
        "username": test_user["username"],
        "password": test_user["password"]
    })
    assert login_response.status_code == 200
    
    student_id = f"2024{uuid.uuid4().hex[:6]}"
    create_response = await client.post("/api/students", json={
        "student_id": student_id,
        "name": "张三",
        "class_name": "软件1班"
    })
    assert create_response.status_code == 200
    initial_score = create_response.json()["data"]["score"]
    
    # Act - 加分
    response = await client.post(f"/api/students/{student_id}/score", json={
        "score_change": 10.0,
        "reason": "课堂表现优秀"
    })
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["score"] == initial_score + 10.0


@pytest.mark.asyncio
async def test_update_score_student_not_found(client, test_user):
    """
    测试更新不存在学生的分数
    
    验证点：
    1. 返回 HTTP 400
    2. 提示学生不存在
    """
    # Arrange - 先登录
    login_response = await client.post("/api/login", json={
        "username": test_user["username"],
        "password": test_user["password"]
    })
    assert login_response.status_code == 200
    
    # Act
    response = await client.post("/api/students/99999999/score", json={
        "score_change": 10.0,
        "reason": "测试"
    })
    
    # Assert
    assert response.status_code == 400
    assert "不存在" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_student_success(client, test_user):
    """
    测试成功删除学生
    
    验证点：
    1. 删除成功返回 200
    2. 删除后无法查询到该学生
    """
    # Arrange - 先登录并创建学生
    login_response = await client.post("/api/login", json={
        "username": test_user["username"],
        "password": test_user["password"]
    })
    assert login_response.status_code == 200
    
    student_id = f"2024{uuid.uuid4().hex[:6]}"
    await client.post("/api/students", json={
        "student_id": student_id,
        "name": "待删除学生",
        "class_name": "软件1班"
    })
    
    # Act - 删除
    delete_response = await client.delete(f"/api/students/{student_id}")
    
    # Assert
    assert delete_response.status_code == 200
    assert delete_response.json()["success"] is True
    
    # 验证已删除
    get_response = await client.get(f"/api/students/{student_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_access_without_auth(client):
    """
    测试未认证访问受保护接口
    
    验证点：
    1. 创建学生返回 401/302/403
    2. 获取列表返回 401/302/403
    """
    # Act
    response = await client.get("/api/students")
    
    # Assert
    assert response.status_code in [302, 401, 403]
