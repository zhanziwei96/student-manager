"""
JWT 认证集成测试
"""
import pytest


class TestJWTLogin:
    """JWT 登录相关测试"""
    
    def test_login_sets_http_only_cookie(self, jwt_client, jwt_admin_user):
        """测试登录设置 HttpOnly Cookie"""
        response = jwt_client.post("/api/v1/login", json={
            "username": "admin",
            "password": "admin123",
            "role": "admin"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # 检查是否设置了 Cookie
        set_cookie = response.headers.get("set-cookie")
        assert set_cookie is not None
        assert "access_token=" in set_cookie
        assert "HttpOnly" in set_cookie  # 必须是 HttpOnly
        assert "SameSite=lax" in set_cookie
    
    def test_login_success_response(self, jwt_client, jwt_admin_user):
        """测试登录成功返回用户信息"""
        response = jwt_client.post("/api/v1/login", json={
            "username": "admin",
            "password": "admin123",
            "role": "admin"
        })
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["username"] == "admin"
        assert data["data"]["role"] == "admin"
        assert data["data"]["is_admin"] is True
    
    def test_login_teacher(self, jwt_client, jwt_teacher_user):
        """测试教师登录"""
        response = jwt_client.post("/api/v1/login", json={
            "username": "zhanziwei",
            "password": "zha123",
            "role": "teacher"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["role"] == "teacher"
        assert data["data"]["is_admin"] is False
    
    def test_login_wrong_password(self, jwt_client, jwt_admin_user):
        """测试密码错误"""
        response = jwt_client.post("/api/v1/login", json={
            "username": "admin",
            "password": "wrongpassword",
            "role": "admin"
        })
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False


class TestJWTProtectedRoutes:
    """JWT 受保护路由测试"""
    
    def test_access_without_cookie(self, jwt_client):
        """测试无 Cookie 访问受保护接口"""
        response = jwt_client.get("/api/v1/students")
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert "未登录" in data["message"]
    
    def test_access_with_valid_cookie(self, jwt_client, jwt_admin_user):
        """测试使用有效 Cookie 访问受保护接口"""
        # 先登录
        login_res = jwt_client.post("/api/v1/login", json={
            "username": "admin",
            "password": "admin123",
            "role": "admin"
        })
        
        # 提取 Cookie
        cookie = login_res.headers.get("set-cookie")
        
        # 访问受保护接口
        response = jwt_client.get("/api/v1/students", headers={"Cookie": cookie})
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_access_with_invalid_cookie(self, jwt_client):
        """测试使用无效 Cookie 访问受保护接口"""
        response = jwt_client.get(
            "/api/v1/students",
            headers={"Cookie": "access_token=invalid.token.value"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False


class TestJWTMeEndpoint:
    """JWT /me 接口测试"""
    
    def test_me_with_valid_token(self, jwt_client, jwt_admin_user):
        """测试使用有效 Token 获取用户信息"""
        # 登录
        login_res = jwt_client.post("/api/v1/login", json={
            "username": "admin",
            "password": "admin123",
            "role": "admin"
        })
        
        cookie = login_res.headers.get("set-cookie")
        
        # 获取用户信息
        response = jwt_client.get("/api/v1/me", headers={"Cookie": cookie})
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["username"] == "admin"
        assert data["data"]["role"] == "admin"
        assert data["data"]["is_admin"] is True
        assert "exp" in data["data"]  # 包含过期时间
    
    def test_me_without_token(self, jwt_client):
        """测试无 Token 访问 /me"""
        response = jwt_client.get("/api/v1/me")
        
        assert response.status_code == 401


class TestJWTLogout:
    """JWT 登出测试"""
    
    def test_logout_clears_cookie(self, jwt_client, jwt_admin_user):
        """测试登出清除 Cookie"""
        # 先登录
        login_res = jwt_client.post("/api/v1/login", json={
            "username": "admin",
            "password": "admin123",
            "role": "admin"
        })
        
        cookie = login_res.headers.get("set-cookie")
        
        # 登出
        logout_res = jwt_client.post("/api/v1/logout", headers={"Cookie": cookie})
        
        assert logout_res.status_code == 200
        
        # 检查 Cookie 是否被清除
        set_cookie = logout_res.headers.get("set-cookie")
        assert set_cookie is not None
        assert 'access_token=""' in set_cookie or "Max-Age=0" in set_cookie
    
    def test_access_after_logout(self, jwt_client, jwt_admin_user):
        """测试登出后 Cookie 被清除"""
        # 登录
        login_res = jwt_client.post("/api/v1/login", json={
            "username": "admin",
            "password": "admin123",
            "role": "admin"
        })
        
        cookie = login_res.headers.get("set-cookie")
        
        # 登出
        logout_res = jwt_client.post("/api/v1/logout", headers={"Cookie": cookie})
        
        # 检查登出响应是否清除 Cookie
        set_cookie = logout_res.headers.get("set-cookie")
        assert set_cookie is not None
        assert 'access_token=""' in set_cookie or "Max-Age=0" in set_cookie
        
        # 注意：JWT 是无状态的，服务端无法使 token 失效
        # 使用旧 Cookie 仍然可以访问（这是 JWT 的特性）
        # 如果需要服务端控制，需要使用 token 黑名单或 Redis


class TestJWTAdminOnlyRoutes:
    """JWT 管理员专属路由测试"""
    
    def test_admin_route_with_admin(self, jwt_client, jwt_admin_user):
        """测试管理员访问管理员接口"""
        # 登录管理员
        login_res = jwt_client.post("/api/v1/login", json={
            "username": "admin",
            "password": "admin123",
            "role": "admin"
        })
        
        cookie = login_res.headers.get("set-cookie")
        
        # 访问管理员接口
        response = jwt_client.get("/api/v1/users", headers={"Cookie": cookie})
        
        assert response.status_code == 200
    
    def test_admin_route_with_teacher(self, jwt_client, jwt_teacher_user):
        """测试教师访问管理员接口被拒绝"""
        # 登录教师
        login_res = jwt_client.post("/api/v1/login", json={
            "username": "zhanziwei",
            "password": "zha123",
            "role": "teacher"
        })
        
        cookie = login_res.headers.get("set-cookie")
        
        # 尝试访问管理员接口
        response = jwt_client.get("/api/v1/users", headers={"Cookie": cookie})
        
        assert response.status_code == 403
