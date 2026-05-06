"""
Tests für /api/ai – KI-Standorterkennung.

Der Anthropic-API-Client wird mit unittest.mock gemockt, damit keine echten
API-Aufrufe gemacht werden (spart Kosten und macht Tests deterministisch).
"""
import json
from unittest.mock import MagicMock, patch

import pytest


def _mock_ai_response(payload: dict) -> MagicMock:
    """Erstellt ein gefaktes anthropic-Response-Objekt."""
    msg = MagicMock()
    msg.content = [MagicMock(text=json.dumps(payload))]
    return msg


def _upload_photo(client, make_jpeg) -> dict:
    return client.post(
        "/api/photos/upload",
        files=[("files", ("p.jpg", make_jpeg(), "image/jpeg"))],
    ).json()[0]


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_detect_location_success(client, make_jpeg):
    photo = _upload_photo(client, make_jpeg)
    response = _mock_ai_response({
        "lat": 47.37,
        "lng": 8.54,
        "location_name": "Zürich, Schweiz",
        "confidence": "high",
        "reasoning": "Sichtbare Landmarken",
    })

    with patch("app.routers.ai.client") as mock_client:
        mock_client.messages.create.return_value = response
        resp = client.post(f"/api/ai/{photo['id']}/detect-location")

    assert resp.status_code == 200
    data = resp.json()
    assert data["location_source"] == "ai"
    assert data["manual_lat"] == pytest.approx(47.37)
    assert data["manual_lng"] == pytest.approx(8.54)
    assert data["location_name"] == "Zürich, Schweiz"


def test_detect_location_updates_gps_type(client, make_jpeg):
    photo = _upload_photo(client, make_jpeg)
    assert photo["gps_type"] == "none"

    response = _mock_ai_response({"lat": 48.2, "lng": 16.37, "location_name": "Wien", "confidence": "medium", "reasoning": "..."})
    with patch("app.routers.ai.client") as mock_client:
        mock_client.messages.create.return_value = response
        data = client.post(f"/api/ai/{photo['id']}/detect-location").json()

    assert data["gps_type"] == "ok"


def test_detect_location_null_coordinates_returns_422(client, make_jpeg):
    photo = _upload_photo(client, make_jpeg)
    response = _mock_ai_response({"lat": None, "lng": None, "location_name": "Unbekannt", "confidence": "low", "reasoning": "Nicht erkennbar"})

    with patch("app.routers.ai.client") as mock_client:
        mock_client.messages.create.return_value = response
        resp = client.post(f"/api/ai/{photo['id']}/detect-location")

    assert resp.status_code == 422


def test_detect_location_invalid_json_returns_500(client, make_jpeg):
    photo = _upload_photo(client, make_jpeg)
    msg = MagicMock()
    msg.content = [MagicMock(text="kein gültiges JSON")]

    with patch("app.routers.ai.client") as mock_client:
        mock_client.messages.create.return_value = msg
        resp = client.post(f"/api/ai/{photo['id']}/detect-location")

    assert resp.status_code == 500


def test_detect_location_photo_not_found(client):
    resp = client.post("/api/ai/999/detect-location")
    assert resp.status_code == 404
