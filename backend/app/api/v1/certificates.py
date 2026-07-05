from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_roles
from app.db.session import get_db
from app.schemas.certificate import (
    CertificateTemplateCreate,
    CertificateTemplateResponse,
    CertificateTemplateUpdate,
)
from app.services.certificate_service import CertificateService

router = APIRouter(prefix="/certificates", tags=["Certificates"])
cert_service = CertificateService()


@router.get("/templates", response_model=list[CertificateTemplateResponse])
async def list_certificate_templates(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([1, 2])),
):
    """Admin: list certificate templates for the current company."""
    return await cert_service.list_templates(db, current_user.company_id)


@router.post("/templates", response_model=CertificateTemplateResponse, status_code=201)
async def create_certificate_template(
    data: CertificateTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([1, 2])),
):
    """Admin: create a certificate template for the current company."""
    return await cert_service.create_template(db, data, current_user.company_id)


@router.put("/templates/{template_id}", response_model=CertificateTemplateResponse)
async def update_certificate_template(
    template_id: int,
    data: CertificateTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([1, 2])),
):
    """Admin: update a certificate template."""
    return await cert_service.update_template(db, template_id, data, current_user.company_id)


@router.patch("/templates/{template_id}/status")
async def update_certificate_template_status(
    template_id: int,
    status: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([1, 2])),
):
    """Admin: activate or deactivate a certificate template."""
    if status not in ["Active", "Inactive"]:
        from fastapi import HTTPException

        raise HTTPException(400, "Status must be 'Active' or 'Inactive'")
    return await cert_service.set_template_status(db, template_id, status, current_user.company_id)


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
