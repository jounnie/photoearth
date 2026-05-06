# --- PYTHON LERNEN: Pydantic für Datenschemas ---
# Pydantic prüft automatisch ob die Daten den richtigen Typ haben.
# BaseModel ist die Basisklasse für alle Pydantic-Modelle.
from pydantic import BaseModel

from datetime import datetime

# --- PYTHON LERNEN: typing-Modul ---
# Optional[X] bedeutet: der Wert kann vom Typ X sein ODER None (leer).
# Ab Python 3.10 kann man auch "X | None" schreiben – dasselbe Konzept.
from typing import Optional


# --- PYTHON LERNEN: Datenklassen mit Typ-Annotationen ---
# "class FooOut(BaseModel)" = FooOut erbt von BaseModel (Pydantic)
# Typ-Annotationen: variable: Typ = Standardwert
# Sie beschreiben welche Felder die Klasse hat und welchen Typ jedes Feld hat.
class PhotoOut(BaseModel):
    id: int                        # int = ganze Zahl
    filename: str                  # str = Text
    original_name: str
    album_id: Optional[int]        # Optional = kann auch None sein
    exif_lat: Optional[float]      # float = Dezimalzahl
    exif_lng: Optional[float]
    manual_lat: Optional[float]
    manual_lng: Optional[float]
    lat: Optional[float]
    lng: Optional[float]
    gps_type: str
    location_name: Optional[str]
    location_source: Optional[str]
    taken_at: Optional[datetime]   # datetime = Datum + Uhrzeit
    uploaded_at: datetime

    # --- PYTHON LERNEN: Verschachtelte Klassen und model_config ---
    # model_config ist ein dict mit Einstellungen für Pydantic.
    # from_attributes=True: Pydantic kann Daten auch aus Objekten lesen (nicht nur aus dicts).
    # Das brauchen wir, weil SQLAlchemy-Objekte keine dicts sind.
    model_config = {"from_attributes": True}


# Schema für eingehende GPS-Daten (vom Nutzer gesendet)
class PhotoGpsUpdate(BaseModel):
    lat: float
    lng: float
    # Standardwert None: wenn nicht angegeben, ist location_name leer
    location_name: Optional[str] = None


# Schema zum Erstellen eines Albums (nur Eingabefelder)
class AlbumCreate(BaseModel):
    name: str
    description: str = ""  # Standardwert leerer String


# Schema für Albumdaten in der Antwort (Ausgabe an den Client)
class AlbumOut(BaseModel):
    id: int
    name: str
    description: str
    created_at: datetime
    photo_count: int = 0  # Standardwert 0 (wird später befüllt)

    model_config = {"from_attributes": True}


# Schema für Aktualisierungen – alle Felder optional (Partial Update)
class AlbumUpdate(BaseModel):
    name: Optional[str] = None        # None = nicht geändert
    description: Optional[str] = None
