# --- PYTHON LERNEN: FastAPI-Imports für Routen ---
# APIRouter = Gruppe von Routen
# Depends = Abhängigkeiten (z.B. Datenbankverbindung)
# HTTPException = Fehlerantwort mit HTTP-Statuscode
# UploadFile, File = für Datei-Uploads
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse   # Gibt eine Datei als Antwort zurück
from sqlalchemy.orm import Session
from sqlalchemy import select

# --- PYTHON LERNEN: uuid für eindeutige IDs ---
# uuid4() erzeugt eine zufällige, weltweit eindeutige ID (z.B. für Dateinamen)
import uuid
import os

# --- PYTHON LERNEN: aiofiles für asynchrones Dateischreiben ---
# aiofiles öffnet Dateien ohne den Event-Loop zu blockieren.
# Ohne aiofiles würde "with open(...)" alle anderen Anfragen pausieren.
import aiofiles

# Relative Imports aus dem Elternpaket (..= eine Ebene höher)
from ..database import get_db
from ..models import Photo
from ..schemas import PhotoOut, PhotoGpsUpdate
from ..exif_utils import extract_metadata

# --- PYTHON LERNEN: Konstanten ---
# Großbuchstaben = Konvention für Konstanten (Werte die sich nicht ändern)
# os.makedirs mit exist_ok=True erstellt den Ordner, falls er nicht existiert
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- PYTHON LERNEN: APIRouter ---
# prefix="/photos" → alle Routen dieses Routers beginnen mit /photos
# tags=["photos"] → Gruppierung in der automatischen API-Dokumentation
router = APIRouter(prefix="/photos", tags=["photos"])


# --- PYTHON LERNEN: Private async-Hilfsfunktion (Single Responsibility) ---
# Eine Funktion, eine Aufgabe: eine einzelne Datei validieren, speichern, EXIF lesen.
# Sie gibt Photo zurück oder None, wenn die Datei kein gültiges Bild ist.
# "Photo | None" = Photo-Objekt ODER leer – modernes Python 3.10+ Syntax.
async def _process_upload(
    file: UploadFile,
    upload_dir: str,
    album_id: int | None,
) -> "Photo | None":
    if not file.content_type or not file.content_type.startswith("image/"):
        return None

    data = await file.read()
    meta = extract_metadata(data)

    ext = os.path.splitext(file.filename or "photo.jpg")[1].lower() or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"

    async with aiofiles.open(os.path.join(upload_dir, filename), "wb") as f:
        await f.write(data)

    return Photo(
        filename=filename,
        original_name=file.filename or filename,
        album_id=album_id,
        exif_lat=meta["lat"],
        exif_lng=meta["lng"],
        taken_at=meta["taken_at"],
        location_source="exif" if meta["lat"] is not None else None,
    )


# --- PYTHON LERNEN: Dekoratoren (@) ---
# @router.get("/") ist ein Dekorator: er "verpackt" die Funktion darunter.
# Er sagt FastAPI: "Wenn jemand GET /photos/ aufruft, führe list_photos() aus."
# response_model=list[PhotoOut] → FastAPI wandelt das Ergebnis automatisch in JSON um.
@router.get("/", response_model=list[PhotoOut])
def list_photos(album_id: int | None = None, db: Session = Depends(get_db)):
    # --- PYTHON LERNEN: Depends() ---
    # Depends(get_db) sagt FastAPI: ruf get_db() auf und übergib das Ergebnis als "db".
    # Das ist "Dependency Injection" – die Funktion bekommt ihre Abhängigkeiten von außen.

    # select(Photo) = SQL: SELECT * FROM photos
    q = select(Photo)
    if album_id is not None:
        # .where() fügt eine WHERE-Bedingung hinzu
        q = q.where(Photo.album_id == album_id)
    # db.scalars().all() führt die Abfrage aus und gibt eine Liste zurück
    return db.scalars(q.order_by(Photo.uploaded_at.desc())).all()


