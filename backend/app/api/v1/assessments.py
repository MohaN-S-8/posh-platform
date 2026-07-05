from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.schemas.assessment import AssessmentQuestionResponse, AssessmentSubmit
from app.services.assessment_service import AssessmentService

router = APIRouter(prefix="/assessments", tags=["Assessments"])
assessment_service = AssessmentService()


@router.get("/{video_id}/questions", response_model=list[AssessmentQuestionResponse])
async def get_questions(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return assessment questions/options for a published company video."""
    return await assessment_service.questions(db, video_id, current_user.company_id)


@router.post("/submit")
async def submit_assessment(
    data: AssessmentSubmit,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Submit assessment answers.
    Assessment is locked until video is 95%+ complete.
    Returns score, pass/fail, and triggers certificate on Pass.
    """

    return await assessment_service.submit(db, current_user.user_id, data, current_user.company_id)
