# --- PYTHON LERNEN: Pydantic für Datenschemas ---
# Pydantic prüft automatisch ob die Daten den richtigen Typ haben.
# BaseModel ist die Basisklasse für alle Pydantic-Modelle.
from pydantic import BaseModel

from datetime import datetime

# --- PYTHON LERNEN: Moderne Typ-Syntax (Python 3.10+) ---
# "X | None" bedeutet: der Wert kann X sein ODER leer (None).
# Das ersetzt das ältere "Optional[X]" aus dem typing-Modul – gleiche Bedeutung, kürzere Schreibweise.
# Da dieses Projekt Python 3.13 voraussetzt, nutzen wir die moderne Variante überall.

# --- PYTHON LERNEN: Literal-Typen (Open/Closed Principle) ---
# Literal["a", "b", "c"] erlaubt nur diese drei Strings – keine anderen.
# Pydantic prüft das automatisch bei der Validierung.
# Vorteil: Fehler werden früh erkannt, nicht erst wenn etwas falsch in der DB landet.
from typing import Literal

# Alle gültigen Werte für location_source an einem Ort definiert.
# Wenn ein neuer Wert dazukommt (z.B. "manual_import"), nur hier ändern.
LocationSource = Literal["exif", "manual", "ai"]


# --- PYTHON LERNEN: Datenklassen mit Typ-Annotationen ---
# "class FooOut(BaseModel)" = FooOut erbt von BaseModel (Pydantic)
# Typ-Annotationen: variable: Typ = Standardwert
# Sie beschreiben welche Felder die Klasse hat und welchen Typ jedes Feld hat.
class PhotoOut(BaseModel):
    id: int                        # int = ganze Zahl
    filename: str                  # str = Text
    original_name: str
    album_id: int | None           # int | None = kann auch leer sein
    exif_lat: float | None         # float = Dezimalzahl
    exif_lng: float | None
    manual_lat: float | None
    manual_lng: float | None
    lat: float | None
    lng: float | None
    gps_type: str
    location_name: str | None
    location_source: LocationSource | None
    taken_at: datetime | None      # datetime = Datum + Uhrzeit
    uploaded_at: datetime

    # --- PYTHON LERNEN: model_config ---
    # from_attributes=True: Pydantic kann Daten auch aus Objekten lesen (nicht nur aus dicts).
    # Das brauchen wir, weil SQLAlchemy-Objekte keine dicts sind.
    model_config = {"from_attributes": True}


# Schema für eingehende GPS-Daten (vom Nutzer gesendet)
class PhotoGpsUpdate(BaseModel):
    lat: float
    lng: float
    location_name: str | None = None  # Standardwert None: wenn nicht angegeben, bleibt es leer


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
    name: str | None = None         # None = nicht geändert
    description: str | None = None