# --- PYTHON LERNEN: async def ---
# "async def" definiert eine asynchrone Funktion.
# Asynchron = Python kann während des Wartens (z.B. auf Datei-Upload) andere Anfragen bearbeiten.
# "await" wartet auf das Ergebnis einer asynchronen Operation.
@router.post("/upload", response_model=list[PhotoOut])
async def upload_photos(
    files: list[UploadFile] = File(...),   # File(...) = Pflichtfeld (... = required)
    album_id: int | None = None,
    db: Session = Depends(get_db),
):
    results = []  # Leere Liste, wird mit hochgeladenen Fotos gefüllt

    # --- PYTHON LERNEN: for-Schleife + Hilfsfunktion ---
    # _process_upload() kümmert sich um Validierung, Speichern und EXIF-Extraktion.
    # Diese Schleife ist nur noch für die Datenbankoperationen zuständig.
    for file in files:
        # await = warte bis _process_upload() fertig ist
        # None bedeutet: keine gültige Bilddatei → überspringen
        photo = await _process_upload(file, UPLOAD_DIR, album_id)
        if photo is None:
            continue  # "continue" überspringt den Rest und geht zum nächsten file

        db.add(photo)         # Objekt zur Session hinzufügen (noch nicht gespeichert)
        results.append(photo)

    # --- PYTHON LERNEN: Batch-Flush statt flush() pro Datei ---
    # Ein einziger flush() schreibt alle neuen Objekte auf einmal in die DB.
    # Das spart N-1 Datenbank-Roundtrips bei einem Upload von N Dateien.
    if results:
        db.flush()   # IDs vergeben (noch kein Commit)
    db.commit()      # Alle Änderungen dauerhaft speichern
    for p in results:
        db.refresh(p)  # Aktuellen Stand aus der DB neu laden
    return results


# --- PYTHON LERNEN: Pfad-Parameter ---
# {photo_id} im Pfad ist ein Pfad-Parameter – FastAPI liest ihn aus der URL.
# photo_id: int → FastAPI konvertiert den String aus der URL automatisch in int.
@router.get("/{photo_id}/image")
def get_image(photo_id: int, db: Session = Depends(get_db)):
    photo = db.get(Photo, photo_id)  # Einzelnes Objekt per ID laden
    if not photo:
        # HTTPException wirft einen HTTP-Fehler (hier: 404 Not Found)
        raise HTTPException(404, "Photo not found")
    path = os.path.join(UPLOAD_DIR, photo.filename)
    if not os.path.exists(path):
        raise HTTPException(404, "File not found")
    return FileResponse(path)  # Datei direkt zurückgeben (kein JSON)


# --- PYTHON LERNEN: PATCH-Methode ---
# PATCH = nur bestimmte Felder eines Eintrags aktualisieren (im Gegensatz zu PUT = alles)
@router.patch("/{photo_id}/gps", response_model=PhotoOut)
def update_gps(photo_id: int, body: PhotoGpsUpdate, db: Session = Depends(get_db)):
    photo = db.get(Photo, photo_id)
    if not photo:
        raise HTTPException(404, "Photo not found")
    # Attribute des Objekts direkt setzen
    photo.manual_lat = body.lat
    photo.manual_lng = body.lng
    photo.location_name = body.location_name
    photo.location_source = "manual"
    db.commit()
    db.refresh(photo)
    return photo


# int | None = None macht album_id explizit optional (kein Pflichtfeld)
@router.patch("/{photo_id}/album", response_model=PhotoOut)
def assign_album(photo_id: int, album_id: int | None = None, db: Session = Depends(get_db)):
    photo = db.get(Photo, photo_id)
    if not photo:
        raise HTTPException(404, "Photo not found")
    photo.album_id = album_id
    db.commit()
    db.refresh(photo)
    return photo


# --- PYTHON LERNEN: DELETE-Methode und Statuscode ---
# status_code=204 = "No Content": Erfolg, aber keine Antwort zurückgeben
@router.delete("/{photo_id}", status_code=204)
def delete_photo(photo_id: int, db: Session = Depends(get_db)):
    photo = db.get(Photo, photo_id)
    if not photo:
        raise HTTPException(404, "Photo not found")
    path = os.path.join(UPLOAD_DIR, photo.filename)
    if os.path.exists(path):
        os.remove(path)  # Datei vom Dateisystem löschen
    db.delete(photo)     # Eintrag aus der Datenbank löschen
    db.commit()
