# --- PYTHON LERNEN: Externe Bibliotheken ---
# "anthropic" ist das offizielle Python-SDK für die Claude-KI-API.
# Es muss installiert sein (pip install anthropic).
import json  # Eingebautes Modul – Imports gehören immer an den Anfang der Datei
import base64
import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, ValidationError  # ValidationError = Pydantic-Fehlerklasse
import anthropic  # Anthropic SDK für Claude

from ..database import get_db
from ..models import Photo
from ..schemas import PhotoOut

# --- PYTHON LERNEN: base64 ---
# base64 kodiert Binärdaten (Bytes) als Text – nötig um Bilder per JSON/API zu senden.

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")

router = APIRouter(prefix="/ai", tags=["ai"])

# --- PYTHON LERNEN: API-Client erstellen ---
# anthropic.Anthropic() liest automatisch den API-Key aus der Umgebungsvariable ANTHROPIC_API_KEY.
# Umgebungsvariablen = Konfiguration außerhalb des Codes (sicher für Passwörter/Keys).
client = anthropic.Anthropic()


# --- PYTHON LERNEN: Pydantic-Modell für die KI-Antwort ---
# float | None = Dezimalzahl ODER leer (wenn die KI den Ort nicht bestimmen kann).
# Pydantic validiert automatisch: passt der JSON-String dieses Schema? Wenn nicht → Fehler.
class LocationResult(BaseModel):
    lat: float | None
    lng: float | None
    location_name: str | None = None
    confidence: str              # Erlaubte Werte: "high" | "medium" | "low"
    reasoning: str


# --- PYTHON LERNEN: POST-Route mit KI-Integration ---
@router.post("/{photo_id}/detect-location", response_model=PhotoOut)
def detect_location(photo_id: int, db: Session = Depends(get_db)):
    photo = db.get(Photo, photo_id)
    if not photo:
        raise HTTPException(404, "Photo not found")

    path = os.path.join(UPLOAD_DIR, photo.filename)
    if not os.path.exists(path):
        raise HTTPException(404, "Image file not found")

    # --- PYTHON LERNEN: Datei lesen und base64 kodieren ---
    # "rb" = read binary (Binärdaten lesen, keine Textdatei)
    with open(path, "rb") as f:
        # base64.standard_b64encode() gibt Bytes zurück
        # .decode() konvertiert Bytes → String (UTF-8)
        image_data = base64.standard_b64encode(f.read()).decode()

    # --- PYTHON LERNEN: dict als Lookup-Tabelle ---
    # .get(key, default) sucht den Schlüssel; falls nicht gefunden: "image/jpeg"
    ext = os.path.splitext(photo.filename)[1].lower()
    media_type = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".webp": "image/webp", ".gif": "image/gif",
    }.get(ext, "image/jpeg")

    # --- PYTHON LERNEN: KI-API aufrufen ---
    # client.messages.create() sendet eine Anfrage an die Claude-API.
    # Das ist ein synchroner (blockierender) Aufruf – Python wartet auf die Antwort.
    message = client.messages.create(
        model="claude-opus-4-7",  # Welches Modell benutzt werden soll
        max_tokens=1024,          # Maximale Länge der Antwort (in Tokens ≈ Wortteilen)
        # messages = Liste von Nachrichten (wie ein Chatverlauf)
        messages=[{
            "role": "user",   # "user" = Nachricht vom Nutzer
            "content": [      # content = Liste von Inhaltselementen
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_data,  # Das base64-kodierte Bild
                    },
                },
                {
                    "type": "text",
                    # Langer String mit Klammern: Python verbindet Strings automatisch
                    "text": (
                        "Analyze this photo and determine where it was taken. "
                        "Respond ONLY with a JSON object (no markdown, no explanation) with these fields:\n"
                        '{"lat": <decimal latitude>, "lng": <decimal longitude>, '
                        '"location_name": "<City, Country>", '
                        '"confidence": "<high|medium|low>", '
                        '"reasoning": "<one sentence why>"}\n'
                        "If you cannot determine the location at all, set lat and lng to null."
                    ),
                },
            ],
        }],
    )

    # --- PYTHON LERNEN: Pydantic für JSON-Validierung nutzen ---
    # model_validate_json() parst den JSON-String UND validiert die Felder automatisch.
    # Bei ungültigem JSON oder falschem Schema wirft es ValidationError.
    try:
        result = LocationResult.model_validate_json(message.content[0].text)
    # --- PYTHON LERNEN: except mit einer Fehlerklasse ---
    # ValidationError fängt sowohl JSON-Fehler als auch Schema-Fehler ab.
    except ValidationError as e:
        raise HTTPException(500, f"Failed to parse AI response: {e}")

    if result.lat is None or result.lng is None:
        raise HTTPException(422, "Could not determine location from image")

    photo.manual_lat = result.lat
    photo.manual_lng = result.lng
    photo.location_name = result.location_name
    photo.location_source = "ai"
    db.commit()
    db.refresh(photo)
    return photo
