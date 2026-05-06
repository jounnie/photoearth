from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PhotoOut(BaseModel):
    id: int
    filename: str
    original_name: str
    album_id: Optional[int]
    exif_lat: Optional[float]
    exif_lng: Optional[float]
    manual_lat: Optional[float]
    manual_lng: Optional[float]
    lat: Optional[float]
    lng: Optional[float]
    gps_type: str
    location_name: Optional[str]
    location_source: Optional[str]
    taken_at: Optional[datetime]
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class PhotoGpsUpdate(BaseModel):
    lat: float
    lng: float
    location_name: Optional[str] = None


class AlbumCreate(BaseModel):
    name: str
    description: str = ""


class AlbumOut(BaseModel):
    id: int
    name: str
    description: str
    created_at: datetime
    photo_count: int = 0

    model_config = {"from_attributes": True}


class AlbumUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
