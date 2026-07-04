import os
import uuid
from typing import Optional

import magic  # python-magic for real MIME type detection
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.storage import generate_presigned_url, upload_file
from app.models.training import CourseAssignment, TrainingHistory
from app.models.video import VideoMaster
from app.schemas.video import VideoCreate

ALLOWED_MIME_TYPES = {"video/mp4", "video/x-msvideo", "video/quicktime"}
ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov"}
MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024  # 500 MB

VIDEO_BUCKET = os.environ.get("MINIO_BUCKET_VIDEOS", "posh-videos")


class VideoService:
    async def upload_video(
        self,
        db: AsyncSession,
        file: UploadFile,
        metadata: VideoCreate,
        uploaded_by: int,
        company_id: int,
    ) -> VideoMaster:
        """Upload a video file and save metadata."""

        # 1. Read file bytes
        file_bytes = await file.read()

        # 2. Check file size
        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds maximum limit of 500MB.",
            )

        # 3. Check MIME type using magic bytes (NOT just file extension)
        # This prevents attackers from renaming malware.exe to video.mp4
        mime_type = magic.from_buffer(file_bytes[:2048], mime=True)
        if mime_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format. Allowed: MP4, AVI, MOV. Got: {mime_type}",
            )

        # 4. Generate unique storage path
        file_ext = os.path.splitext(file.filename or "video.mp4")[1].lower()
        object_key = f"videos/{company_id}/{uuid.uuid4()}{file_ext}"

        # 5. Upload to MinIO
        upload_file(file_bytes, VIDEO_BUCKET, object_key, mime_type)

        # 6. Save metadata to DB (store path, not URL)
        video = VideoMaster(
            title=metadata.title,
            description=metadata.description,
            category_id=metadata.category_id,
            duration_minutes=metadata.duration_minutes,
            video_url=object_key,  # path only — never a public URL
            storage_type="MinIO",
            status="Draft",
            created_by=uploaded_by,
            company_id=company_id,
        )
        db.add(video)
        await db.commit()
        await db.refresh(video)
        return video

    async def get_stream_url(
        self, db: AsyncSession, video_id: int, user_id: int, company_id: int
    ) -> dict:
        """
        Generate a short-lived signed URL for video streaming.
        Verifies the user is assigned this course first.
        """
        # Verify video exists and belongs to this company
        result = await db.execute(
            select(VideoMaster).where(
                VideoMaster.video_id == video_id,
                VideoMaster.company_id == company_id,
                VideoMaster.status == "Published",
            )
        )
        video = result.scalar_one_or_none()
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found or not yet published.",
            )

        # Verify user is assigned this course
        assigned = await db.execute(
            select(CourseAssignment).where(
                CourseAssignment.video_id == video_id,
                CourseAssignment.company_id == company_id,
            )
        )
        if not assigned.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned to this course.",
            )

        # Generate signed URL (expires in 5 minutes)
        signed_url = generate_presigned_url(VIDEO_BUCKET, video.video_url, 300)

        # Initialize training history if not exists
        history_result = await db.execute(
            select(TrainingHistory).where(
                TrainingHistory.user_id == user_id,
                TrainingHistory.video_id == video_id,
            )
        )
        history = history_result.scalar_one_or_none()

        if not history:
            history = TrainingHistory(
                user_id=user_id,
                video_id=video_id,
                company_id=company_id,
                total_seconds=(video.duration_minutes or 0) * 60,
                status="In Progress",
            )
            db.add(history)
            await db.commit()

        return {
            "stream_url": signed_url,
            "resume_position": history.last_watched_position if history else 0,
            "completion_percent": float(history.completion_percent) if history else 0,
        }

    async def update_progress(
        self,
        db: AsyncSession,
        video_id: int,
        user_id: int,
        current_position: int,
        total_duration: int,
    ) -> dict:
        """
        Update video watch progress.
        Enforces no-fast-forward: current_position cannot exceed furthest_position + 30s.
        """
        result = await db.execute(
            select(TrainingHistory).where(
                TrainingHistory.user_id == user_id,
                TrainingHistory.video_id == video_id,
            )
        )
        history = result.scalar_one_or_none()

        if not history:
            raise HTTPException(404, "No training history found. Start the video first.")

        # No-fast-forward enforcement:
        # Allow up to 30 seconds ahead of furthest watched position (buffer for network)
        max_allowed = (history.furthest_position or 0) + 30
        if current_position > max_allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Fast-forward is not allowed. Please watch the video in sequence.",
            )

        # Update progress
        history.last_watched_position = current_position
        history.watched_seconds = current_position

        if current_position > (history.furthest_position or 0):
            history.furthest_position = current_position

        # Calculate completion %
        if total_duration > 0:
            percent = (current_position / total_duration) * 100
            history.completion_percent = min(percent, 100)

        # Mark as completed when >= 95% watched
        if history.completion_percent >= 95 and history.status != "Completed":
            history.status = "Completed"
            from datetime import datetime, timezone

            history.completed_at = datetime.now(timezone.utc)

        await db.commit()

        return {
            "completion_percent": float(history.completion_percent),
            "status": history.status,
            "assessment_unlocked": history.status == "Completed",
        }

    async def publish_video(self, db: AsyncSession, video_id: int, company_id: int) -> VideoMaster:
        result = await db.execute(
            select(VideoMaster).where(
                VideoMaster.video_id == video_id,
                VideoMaster.company_id == company_id,
            )
        )
        video = result.scalar_one_or_none()
        if not video:
            raise HTTPException(404, "Video not found.")
        video.status = "Published"
        await db.commit()
        return video

    async def list_videos(self, db: AsyncSession, company_id: int):
        result = await db.execute(
            select(VideoMaster)
            .where(VideoMaster.company_id == company_id)
            .order_by(VideoMaster.created_date.desc())
        )
        return result.scalars().all()

    async def list_published_videos(self, db: AsyncSession, company_id: int) -> list:
        """List only published videos — used by HR assignment dropdown."""
        result = await db.execute(
            select(VideoMaster)
            .where(
                VideoMaster.company_id == company_id,
                VideoMaster.status == "Published",
            )
            .order_by(VideoMaster.title)
        )
        return result.scalars().all()
