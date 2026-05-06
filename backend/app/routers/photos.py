from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional
import uuid
import os

from ..database import get_db
from ..models import Photo
from ..schemas import PhotoOut, PhotoGpsUpdate
from ..exif_utils import extract_metadata

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter(prefix="/photos", tags=["photos"])


@router.get("/", response_model=list[PhotoOut])
def list_photos(album_id: Optional[int] = None, db: Session = Depends(get_db)):
    q = select(Photo)
    if album_id is not None:
        q = q.where(Photo.album_id == album_id)
    return db.scalars(q.order_by(Photo.uploaded_at.desc())).all()


@router.post("/upload", response_model=list[PhotoOut])
async def upload_photos(
    files: list[UploadFile] = File(...),
    album_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    results = []
    for file in files:
        if not file.content_type or not file.content_type.startswith("image/"):
            continue

        data = await file.read()
        meta = extract_metadata(data)

        ext = os.path.splitext(file.filename or "photo.jpg")[1].lower() or ".jpg"
        filename = f"{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)

        with open(filepath, "wb") as f:
            f.write(data)

        photo = Photo(
            filename=filename,
            original_name=file.filename or filename,
            album_id=album_id,
            exif_lat=meta["lat"],
            exif_lng=meta["lng"],
            taken_at=meta["taken_at"],
            location_source="exif" if meta["lat"] is not None else None,
        )
        db.add(photo)
        db.flush()
        results.append(photo)

    db.commit()
    for p in results:
        db.refresh(p)
    return results


@router.get("/{photo_id}/image")
def get_image(photo_id: int, db: Session = Depends(get_db)):
    photo = db.get(Photo, photo_id)
    if not photo:
        raise HTTPException(404, "Photo not found")
    path = os.path.join(UPLOAD_DIR, photo.filename)
    if not os.path.exists(path):
        raise HTTPException(404, "File not found")
    return FileResponse(path)


@router.patch("/{photo_id}/gps", response_model=PhotoOut)
def update_gps(photo_id: int, body: PhotoGpsUpdate, db: Session = Depends(get_db)):
    photo = db.get(Photo, photo_id)
    if not photo:
        raise HTTPException(404, "Photo not found")
    photo.manual_lat = body.lat
    photo.manual_lng = body.lng
    photo.location_name = body.location_name
    photo.location_source = "manual"
    db.commit()
    db.refresh(photo)
    return photo


@router.patch("/{photo_id}/album", response_model=PhotoOut)
def assign_album(photo_id: int, album_id: Optional[int], db: Session = Depends(get_db)):
    photo = db.get(Photo, photo_id)
    if not photo:
        raise HTTPException(404, "Photo not found")
    photo.album_id = album_id
    db.commit()
    db.refresh(photo)
    return photo


@router.delete("/{photo_id}", status_code=204)
def delete_photo(photo_id: int, db: Session = Depends(get_db)):
    photo = db.get(Photo, photo_id)
    if not photo:
        raise HTTPException(404, "Photo not found")
    path = os.path.join(UPLOAD_DIR, photo.filename)
    if os.path.exists(path):
        os.remove(path)
    db.delete(photo)
    db.commit()
