from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_roles
from app.db.session import get_db
from app.services.certificate_service import CertificateService

router = APIRouter(prefix="/certificates", tags=["Certificates"])
cert_service = CertificateService()


@router.get("/my")
async def my_certificates(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Employee: list all my certificates."""
    return await cert_service.list_user_certificates(db, current_user.user_id)


@router.get("/{certificate_id}/download")
async def download_certificate(
    certificate_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Employee: get a signed URL to download a certificate PDF."""
    return await cert_service.get_download_url(db, certificate_id, current_user.user_id)


@router.get("/verify/{certificate_number}")
async def verify_certificate(
    certificate_number: str,
    db: AsyncSession = Depends(get_db),
):
    """
    PUBLIC endpoint — no authentication required.
    Called when someone scans a QR code.
    Rate-limited at Nginx level.
    """
    return await cert_service.verify_certificate(db, certificate_number)


@router.post("/{certificate_id}/revoke")
async def revoke_certificate(
    certificate_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([1])),  # Super Admin only
):
    """Super Admin: revoke a certificate."""
    return await cert_service.revoke_certificate(db, certificate_id)


@router.post("/generate")
async def generate_certificate_manual(
    user_id: int,
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([1, 2])),  # Admin only — for testing
):
    """
    Manually trigger certificate generation.
    In production this is called automatically after assessment pass.
    """
    cert = await cert_service.generate_certificate(db, user_id, video_id, current_user.company_id)
    return {
        "message": "Certificate generated successfully.",
        "certificate_number": cert.certificate_number,
        "certificate_id": cert.certificate_id,
    }
