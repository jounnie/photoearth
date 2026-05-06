from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import anthropic
import base64
import os

from ..database import get_db
from ..models import Photo
from ..schemas import PhotoOut

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")

router = APIRouter(prefix="/ai", tags=["ai"])

client = anthropic.Anthropic()


class LocationResult(BaseModel):
    lat: float
    lng: float
    location_name: str
    confidence: str   # "high" | "medium" | "low"
    reasoning: str


@router.post("/{photo_id}/detect-location", response_model=PhotoOut)
def detect_location(photo_id: int, db: Session = Depends(get_db)):
    photo = db.get(Photo, photo_id)
    if not photo:
        raise HTTPException(404, "Photo not found")

    path = os.path.join(UPLOAD_DIR, photo.filename)
    if not os.path.exists(path):
        raise HTTPException(404, "Image file not found")

    with open(path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode()

    ext = os.path.splitext(photo.filename)[1].lower()
    media_type = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".webp": "image/webp", ".gif": "image/gif",
    }.get(ext, "image/jpeg")

    message = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": image_data},
                },
                {
                    "type": "text",
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

    import json
    try:
        result = json.loads(message.content[0].text)
        if result.get("lat") is None or result.get("lng") is None:
            raise HTTPException(422, "Could not determine location from image")

        photo.manual_lat = float(result["lat"])
        photo.manual_lng = float(result["lng"])
        photo.location_name = result.get("location_name")
        photo.location_source = "ai"
        db.commit()
        db.refresh(photo)
        return photo
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        raise HTTPException(500, f"Failed to parse AI response: {e}")
