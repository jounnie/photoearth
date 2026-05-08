# --- PYTHON LERNEN: Pillow (PIL) ---
# PIL / Pillow ist eine Bibliothek zum Lesen und Bearbeiten von Bilddateien.
# TAGS und GPSTAGS sind dicts, die numerische EXIF-Codes in lesbare Namen übersetzen.
# IFD (Image File Directory) = Zeiger auf Sub-Tabellen innerhalb der EXIF-Daten.
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS, IFD

from datetime import datetime

# io = Input/Output-Modul, damit wir Bytes wie eine Datei behandeln können
import io

# --- PYTHON LERNEN: TypedDict ---
# TypedDict definiert ein dict mit festen Schlüsseln und bekannten Typen.
# Vorteil: IDE-Unterstützung und Typ-Prüfung – ohne Runtime-Overhead.
from typing import TypedDict


# --- PYTHON LERNEN: TypedDict-Definition ---
# Jede Klasse die TypedDict erbt ist ein gewöhnliches Python-dict,
# aber der Typ-Checker weiß welche Schlüssel und Typen erwartet werden.
class ExifMetadata(TypedDict):
    lat: float | None
    lng: float | None
    taken_at: datetime | None


# --- PYTHON LERNEN: Funktionen mit Typ-Annotationen ---
# "def name(parameter: Typ) -> Rückgabetyp:" definiert eine Funktion.
# Image.Image ist der Typ des Parameters (ein Pillow-Bild-Objekt).
# -> dict sagt: die Funktion gibt ein dict zurück.
# Der Unterstrich am Anfang (_get_exif) ist eine Konvention: "privat, nicht von außen benutzen".
def _get_exif(image: Image.Image) -> dict:
    # image.getexif() ist die öffentliche Pillow-API (seit Pillow 6.0).
    # Sie gibt ein hierarchisches Exif-Objekt zurück – GPS und Datum liegen in Sub-IFDs.
    exif = image.getexif()
    if not exif:             # "not exif" = True wenn keine EXIF-Daten vorhanden
        return {}

    # --- PYTHON LERNEN: Dict Comprehension ---
    # {ausdruck for variable in iterable} erzeugt ein dict in einer Zeile.
    # Haupt-IFD: enthält DateTime, Make, Model, ...
    result = {TAGS.get(tag, tag): value for tag, value in exif.items()}

    # Exif-Sub-IFD: enthält DateTimeOriginal, ExposureTime, ...
    # get_ifd() liest eine verschachtelte Sub-Tabelle aus.
    # setdefault schreibt nur wenn der Schlüssel noch nicht vorhanden ist.
    for tag, value in exif.get_ifd(IFD.Exif).items():
        result.setdefault(TAGS.get(tag, tag), value)

    # GPS-Sub-IFD: enthält GPSLatitude, GPSLongitude, ...
    gps_ifd = exif.get_ifd(IFD.GPSInfo)
    if gps_ifd:
        result["GPSInfo"] = dict(gps_ifd)  # als normales dict speichern

    return result


# --- PYTHON LERNEN: Verschachtelte Funktionen ---
# tuple[float | None, float | None] = die Funktion gibt ein Tupel mit zwei floats zurück.
# Tupel: runde Klammern (), unveränderlich, mehrere Werte auf einmal
def _parse_gps(gps_info: dict) -> tuple[float | None, float | None]:
    # "to_decimal" ist eine innere Funktion – sie existiert nur innerhalb von _parse_gps.
    def to_decimal(values, ref):
        # Tuple Unpacking: drei Werte aus der Liste auf einmal zuweisen
        d, m, s = values
        # Umrechnung von Grad/Minuten/Sekunden in Dezimalgrad
        decimal = float(d) + float(m) / 60 + float(s) / 3600
        # "in" prüft ob ein Wert in einem Tupel/Liste enthalten ist
        if ref in ("S", "W"):
            decimal = -decimal  # Süd und West sind negativ
        return decimal

    # --- PYTHON LERNEN: try/except für Fehlerbehandlung ---
    # Code in "try" wird versucht. Wenn ein Fehler passiert, springt Python zu "except".
    try:
        # Dict Comprehension um GPS-Tags in lesbare Namen umzuwandeln
        gps = {GPSTAGS.get(k, k): v for k, v in gps_info.items()}
        lat = to_decimal(gps["GPSLatitude"], gps["GPSLatitudeRef"])
        lng = to_decimal(gps["GPSLongitude"], gps["GPSLongitudeRef"])
        # Tupel mit zwei Werten zurückgeben
        return lat, lng
    # Mehrere Fehlertypen in einer Zeile abfangen (Klammern nötig)
    except (KeyError, TypeError, ZeroDivisionError):
        return None, None  # Bei Fehler: beide Werte leer


# --- PYTHON LERNEN: bytes als Parameter ---
# "data: bytes" = die Funktion erwartet rohe Binärdaten (den Inhalt einer Datei)
def extract_metadata(data: bytes) -> ExifMetadata:
    # io.BytesIO() macht aus einem bytes-Objekt ein "Datei-ähnliches Objekt"
    # So kann Pillow es wie eine echte Datei öffnen, ohne sie auf der Festplatte zu speichern.
    image = Image.open(io.BytesIO(data))
    exif = _get_exif(image)

    lat, lng = None, None
    # "in" prüft ob ein Schlüssel im dict vorhanden ist
    if "GPSInfo" in exif:
        lat, lng = _parse_gps(exif["GPSInfo"])

    taken_at = None
    # --- PYTHON LERNEN: for-Schleife über Tupel/Liste ---
    # Python probiert die Tags der Reihe nach, nimmt den ersten der gefunden wird.
    for tag in ("DateTimeOriginal", "DateTime"):
        if tag in exif:
            try:
                # strptime = "string parse time": Text → datetime-Objekt
                # "%Y:%m:%d %H:%M:%S" ist das Format der EXIF-Zeitangabe
                taken_at = datetime.strptime(exif[tag], "%Y:%m:%d %H:%M:%S")
            except ValueError:
                pass  # Falsches Format → ignorieren
            # break beendet die Schleife sofort (wir haben gefunden was wir suchten)
            break

    # --- PYTHON LERNEN: TypedDict-Instanz zurückgeben ---
    # ExifMetadata(...) sieht aus wie ein Konstruktor, erzeugt aber ein normales dict.
    return ExifMetadata(lat=lat, lng=lng, taken_at=taken_at)
