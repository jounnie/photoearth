# --- PYTHON LERNEN: Externe Bibliotheken ---
# "anthropic" ist das offizielle Python-SDK für die Claude-KI-API.
# Es muss installiert sein (pip install anthropic).
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import anthropic  # Anthropic SDK für Claude

# --- PYTHON LERNEN: base64 ---
# base64 kodiert Binärdaten (Bytes) als Text – nötig um Bilder per JSON/API zu senden.
import base64
import os

from ..database import get_db
from ..models import Photo
from ..schemas import PhotoOut

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")

router = APIRouter(prefix="/ai", tags=["ai"])

# --- PYTHON LERNEN: API-Client erstellen ---
# anthropic.Anthropic() liest automatisch den API-Key aus der Umgebungsvariable ANTHROPIC_API_KEY.
# Umgebungsvariablen = Konfiguration außerhalb des Codes (sicher für Passwörter/Keys).
client = anthropic.Anthropic()


# --- PYTHON LERNEN: Pydantic-Modell für die KI-Antwort ---
class LocationResult(BaseModel):
    lat: float
    lng: float
    location_name: str
    confidence: str   # Erlaubte Werte: "high" | "medium" | "low"
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

    # --- PYTHON LERNEN: JSON parsen ---
    # json ist ein eingebautes Modul zum Lesen/Schreiben von JSON.
    # Import innerhalb der Funktion ist erlaubt (aber unüblich – normalerweise oben).
    import json
    try:
        # message.content[0].text = der Antworttext der KI (erstes Element der Liste)
        # json.loads() konvertiert JSON-String → Python-dict
        result = json.loads(message.content[0].text)

        # .get() auf dict: sicher lesen ohne KeyError wenn Schlüssel fehlt
        if result.get("lat") is None or result.get("lng") is None:
            raise HTTPException(422, "Could not determine location from image")

        # float() konvertiert sicher zu Dezimalzahl (auch wenn KI int zurückgibt)
        photo.manual_lat = float(result["lat"])
        photo.manual_lng = float(result["lng"])
        photo.location_name = result.get("location_name")
        photo.location_source = "ai"
        db.commit()
        db.refresh(photo)
        return photo

    # --- PYTHON LERNEN: Mehrere Fehlertypen abfangen ---
    # json.JSONDecodeError: KI hat kein gültiges JSON gesendet
    # KeyError: erwarteter Schlüssel fehlt im dict
    # ValueError: Typkonvertierung (float()) fehlgeschlagen
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        # f-String mit Variable: {e} wird durch die Fehlermeldung ersetzt
        raise HTTPException(500, f"Failed to parse AI response: {e}")
