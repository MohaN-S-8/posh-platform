from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_roles
from app.db.session import get_db
from app.schemas.hr import TrainingAssignRequest
from app.services.hr_service import HRService

router = APIRouter(prefix="/hr", tags=["HR Portal"])
hr_service = HRService()

HR_ROLES = [1, 2, 3]  # Super Admin, Company Admin, HR


@router.get("/employees")
async def list_assignable_employees(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(HR_ROLES)),
):
    """List active employees and departments available for training assignment."""
    return await hr_service.list_assignable_employees(db, current_user.company_id)


@router.post("/employees/bulk-upload")
async def bulk_upload_employees(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(HR_ROLES)),
):
    """
    Upload Excel or CSV file to create employees in bulk.
    Returns success count and per-row error details.
    Supported formats: .xlsx, .xls, .csv
    Required columns: employee_id, first_name, email, mobile, role_id
    """
    return await hr_service.bulk_upload_employees(
        db, file, current_user.company_id, current_user.user_id
    )


@router.post("/training/assign")
async def assign_training(
    data: TrainingAssignRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(HR_ROLES)),
):
    """
    Assign a training video to:
    - Individual employee (assign_type: Individual, assigned_to_user_id required)
    - Department (assign_type: Department, assigned_to_department required)
    - Entire company (assign_type: Company-Wide)
    """
    return await hr_service.assign_training(db, data, current_user.company_id, current_user.user_id)


@router.get("/compliance/dashboard")
async def compliance_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(HR_ROLES)),
):
    """
    Compliance overview for the company:
    total employees, completed, in-progress, not-started, compliance rate,
    department breakdown, and overdue employees list.
    """
    return await hr_service.get_compliance_dashboard(db, current_user.company_id)


@router.get("/reports/employees")
async def download_employee_report(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(HR_ROLES)),
):
    """
    Download employee training report as Excel file.
    Contains all employees with their training status and completion %.
    """
    excel_bytes = await hr_service.generate_employee_report(db, current_user.company_id)
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=employee_training_report.xlsx"},
    )


@router.get("/reports/departments")
async def download_department_report(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(HR_ROLES)),
):
    """Download department compliance report as Excel file."""
    excel_bytes = await hr_service.generate_department_report(db, current_user.company_id)
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=department_compliance_report.xlsx"},
    )


@router.get("/reports/certificates")
async def download_certificate_report(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(HR_ROLES)),
):
    """Download issued certificate report as Excel file."""
    excel_bytes = await hr_service.generate_certificate_report(db, current_user.company_id)
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=certificate_report.xlsx"},
    )
