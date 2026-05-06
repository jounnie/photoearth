from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from ..database import get_db
from ..models import Album, Photo
from ..schemas import AlbumCreate, AlbumOut, AlbumUpdate

router = APIRouter(prefix="/albums", tags=["albums"])


@router.get("/", response_model=list[AlbumOut])
def list_albums(db: Session = Depends(get_db)):
    albums = db.scalars(select(Album).order_by(Album.created_at.desc())).all()
    counts = dict(
        db.execute(
            select(Photo.album_id, func.count()).group_by(Photo.album_id)
        ).all()
    )
    result = []
    for album in albums:
        out = AlbumOut.model_validate(album)
        out.photo_count = counts.get(album.id, 0)
        result.append(out)
    return result


@router.post("/", response_model=AlbumOut, status_code=201)
def create_album(body: AlbumCreate, db: Session = Depends(get_db)):
    album = Album(name=body.name, description=body.description)
    db.add(album)
    db.commit()
    db.refresh(album)
    out = AlbumOut.model_validate(album)
    out.photo_count = 0
    return out


@router.patch("/{album_id}", response_model=AlbumOut)
def update_album(album_id: int, body: AlbumUpdate, db: Session = Depends(get_db)):
    album = db.get(Album, album_id)
    if not album:
        raise HTTPException(404, "Album not found")
    if body.name is not None:
        album.name = body.name
    if body.description is not None:
        album.description = body.description
    db.commit()
    db.refresh(album)
    count = db.scalar(select(func.count()).where(Photo.album_id == album_id))
    out = AlbumOut.model_validate(album)
    out.photo_count = count or 0
    return out


@router.delete("/{album_id}", status_code=204)
def delete_album(album_id: int, db: Session = Depends(get_db)):
    album = db.get(Album, album_id)
    if not album:
        raise HTTPException(404, "Album not found")
    db.delete(album)
    db.commit()
