from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_roles
from app.db.session import get_db
from app.schemas.video import ProgressUpdate, VideoCreate, VideoListResponse, VideoResponse
from app.services.video_service import VideoService

router = APIRouter(prefix="/videos", tags=["Video Management"])
video_service = VideoService()


@router.get("/", response_model=list[VideoListResponse])
async def list_videos(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all videos for current user's company (all statuses)."""
    return await video_service.list_videos(db, current_user.company_id)


@router.get("/published", response_model=list[VideoListResponse])
async def list_published_videos(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([1, 2, 3])),
):
    """List only published videos — used by HR training assignment dropdown."""
    return await video_service.list_published_videos(db, current_user.company_id)


@router.post("/upload", response_model=VideoResponse, status_code=201)
async def upload_video(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(None),
    category_id: int = Form(None),
    duration_minutes: int = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([1, 2])),
):
    """
    Upload a video file. Accepts MP4, AVI, MOV up to 500MB.
    File is stored securely in MinIO — never publicly accessible.
    Status starts as Draft. Publish separately.
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
    """Publish a draft video so employees can watch it."""
    return await video_service.publish_video(db, video_id, current_user.company_id)


@router.patch("/{video_id}/archive")
async def archive_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([1, 2])),
):
    """Archive a published video — removes it from employee view."""
    from sqlalchemy import select

    from app.models.video import VideoMaster

    result = await db.execute(
        select(VideoMaster).where(
            VideoMaster.video_id == video_id,
            VideoMaster.company_id == current_user.company_id,
        )
    )
    video = result.scalar_one_or_none()
    if not video:
        from fastapi import HTTPException

        raise HTTPException(404, "Video not found.")
    video.status = "Archived"
    await db.commit()
    return {"message": f"Video '{video.title}' archived."}


@router.get("/{video_id}/stream-url")
async def get_stream_url(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get a short-lived signed URL for video streaming.
    URL expires in 5 minutes. Employee must be assigned this course.
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
    Enforces no-fast-forward. Returns completion status and assessment unlock flag.
    """
    return await video_service.update_progress(
        db,
        video_id,
        current_user.user_id,
        data.current_position,
        data.total_duration,
    )
