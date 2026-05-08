"""Tests für app/exif_utils – GPS-Extraktion und Datum-Parsing."""
import io
from datetime import datetime

import piexif
import pytest
from PIL import Image

from app.exif_utils import extract_metadata
from tests.helpers import to_dms  # geteilte Hilfsfunktion, kein Duplikat


# ── Lokale Hilfsfunktionen ────────────────────────────────────────────────────

def _jpeg_no_exif() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (50, 50)).save(buf, format="JPEG")
    return buf.getvalue()


def _jpeg_with_gps(lat: float, lng: float) -> bytes:
    gps_ifd = {
        piexif.GPSIFD.GPSLatitudeRef: b"N" if lat >= 0 else b"S",
        piexif.GPSIFD.GPSLatitude: to_dms(lat),
        piexif.GPSIFD.GPSLongitudeRef: b"E" if lng >= 0 else b"W",
        piexif.GPSIFD.GPSLongitude: to_dms(lng),
    }
    exif_bytes = piexif.dump({"GPS": gps_ifd})
    buf = io.BytesIO()
    Image.new("RGB", (50, 50)).save(buf, format="JPEG", exif=exif_bytes)
    return buf.getvalue()


def _jpeg_with_datetime(dt_str: str) -> bytes:
    exif_bytes = piexif.dump({"Exif": {piexif.ExifIFD.DateTimeOriginal: dt_str.encode()}})
    buf = io.BytesIO()
    Image.new("RGB", (50, 50)).save(buf, format="JPEG", exif=exif_bytes)
    return buf.getvalue()


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_no_exif_returns_none():
    meta = extract_metadata(_jpeg_no_exif())
    assert meta["lat"] is None
    assert meta["lng"] is None
    assert meta["taken_at"] is None


def test_gps_north_east():
    meta = extract_metadata(_jpeg_with_gps(47.37, 8.54))
    assert meta["lat"] == pytest.approx(47.37, abs=0.01)
    assert meta["lng"] == pytest.approx(8.54, abs=0.01)


def test_gps_south_west():
    # Santiago de Chile – beide Koordinaten negativ
    meta = extract_metadata(_jpeg_with_gps(-33.45, -70.66))
    assert meta["lat"] == pytest.approx(-33.45, abs=0.01)
    assert meta["lng"] == pytest.approx(-70.66, abs=0.01)


def test_datetime_original_parsed():
    meta = extract_metadata(_jpeg_with_datetime("2024:06:15 08:30:00"))
    assert meta["taken_at"] == datetime(2024, 6, 15, 8, 30, 0)


def test_invalid_datetime_returns_none():
    # Korruptes Datumsformat → kein Absturz, einfach None
    meta = extract_metadata(_jpeg_with_datetime("not-a-date"))
    assert meta["taken_at"] is None
