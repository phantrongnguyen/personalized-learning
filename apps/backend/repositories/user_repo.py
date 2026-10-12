import uuid
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.user import User, Role


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
    """Tìm user theo ID kèm nạp sẵn danh sách roles và profiles"""
    query = (
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.roles),
            selectinload(User.student_profile),
            selectinload(User.advisor_profile),
        )
    )
    result = await db.execute(query)
    return result.scalars().first()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Tìm user theo Email kèm roles và profiles"""
    query = (
        select(User)
        .where(User.email == email)
        .options(
            selectinload(User.roles),
            selectinload(User.student_profile),
            selectinload(User.advisor_profile),
        )
    )
    result = await db.execute(query)
    return result.scalars().first()


async def get_users(
    db: AsyncSession, skip: int = 0, limit: int = 50, role_code: Optional[str] = None
) -> List[User]:
    """Lấy danh sách người dùng có phân trang và lọc role"""
    query = (
        select(User)
        .options(selectinload(User.roles))
        .offset(skip)
        .limit(limit)
        .order_by(User.created_at.desc())
    )
    if role_code:
        query = query.join(User.roles).where(Role.code == role_code)

    result = await db.execute(query)
    return list(result.scalars().all())


async def create_user(
    db: AsyncSession,
    email: str,
    hashed_password: str,
    full_name: str,
    phone_number: Optional[str] = None,
    avatar_url: Optional[str] = None,
    role_codes: Optional[List[str]] = None,
) -> User:
    """Tạo người dùng mới và gán vai trò"""
    user = User(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        phone_number=phone_number,
        avatar_url=avatar_url,
        is_active=True,
    )
    if role_codes:
        role_query = select(Role).where(Role.code.in_(role_codes))
        roles_result = await db.execute(role_query)
        user.roles = list(roles_result.scalars().all())

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
