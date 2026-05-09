# --- PYTHON LERNEN: Imports ---
# Wir importieren genau das, was wir brauchen – nicht mehr.
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func  # func = SQL-Aggregatfunktionen (COUNT, SUM, ...)

from ..database import get_db
from ..models import Album, Photo
from ..schemas import AlbumCreate, AlbumOut, AlbumUpdate

# Router mit Präfix: alle Routen beginnen mit /albums
router = APIRouter(prefix="/albums", tags=["albums"])


# --- PYTHON LERNEN: GET-Route mit JOIN-Datenbankabfrage ---
@router.get("/", response_model=list[AlbumOut])
def list_albums(db: Session = Depends(get_db)):
    # --- PYTHON LERNEN: LEFT OUTER JOIN + GROUP BY in einer Abfrage ---
    # Statt zwei separater Abfragen (Albums + Foto-Zählung) erledigt ein JOIN beides.
    # LEFT OUTER JOIN: Alben ohne Fotos werden trotzdem zurückgegeben (count = 0).
    # func.count(Photo.id) zählt nur Zeilen wo Photo.id nicht NULL ist (korrekt für LEFT JOIN).
    rows = db.execute(
        select(Album, func.count(Photo.id).label("photo_count"))
        .outerjoin(Photo, Photo.album_id == Album.id)
        .group_by(Album.id)
        .order_by(Album.created_at.desc())
    ).all()

    # --- PYTHON LERNEN: Tupel-Unpacking in List Comprehension ---
    # Jede Zeile ist ein Tupel (Album-Objekt, Zahl).
    # album, count = row trennt die beiden Werte.
    return [
        AlbumOut.model_validate(album).model_copy(update={"photo_count": count})
        for album, count in rows
    ]


# --- PYTHON LERNEN: POST-Route zum Erstellen ---
# status_code=201 = "Created": der Standard für erfolgreiche POST-Anfragen
@router.post("/", response_model=AlbumOut, status_code=201)
def create_album(body: AlbumCreate, db: Session = Depends(get_db)):
    # Neues Album-Objekt erstellen mit den Daten aus dem Request-Body
    album = Album(name=body.name, description=body.description)
    db.add(album)
    db.commit()
    db.refresh(album)
    # Neues Album hat noch keine Fotos → Standardwert 0 aus AlbumOut.photo_count greift
    return AlbumOut.model_validate(album)


# --- PYTHON LERNEN: Bedingte Updates (Partial Update) ---
@router.patch("/{album_id}", response_model=AlbumOut)
def update_album(album_id: int, body: AlbumUpdate, db: Session = Depends(get_db)):
    album = db.get(Album, album_id)
    if not album:
        raise HTTPException(404, "Album not found")
    # "is not None" prüft ob das Feld im Request angegeben wurde
    # Nur überschreiben wenn tatsächlich ein neuer Wert gesendet wurde
    if body.name is not None:
        album.name = body.name
    if body.description is not None:
        album.description = body.description
    db.commit()
    db.refresh(album)
    # db.scalar() gibt einen einzelnen Wert zurück (nicht eine Liste)
    count = db.scalar(select(func.count()).where(Photo.album_id == album_id))
    # "or 0" = falls count None ist (kein Foto), nimm 0
    return AlbumOut.model_validate(album).model_copy(update={"photo_count": count or 0})


# --- PYTHON LERNEN: DELETE-Route ---
@router.delete("/{album_id}", status_code=204)
def delete_album(album_id: int, db: Session = Depends(get_db)):
    album = db.get(Album, album_id)
    if not album:
        raise HTTPException(404, "Album not found")
    # cascade="all, delete-orphan" in models.py sorgt dafür,
    # dass alle Fotos des Albums ebenfalls gelöscht werden.
    db.delete(album)
    db.commit()
