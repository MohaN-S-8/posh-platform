from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_roles
from app.db.session import get_db
from app.schemas.video import ProgressUpdate, VideoCreate, VideoResponse
from app.services.video_service import VideoService

router = APIRouter(prefix="/videos", tags=["Video Management"])
video_service = VideoService()


@router.post("/upload", response_model=VideoResponse, status_code=201)
async def upload_video(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(None),
    category_id: int = Form(None),
    duration_minutes: int = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([1, 2])),  # Admin only
):
    """
    Upload a video file. Accepts MP4, AVI, MOV up to 500MB.
    File is stored securely in MinIO — never publicly accessible.
    """
    metadata = VideoCreate(
        title=title,
        description=description,
        category_id=category_id,
        duration_minutes=duration_minutes,
    )
    return await video_service.upload_video(
        db, file, metadata, current_user.user_id, current_user.company_id
    )


@router.patch("/{video_id}/publish")
async def publish_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([1, 2])),
):
    """Publish a video so employees can watch it."""
    return await video_service.publish_video(db, video_id, current_user.company_id)


@router.get("/{video_id}/stream-url")
async def get_stream_url(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get a short-lived signed URL for video streaming.
    URL expires in 5 minutes — prevents sharing.
    Employee must be assigned this course.
    """
    return await video_service.get_stream_url(
        db, video_id, current_user.user_id, current_user.company_id
    )


@router.post("/{video_id}/progress")
async def update_progress(
    video_id: int,
    data: ProgressUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Update video watch progress (called every 10 seconds by the player).
    Enforces no-fast-forward. Returns completion status and assessment unlock.
    """
    return await video_service.update_progress(
        db,
        video_id,
        current_user.user_id,
        data.current_position,
        data.total_duration,
    )
