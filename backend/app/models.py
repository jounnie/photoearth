# --- PYTHON LERNEN: Imports aus SQLAlchemy ---
# Wir importieren genau die Klassen, die wir brauchen (nicht die ganze Bibliothek).
# Column = eine Tabellenspalte, Integer/String/Float/... = Datentypen
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

# --- PYTHON LERNEN: datetime-Modul ---
# datetime ist ein eingebautes Python-Modul für Datum und Uhrzeit.
# timezone.utc = koordinierte Weltzeit (kein Sommerzeit-Problem)
from datetime import datetime, timezone

from .database import Base  # relativer Import: Punkt = aktuelles Paket (app/)


# --- PYTHON LERNEN: Klasse mit Vererbung ---
# Album erbt von Base (steht in der Klammer).
# Durch die Vererbung weiß SQLAlchemy, dass Album eine Datenbanktabelle ist.
class Album(Base):
    # __tablename__ ist ein spezielles Klassenattribut (doppelte Unterstriche = "dunder").
    # SQLAlchemy liest es aus, um den Tabellennamen in der Datenbank zu bestimmen.
    __tablename__ = "albums"

    # --- PYTHON LERNEN: Klassenattribute ---
    # Diese Attribute existieren auf der Klasse selbst, nicht auf einer Instanz.
    # Column(...) beschreibt eine Spalte in der Datenbanktabelle.
    id = Column(Integer, primary_key=True, index=True)  # Eindeutige ID, automatisch erhöht
    name = Column(String, nullable=False)               # nullable=False = darf nicht leer sein
    description = Column(Text, default="")              # default = Standardwert wenn nichts angegeben
    # lambda: ... ist eine anonyme Mini-Funktion, hier wird sie bei jeder neuen Zeile aufgerufen
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # --- PYTHON LERNEN: Beziehungen zwischen Tabellen ---
    # relationship() sagt SQLAlchemy: ein Album hat mehrere Photos.
    # cascade="all, delete-orphan" = wenn Album gelöscht wird, werden auch alle Photos gelöscht.
    photos = relationship("Photo", back_populates="album", cascade="all, delete-orphan")


class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)       # Dateiname auf dem Server (zufällig generiert)
    original_name = Column(String, nullable=False)  # Originalname beim Hochladen

    # --- PYTHON LERNEN: Optionale Spalten ---
    # nullable=True (oder kein Argument) = der Wert darf NULL (leer) sein
    album_id = Column(Integer, ForeignKey("albums.id"), nullable=True)  # Fremdschlüssel

    exif_lat = Column(Float, nullable=True)   # GPS-Breitengrad aus den Bilddaten
    exif_lng = Column(Float, nullable=True)   # GPS-Längengrad aus den Bilddaten

    manual_lat = Column(Float, nullable=True)        # Manuell gesetzt oder via AI
    manual_lng = Column(Float, nullable=True)
    location_name = Column(String, nullable=True)    # z.B. "Zürich, Schweiz"
    location_source = Column(String, nullable=True)  # "exif" | "manual" | "ai"

    taken_at = Column(DateTime, nullable=True)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Rückbeziehung: Photo kennt sein Album (andere Richtung)
    album = relationship("Album", back_populates="photos")

    # --- PYTHON LERNEN: Properties (@property) ---
    # @property macht eine Methode zu einem Attribut – kein () beim Aufrufen nötig.
    # photo.lat statt photo.lat()
    @property
    def lat(self):
        # "if X is not None" prüft ob X einen Wert hat (nicht leer ist).
        # Kurzschreibweise für: wenn manual_lat gesetzt ist, nimm es, sonst exif_lat
        return self.manual_lat if self.manual_lat is not None else self.exif_lat

    @property
    def lng(self):
        return self.manual_lng if self.manual_lng is not None else self.exif_lng

    @property
    def gps_type(self):
        # Mehrere Variablen auf einmal zuweisen (Tuple Unpacking)
        lat, lng = self.lat, self.lng
        # Vergleich mit "is None": prüft ob ein Wert wirklich leer (None) ist
        if lat is None:
            return "none"
        # Vergleich mit ==: prüft ob zwei Werte gleich sind
        if lat == 0.0 and lng == 0.0:
            return "zero"
        return "ok"
