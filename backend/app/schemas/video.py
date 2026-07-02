from typing import Optional

from pydantic import BaseModel


class VideoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category_id: Optional[int] = None
    duration_minutes: Optional[int] = None


class VideoResponse(BaseModel):
    video_id: int
    title: str
    description: Optional[str]
    status: str
    duration_minutes: Optional[int]
    created_date: Optional[str] = None

    class Config:
        from_attributes = True


class ProgressUpdate(BaseModel):
    current_position: int  # current playback position in seconds
    total_duration: int  # total video length in seconds
