import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from models.audit import AuditLog


def get_client_ip(request) -> Optional[str]:
    """Trích xuất địa chỉ IP client từ Request (hỗ trợ proxy qua X-Forwarded-For)."""
    if request is None:
        return None
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


async def write_audit_log(
    db: AsyncSession,
    *,
    user_id: Optional[uuid.UUID],
    action: str,
    target_type: Optional[str] = None,
    target_id: Optional[uuid.UUID] = None,
    detail: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    """Ghi một bản ghi vết thao tác. Chỉ flush để caller commit cùng transaction."""
    log = AuditLog(
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=detail,
        ip_address=ip_address,
    )
    db.add(log)
    await db.flush()
    return log