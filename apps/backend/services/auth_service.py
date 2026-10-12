import uuid
from typing import Dict, Any, Tuple
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.security import verify_password, create_access_token, create_refresh_token, decode_token
from models.user import User
from repositories.user_repo import get_user_by_email, get_user_by_id, get_user_by_student_code


async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> Tuple[User, Dict[str, Any]]:
    """Xác thực thông tin tài khoản và sinh cặp access/refresh token"""
    username = username.strip()
    user = await get_user_by_email(db, username) if "@" in username else await get_user_by_student_code(db, username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không chính xác",
        )

    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không chính xác",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản này đã bị vô hiệu hóa",
        )

    role_codes = [role.code for role in user.roles]
    token_payload = {
        "sub": str(user.id),
        "email": user.email,
        "roles": role_codes,
    }

    access_token = create_access_token(token_payload)
    refresh_token = create_refresh_token(token_payload)

    tokens = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }
    return user, tokens


async def refresh_access_token(db: AsyncSession, refresh_token: str) -> Dict[str, Any]:
    """Cấp access token mới từ refresh token hợp lệ"""
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token không hợp lệ hoặc đã hết hạn",
        )

    user_id_str = payload.get("sub")
    try:
        user_id = uuid.UUID(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Payload định danh token không hợp lệ",
        )

    user = await get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản không tồn tại hoặc đã bị khóa",
        )

    token_payload = {
        "sub": str(user.id),
        "email": user.email,
        "roles": [role.code for role in user.roles],
    }

    new_access_token = create_access_token(token_payload)
    new_refresh_token = create_refresh_token(token_payload)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }
