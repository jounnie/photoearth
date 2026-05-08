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


# --- PYTHON LERNEN: GET-Route mit komplexer Datenbankabfrage ---
@router.get("/", response_model=list[AlbumOut])
def list_albums(db: Session = Depends(get_db)):
    # SQL: SELECT * FROM albums ORDER BY created_at DESC
    # .desc() = absteigend (neueste zuerst)
    albums = db.scalars(select(Album).order_by(Album.created_at.desc())).all()

    # --- PYTHON LERNEN: Aggregation mit GROUP BY ---
    # func.count() = COUNT(*) in SQL
    # group_by = GROUP BY in SQL: zählt Fotos pro Album
    # .all() gibt eine Liste von Tupeln zurück: [(album_id, count), ...]
    counts = dict(
        db.execute(
            select(Photo.album_id, func.count()).group_by(Photo.album_id)
        ).all()
    )
    # dict() macht aus der Liste von Tupeln ein Wörterbuch: {album_id: count}

    # --- PYTHON LERNEN: List Comprehension + model_copy() ---
    # model_copy(update={...}) erstellt eine Kopie des Pydantic-Objekts mit neuen Feldern.
    # Das ist expliziter als eine nachträgliche Zuweisung – der Leser sieht sofort,
    # dass photo_count bewusst überschrieben wird.
    return [
        AlbumOut.model_validate(a).model_copy(update={"photo_count": counts.get(a.id, 0)})
        for a in albums
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
