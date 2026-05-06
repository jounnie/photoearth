# --- PYTHON LERNEN: Pillow (PIL) ---
# PIL / Pillow ist eine Bibliothek zum Lesen und Bearbeiten von Bilddateien.
# TAGS und GPSTAGS sind dicts, die numerische EXIF-Codes in lesbare Namen übersetzen.
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

from datetime import datetime

# --- PYTHON LERNEN: typing für Typ-Hinweise ---
# Optional[float] = float oder None – hilft beim Verstehen des Codes
from typing import Optional

# io = Input/Output-Modul, damit wir Bytes wie eine Datei behandeln können
import io


# --- PYTHON LERNEN: Funktionen mit Typ-Annotationen ---
# "def name(parameter: Typ) -> Rückgabetyp:" definiert eine Funktion.
# Image.Image ist der Typ des Parameters (ein Pillow-Bild-Objekt).
# -> dict sagt: die Funktion gibt ein dict zurück.
# Der Unterstrich am Anfang (_get_exif) ist eine Konvention: "privat, nicht von außen benutzen".
def _get_exif(image: Image.Image) -> dict:
    raw = image._getexif()  # Rohe EXIF-Daten aus dem Bild holen
    if not raw:             # "not raw" = True wenn raw leer/None ist
        return {}           # Leeres dict zurückgeben (keine EXIF-Daten)
    # --- PYTHON LERNEN: Dict Comprehension ---
    # {ausdruck for variable in iterable} erzeugt ein dict in einer Zeile.
    # TAGS.get(tag, tag) = schau im TAGS-dict nach; falls nicht gefunden, nimm tag selbst.
    return {TAGS.get(tag, tag): value for tag, value in raw.items()}


# --- PYTHON LERNEN: Verschachtelte Funktionen ---
# tuple[Optional[float], Optional[float]] = die Funktion gibt ein Tupel mit zwei floats zurück.
# Tupel: runde Klammern (), unveränderlich, mehrere Werte auf einmal
def _parse_gps(gps_info: dict) -> tuple[Optional[float], Optional[float]]:
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
def extract_metadata(data: bytes) -> dict:
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

    # --- PYTHON LERNEN: dict zurückgeben ---
    # dict mit geschweiften Klammern {} und "Schlüssel": Wert
    return {"lat": lat, "lng": lng, "taken_at": taken_at}
