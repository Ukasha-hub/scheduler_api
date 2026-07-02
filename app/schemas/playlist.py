# app/schemas/playlist.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class PlaylistBase(BaseModel):
    label: Optional[str] = Field(None, max_length=255)
    name: Optional[str] = Field(None, max_length=255)
    timecode: Optional[str] = Field(None, max_length=255)
    starttime: Optional[str] = Field(None, max_length=255)
    seek: Optional[str] = Field("0", max_length=255)
    length: Optional[str] = Field("0", max_length=255)
    state: Optional[str] = Field(None, max_length=10)
    pushtime: Optional[datetime] = None
    asset_id: Optional[str] = Field(None, max_length=255)
    scheduler_id: Optional[int] = None
    createdby: Optional[str] = Field(None, max_length=255)
    updatedby: Optional[str] = Field(None, max_length=255)
    slug_name: Optional[str] = Field(None, max_length=255)


class PlaylistCreate(BaseModel):
    """Schema for creating a new playlist."""
    label: Optional[str] = Field(None, max_length=255)
    name: str = Field(..., max_length=255, description="Name is required")
    timecode: Optional[str] = Field(None, max_length=255)
    starttime: Optional[str] = Field(None, max_length=255)
    seek: Optional[str] = Field("0", max_length=255)
    length: Optional[str] = Field("0", max_length=255)
    state: Optional[str] = Field(None, max_length=10)
    pushtime: Optional[datetime] = None
    asset_id: Optional[str] = Field(None, max_length=255)
    scheduler_id: Optional[int] = None
    createdby: str = Field(..., max_length=255, description="Creator name is required")
    slug_name: Optional[str] = Field(None, max_length=255)


class PlaylistResponse(BaseModel):
    """Schema for GET response."""
    id: int
    label: Optional[str] = None
    name: Optional[str] = None
    timecode: Optional[str] = None
    starttime: Optional[str] = None
    seek: Optional[str] = "0"
    length: Optional[str] = "0"
    state: Optional[str] = None
    pushtime: Optional[datetime] = None
    asset_id: Optional[str] = None
    scheduler_id: Optional[int] = None
    createdby: Optional[str] = None
    updatedby: Optional[str] = None
    slug_name: Optional[str] = None
    created: Optional[datetime] = None
    updated: Optional[datetime] = None

    class Config:
        from_attributes = True


class PlaylistListResponse(BaseModel):
    """Schema for paginated GET list response."""
    total: int
    items: List[PlaylistResponse]
    page: int
    size: int
    pages: int