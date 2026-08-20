from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_permission, require_roles
from app.db.session import get_db
from app.models.certificate import Certificate, CertificateTemplate
from app.models.company import CompanyMaster
from app.models.concern import Concern
from app.models.training import AssessmentResult, CourseAssignment, TrainingHistory
from app.models.user import UserMaster
from app.models.video import VideoMaster

router = APIRouter(prefix="/analytics", tags=["Analytics"])


async def _platform_overview(db: AsyncSession) -> dict:
    async def scalar_count(*conditions) -> int:
        result = await db.execute(select(func.count()).where(*conditions))
        return result.scalar() or 0

    async def grouped_counts(column, *conditions) -> dict:
        result = await db.execute(select(column, func.count()).where(*conditions).group_by(column))
        return {str(key or "Unassigned"): value for key, value in result.all()}

    companies_result = await db.execute(
        select(func.count()).where(
            CompanyMaster.is_deleted == "N", CompanyMaster.status == "Active"
        )
    )
    total_companies = companies_result.scalar() or 0

    users_result = await db.execute(
        select(func.count()).where(UserMaster.is_deleted == "N", UserMaster.status == "Active")
    )
    total_users = users_result.scalar() or 0

    certs_result = await db.execute(select(func.count()).where(Certificate.status == "Valid"))
    total_certificates = certs_result.scalar() or 0

    completions_result = await db.execute(
        select(func.count()).where(TrainingHistory.status == "Completed")
    )
    total_completions = completions_result.scalar() or 0

    avg_score_result = await db.execute(
        select(func.avg(AssessmentResult.score)).where(AssessmentResult.result == "Pass")
    )
    avg_score = round(float(avg_score_result.scalar() or 0), 2)
    role_counts = await grouped_counts(
        UserMaster.role_id,
        UserMaster.is_deleted == "N",
        UserMaster.status == "Active",
    )
    company_approval = await grouped_counts(
        CompanyMaster.approval_status,
        CompanyMaster.is_deleted == "N",
    )
    company_status = await grouped_counts(
        CompanyMaster.status,
        CompanyMaster.is_deleted == "N",
    )
    video_status = await grouped_counts(VideoMaster.status)
    template_status = await grouped_counts(CertificateTemplate.status)
    concern_status = await grouped_counts(Concern.status)
    assessment_results = await grouped_counts(AssessmentResult.result)
    total_employees = role_counts.get("4", 0)
    completed_users_result = await db.execute(
        select(func.count(TrainingHistory.user_id.distinct())).where(
            TrainingHistory.status == "Completed"
        )
    )
    completed_users = completed_users_result.scalar() or 0
    assignments_result = await db.execute(select(func.count()).select_from(CourseAssignment))
    total_assignments = assignments_result.scalar() or 0
    compliance_rate = round((completed_users / total_employees * 100), 2) if total_employees else 0

    return {
        "scope": "platform",
        "total_companies": total_companies,
        "total_users": total_users,
        "total_certificates_issued": total_certificates,
        "total_course_completions": total_completions,
        "average_pass_score": avg_score,
        "compliance_rate": compliance_rate,
        "hierarchy": {
            "super_admins": role_counts.get("1", 0),
            "company_admins": role_counts.get("2", 0),
            "client_management": role_counts.get("5", 0),
            "hr_users": role_counts.get("3", 0),
            "employees": total_employees,
        },
        "companies": {
            "active": company_status.get("Active", 0),
            "inactive": company_status.get("Inactive", 0),
            "approved": company_approval.get("Approved", 0),
            "pending": company_approval.get("Pending", 0),
            "rejected": company_approval.get("Rejected", 0),
        },
        "videos": {
            "total": sum(video_status.values()),
            "draft": video_status.get("Draft", 0),
            "published": video_status.get("Published", 0),
            "archived": video_status.get("Archived", 0),
        },
        "training": {
            "assignments": total_assignments,
            "completed_users": completed_users,
            "completed_history": total_completions,
            "in_progress": await scalar_count(TrainingHistory.status == "In Progress"),
            "compliance_rate": compliance_rate,
        },
        "assessments": {
            "passed": assessment_results.get("Pass", 0),
            "failed": assessment_results.get("Fail", 0),
            "average_pass_score": avg_score,
        },
        "certificates": {
            "issued": total_certificates,
            "revoked": await scalar_count(Certificate.status == "Revoked"),
            "templates_pending": template_status.get("Pending", 0),
            "templates_active": template_status.get("Active", 0),
            "templates_rejected": template_status.get("Rejected", 0),
        },
        "concerns": {
            "open": concern_status.get("Open", 0),
            "reviewed": concern_status.get("Reviewed", 0),
            "closed": concern_status.get("Closed", 0),
            "total": sum(concern_status.values()),
        },
        "approvals": {
            "companies_pending": company_approval.get("Pending", 0),
            "videos_pending": video_status.get("Draft", 0),
            "certificate_templates_pending": template_status.get("Pending", 0),
            "open_concerns": concern_status.get("Open", 0),
        },
    }


async def _company_overview(db: AsyncSession, company_id: int) -> dict:
    total_result = await db.execute(
        select(func.count()).where(
            UserMaster.company_id == company_id,
            UserMaster.is_deleted == "N",
            UserMaster.role_id == 4,
        )
    )
    total = total_result.scalar() or 0

    completed_result = await db.execute(
        select(func.count(TrainingHistory.user_id.distinct())).where(
            TrainingHistory.company_id == company_id,
            TrainingHistory.status == "Completed",
        )
    )
    completed = completed_result.scalar() or 0

    in_progress_result = await db.execute(
        select(func.count(TrainingHistory.user_id.distinct())).where(
            TrainingHistory.company_id == company_id,
            TrainingHistory.status == "In Progress",
        )
    )
    in_progress = in_progress_result.scalar() or 0

    cert_result = await db.execute(select(func.count()).where(Certificate.company_id == company_id))
    total_certs = cert_result.scalar() or 0

    avg_score_result = await db.execute(
        select(func.avg(AssessmentResult.score)).where(
            AssessmentResult.video_id.in_(
                select(TrainingHistory.video_id).where(TrainingHistory.company_id == company_id)
            ),
            AssessmentResult.result == "Pass",
        )
    )
    avg_score = round(float(avg_score_result.scalar() or 0), 2)
    compliance_rate = round((completed / total * 100), 2) if total > 0 else 0.0

    return {
        "scope": "company",
        "company_id": company_id,
        "total_employees": total,
        "completed_training": completed,
        "in_progress_training": in_progress,
        "not_started_training": max(total - completed - in_progress, 0),
        "compliance_rate": compliance_rate,
        "certificates_issued": total_certs,
        "average_pass_score": avg_score,
    }


@router.get("/current")
async def current_analytics(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("reports.view")),
):
    """Analytics for the current admin scope."""
    if current_user.role_id == 1:
        return await _platform_overview(db)
    return await _company_overview(db, current_user.company_id)


@router.get("/overview")
async def analytics_overview(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([1])),  # Super Admin only
):
    """Platform-wide analytics for Super Admin."""
    return await _platform_overview(db)


@router.get("/company/{company_id}")
async def company_analytics(
    company_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("reports.view")),
):
    """Analytics for a specific company."""
    if current_user.role_id != 1 and current_user.company_id != company_id:
        raise HTTPException(403, "You do not have permission to access this company.")

    return await _company_overview(db, company_id)
