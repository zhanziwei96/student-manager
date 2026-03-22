"""
JWT 认证工具
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import HTTPException, Request, Response
from app.core.config import get_settings

settings = get_settings()

# JWT 配置
SECRET_KEY = settings.security.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24小时
COOKIE_NAME = "access_token"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建 JWT Token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """解码 JWT Token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def set_token_cookie(response: Response, token: str):
    """设置 HttpOnly Cookie"""
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,  # JS 无法访问
        secure=False,   # 生产环境应设为 True (HTTPS)
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


def clear_token_cookie(response: Response):
    """清除 Cookie"""
    response.delete_cookie(key=COOKIE_NAME)


def get_token_from_cookie(request: Request) -> Optional[str]:
    """从 Cookie 获取 Token"""
    return request.cookies.get(COOKIE_NAME)


# 依赖注入函数
async def get_current_user(request: Request) -> Dict[str, Any]:
    """获取当前用户（FastAPI 依赖）"""
    token = get_token_from_cookie(request)
    if not token:
        raise HTTPException(status_code=401, detail="未登录")
    
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="登录已过期")
    
    # 检查过期时间
    exp = payload.get("exp")
    if exp and datetime.utcnow().timestamp() > exp:
        raise HTTPException(status_code=401, detail="登录已过期")
    
    return payload


async def require_login(request: Request) -> str:
    """要求登录，返回用户ID"""
    user = await get_current_user(request)
    user_id = user.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的用户信息")
    return user_id


async def require_admin(request: Request) -> str:
    """要求管理员权限"""
    user = await get_current_user(request)
    user_id = user.get("sub")
    is_admin = user.get("is_admin", False)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="未登录")
    if not is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    return user_id
