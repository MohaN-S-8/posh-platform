from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.training import (
    AssessmentOption,
    AssessmentQuestion,
    AssessmentResult,
    TrainingHistory,
)
from app.schemas.assessment import AssessmentSubmit
from app.services.certificate_service import CertificateService


class AssessmentService:
    async def submit(
        self, db: AsyncSession, user_id: int, data: AssessmentSubmit, company_id: int
    ) -> dict:
        """Submit assessment answers. Video must be completed first."""

        # 1. Verify video is completed
        history_result = await db.execute(
            select(TrainingHistory).where(
                TrainingHistory.user_id == user_id,
                TrainingHistory.video_id == data.video_id,
                TrainingHistory.status == "Completed",
            )
        )
        if not history_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please complete the training video before taking the assessment.",
            )

        # 2. Count attempt number
        attempt_result = await db.execute(
            select(func.count()).where(
                AssessmentResult.user_id == user_id,
                AssessmentResult.video_id == data.video_id,
            )
        )
        attempt_number = (attempt_result.scalar() or 0) + 1

        # 3. Score the answers
        correct = 0
        total = len(data.answers)

        for answer in data.answers:
            q_result = await db.execute(
                select(AssessmentQuestion).where(
                    AssessmentQuestion.question_id == answer.question_id
                )
            )
            question = q_result.scalar_one_or_none()
            if question and question.correct_option == answer.selected_option.upper():
                correct += 1

        score = (correct / total * 100) if total > 0 else 0
        passing_score = 70.0  # default; can be from course_assignment
        result = "Pass" if score >= passing_score else "Fail"

        # 4. Save result
        assessment_result = AssessmentResult(
            user_id=user_id,
            video_id=data.video_id,
            total_questions=total,
            correct_answers=correct,
            score=score,
            passing_score=passing_score,
            result=result,
            attempt_number=attempt_number,
        )
        db.add(assessment_result)
        await db.commit()

        response = {
            "score": round(score, 2),
            "correct": correct,
            "total": total,
            "result": result,
            "attempt_number": attempt_number,
            "certificate_triggered": result == "Pass",
        }

        # 5. Trigger certificate generation on Pass
        if result == "Pass":
            cert_service = CertificateService()
            try:
                cert = await cert_service.generate_certificate(
                    db, user_id, data.video_id, company_id
                )
                response["certificate_number"] = cert.certificate_number
                response["message"] = (
                    f"Congratulations! Certificate {cert.certificate_number} generated."
                )
            except Exception:
                # Don't fail the assessment if certificate generation fails
                response["message"] = "Assessment passed. Certificate generation in progress."
        else:
            response["message"] = (
                f"Score: {score:.1f}%. You need {passing_score}% to pass. Please retry."
            )

        return response
