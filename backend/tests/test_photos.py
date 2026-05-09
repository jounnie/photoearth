"""Tests für /api/photos – Upload, GPS-Update, Album-Zuweisung, Löschen."""
import pytest


def test_list_photos_empty(client):
    resp = client.get("/api/photos/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_upload_photo(client, make_jpeg):
    resp = client.post(
        "/api/photos/upload",
        files=[("files", ("foto.jpg", make_jpeg(), "image/jpeg"))],
    )
    assert resp.status_code == 200
    photos = resp.json()
    assert len(photos) == 1
    photo = photos[0]
    assert photo["original_name"] == "foto.jpg"
    assert photo["gps_type"] == "none"
    assert photo["exif_lat"] is None
    assert photo["location_source"] is None


def test_upload_photo_with_gps(client, make_jpeg):
    resp = client.post(
        "/api/photos/upload",
        files=[("files", ("gps.jpg", make_jpeg(lat=47.37, lng=8.54), "image/jpeg"))],
    )
    photo = resp.json()[0]
    assert photo["gps_type"] == "ok"
    assert photo["exif_lat"] == pytest.approx(47.37, abs=0.01)
    assert photo["exif_lng"] == pytest.approx(8.54, abs=0.01)
    assert photo["location_source"] == "exif"
    assert photo["lat"] == pytest.approx(47.37, abs=0.01)


def test_upload_photo_gps_zero(client, make_jpeg):
    # GPS-Koordinaten (0.0, 0.0) mitten im Atlantik → gps_type "zero" (wahrscheinlich fehlerhaft)
    resp = client.post(
        "/api/photos/upload",
        files=[("files", ("zero.jpg", make_jpeg(lat=0.0, lng=0.0), "image/jpeg"))],
    )
    assert resp.json()[0]["gps_type"] == "zero"


def test_upload_multiple_photos(client, make_jpeg):
    resp = client.post(
        "/api/photos/upload",
        files=[
            ("files", ("a.jpg", make_jpeg(), "image/jpeg")),
            ("files", ("b.jpg", make_jpeg(), "image/jpeg")),
        ],
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_upload_skips_non_images(client, make_jpeg):
    resp = client.post(
        "/api/photos/upload",
        files=[
            ("files", ("doc.txt", b"text content", "text/plain")),
            ("files", ("real.jpg", make_jpeg(), "image/jpeg")),
        ],
    )
    assert len(resp.json()) == 1


def test_upload_no_valid_images_returns_empty_list(client):
    resp = client.post(
        "/api/photos/upload",
        files=[("files", ("doc.pdf", b"pdf content", "application/pdf"))],
    )
    assert resp.status_code == 200
    assert resp.json() == []


def test_upload_assigns_album(client, make_jpeg):
    album = client.post("/api/albums/", json={"name": "Album"}).json()
    resp = client.post(
        "/api/photos/upload",
        files=[("files", ("p.jpg", make_jpeg(), "image/jpeg"))],
        params={"album_id": album["id"]},
    )
    assert resp.json()[0]["album_id"] == album["id"]


def test_list_photos_sorted_newest_first(client, make_jpeg):
    for name in ["a.jpg", "b.jpg"]:
        client.post(
            "/api/photos/upload",
            files=[("files", (name, make_jpeg(), "image/jpeg"))],
        )
    names = [p["original_name"] for p in client.get("/api/photos/").json()]
    assert names == ["b.jpg", "a.jpg"]


def test_list_photos_filter_by_album(client, make_jpeg):
    a1 = client.post("/api/albums/", json={"name": "A1"}).json()
    a2 = client.post("/api/albums/", json={"name": "A2"}).json()
    client.post("/api/photos/upload", files=[("files", ("p1.jpg", make_jpeg(), "image/jpeg"))], params={"album_id": a1["id"]})
    client.post("/api/photos/upload", files=[("files", ("p2.jpg", make_jpeg(), "image/jpeg"))], params={"album_id": a2["id"]})

    resp = client.get("/api/photos/", params={"album_id": a1["id"]})
    assert len(resp.json()) == 1
    assert resp.json()[0]["album_id"] == a1["id"]


def test_get_image(client, make_jpeg):
    photo_id = client.post(
        "/api/photos/upload",
        files=[("files", ("p.jpg", make_jpeg(), "image/jpeg"))],
    ).json()[0]["id"]

    resp = client.get(f"/api/photos/{photo_id}/image")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("image/")


def test_get_image_not_found(client):
    assert client.get("/api/photos/999/image").status_code == 404


def test_update_gps(client, make_jpeg):
    photo_id = client.post(
        "/api/photos/upload",
        files=[("files", ("p.jpg", make_jpeg(), "image/jpeg"))],
    ).json()[0]["id"]

    resp = client.patch(
        f"/api/photos/{photo_id}/gps",
        json={"lat": 48.137, "lng": 11.575, "location_name": "München, Deutschland"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["manual_lat"] == pytest.approx(48.137)
    assert data["manual_lng"] == pytest.approx(11.575)
    assert data["location_name"] == "München, Deutschland"
    assert data["location_source"] == "manual"
    assert data["gps_type"] == "ok"
    assert data["lat"] == pytest.approx(48.137)


def test_update_gps_overrides_exif(client, make_jpeg):
    photo_id = client.post(
        "/api/photos/upload",
        files=[("files", ("p.jpg", make_jpeg(lat=10.0, lng=20.0), "image/jpeg"))],
    ).json()[0]["id"]

    client.patch(f"/api/photos/{photo_id}/gps", json={"lat": 48.0, "lng": 11.0})
    data = client.get("/api/photos/").json()[0]
    assert data["lat"] == pytest.approx(48.0)
    assert data["exif_lat"] == pytest.approx(10.0, abs=0.1)  # EXIF bleibt erhalten


def test_update_gps_not_found(client):
    resp = client.patch("/api/photos/999/gps", json={"lat": 0.0, "lng": 0.0})
    assert resp.status_code == 404


def test_assign_album(client, make_jpeg):
    album_id = client.post("/api/albums/", json={"name": "Album"}).json()["id"]
    photo_id = client.post(
        "/api/photos/upload",
        files=[("files", ("p.jpg", make_jpeg(), "image/jpeg"))],
    ).json()[0]["id"]

    resp = client.patch(f"/api/photos/{photo_id}/album", params={"album_id": album_id})
    assert resp.status_code == 200
    assert resp.json()["album_id"] == album_id


def test_remove_album_assignment(client, make_jpeg):
    album_id = client.post("/api/albums/", json={"name": "Album"}).json()["id"]
    photo_id = client.post(
        "/api/photos/upload",
        files=[("files", ("p.jpg", make_jpeg(), "image/jpeg"))],
        params={"album_id": album_id},
    ).json()[0]["id"]

    # Ohne album_id-Parameter → album_id wird auf None gesetzt
    resp = client.patch(f"/api/photos/{photo_id}/album")
    assert resp.status_code == 200
    assert resp.json()["album_id"] is None


def test_delete_photo(client, make_jpeg):
    photo_id = client.post(
        "/api/photos/upload",
        files=[("files", ("p.jpg", make_jpeg(), "image/jpeg"))],
    ).json()[0]["id"]

    resp = client.delete(f"/api/photos/{photo_id}")
    assert resp.status_code == 204
    assert client.get("/api/photos/").json() == []


def test_delete_photo_not_found(client):
    assert client.delete("/api/photos/999").status_code == 404
