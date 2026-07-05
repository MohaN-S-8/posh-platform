from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_roles
from app.db.session import get_db
from app.models.auth import LoginAttempts
from app.models.language import LanguageMaster

router = APIRouter(prefix="/admin", tags=["Admin Portal"])


@router.get("/audit-logins")
async def list_login_audit_logs(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([1, 2])),
):
    """List recent login audit events."""
    result = await db.execute(
        select(LoginAttempts).order_by(LoginAttempts.attempted_at.desc()).limit(100)
    )
    rows = result.scalars().all()
    return [
        {
            "id": row.id,
            "user_id": row.user_id,
            "email_attempted": row.email_attempted,
            "ip_address": row.ip_address,
            "success": row.success,
            "attempted_at": row.attempted_at,
        }
        for row in rows
    ]


@router.get("/languages")
async def list_languages(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([1, 2])),
):
    """List platform languages configured in language_master."""
    result = await db.execute(select(LanguageMaster).order_by(LanguageMaster.language_name))
    return [
        {"language_id": row.language_id, "language_name": row.language_name}
        for row in result.scalars().all()
    ]
