from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from datetime import datetime
from typing import Optional
import io


def _get_exif(image: Image.Image) -> dict:
    raw = image._getexif()
    if not raw:
        return {}
    return {TAGS.get(tag, tag): value for tag, value in raw.items()}


def _parse_gps(gps_info: dict) -> tuple[Optional[float], Optional[float]]:
    def to_decimal(values, ref):
        d, m, s = values
        decimal = float(d) + float(m) / 60 + float(s) / 3600
        if ref in ("S", "W"):
            decimal = -decimal
        return decimal

    try:
        gps = {GPSTAGS.get(k, k): v for k, v in gps_info.items()}
        lat = to_decimal(gps["GPSLatitude"], gps["GPSLatitudeRef"])
        lng = to_decimal(gps["GPSLongitude"], gps["GPSLongitudeRef"])
        return lat, lng
    except (KeyError, TypeError, ZeroDivisionError):
        return None, None


def extract_metadata(data: bytes) -> dict:
    image = Image.open(io.BytesIO(data))
    exif = _get_exif(image)

    lat, lng = None, None
    if "GPSInfo" in exif:
        lat, lng = _parse_gps(exif["GPSInfo"])

    taken_at = None
    for tag in ("DateTimeOriginal", "DateTime"):
        if tag in exif:
            try:
                taken_at = datetime.strptime(exif[tag], "%Y:%m:%d %H:%M:%S")
            except ValueError:
                pass
            break

    return {"lat": lat, "lng": lng, "taken_at": taken_at}
