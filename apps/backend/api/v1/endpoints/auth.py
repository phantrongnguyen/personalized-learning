import uuid
from anyio import to_thread
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.config import settings
from core.permissions import get_current_user
from core.security import verify_password, get_password_hash
from models.user import User
from schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    UserOut,
    UserUpdateProfile,
    ChangePasswordRequest,
)
from services.auth_service import authenticate_user, refresh_access_token
from services.avatar_service import (
    AVATAR_CONTENT_TYPES, AVATAR_URL_PREFIX, MAX_AVATAR_BYTES,
    normalize_avatar, remove_owned_avatar,
)

router = APIRouter()


@router.post("/login", response_model=TokenResponse, summary="Đăng nhập tài khoản")
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Đăng nhập bằng mã sinh viên hoặc email và mật khẩu."""
    _, tokens = await authenticate_user(db, payload.username or str(payload.email), payload.password)
    return tokens


@router.post("/refresh", response_model=TokenResponse, summary="Cấp mới token")
async def refresh_token(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Cấp access token mới từ refresh token hợp lệ"""
    tokens = await refresh_access_token(db, payload.refresh_token)
    return tokens


@router.get("/me", response_model=UserOut, summary="Lấy thông tin tài khoản hiện tại")
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """Trả về thông tin chi tiết người dùng đang đăng nhập cùng danh sách vai trò"""
    return current_user


@router.put("/profile", response_model=UserOut, summary="Cập nhật hồ sơ cá nhân")
async def update_profile(
    payload: UserUpdateProfile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cập nhật họ tên, số điện thoại hoặc ảnh đại diện của người dùng hiện tại"""
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    if payload.phone_number is not None:
        current_user.phone_number = payload.phone_number
    if payload.avatar_url is not None:
        current_user.avatar_url = payload.avatar_url

    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.post("/profile/avatar", response_model=UserOut, summary="Tải ảnh đại diện cá nhân")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        if file.content_type not in AVATAR_CONTENT_TYPES:
            raise HTTPException(415, "Chỉ hỗ trợ ảnh JPG, PNG hoặc WebP")
        data = await file.read(MAX_AVATAR_BYTES + 1)
    finally:
        await file.close()
    normalized = await to_thread.run_sync(normalize_avatar, data)
    user_id = current_user.id
    previous_url = current_user.avatar_url
    filename = f"{user_id}-{uuid.uuid4().hex}.jpg"
    path = settings.avatar_upload_dir / filename
    try:
        await to_thread.run_sync(lambda: path.parent.mkdir(parents=True, exist_ok=True))
        await to_thread.run_sync(path.write_bytes, normalized)
        current_user.avatar_url = AVATAR_URL_PREFIX + filename
        db.add(current_user)
        await db.commit()
    except Exception as exc:
        await db.rollback()
        await to_thread.run_sync(remove_owned_avatar, path.parent, AVATAR_URL_PREFIX + filename, user_id)
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(500, "Không thể lưu ảnh đại diện, vui lòng thử lại") from exc
    await to_thread.run_sync(remove_owned_avatar, path.parent, previous_url, user_id)
    await db.refresh(current_user)
    return current_user


@router.put("/change-password", summary="Đổi mật khẩu")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Đổi mật khẩu của người dùng hiện tại"""
    if not verify_password(payload.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu hiện tại không chính xác",
        )

    current_user.hashed_password = get_password_hash(payload.new_password)
    db.add(current_user)
    await db.commit()
    return {"message": "Đổi mật khẩu thành công"}
