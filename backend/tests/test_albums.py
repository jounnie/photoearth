"""Tests für /api/albums – CRUD und Foto-Zählung."""


def test_list_albums_empty(client):
    resp = client.get("/api/albums/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_album(client):
    resp = client.post("/api/albums/", json={"name": "Urlaub 2024", "description": "Sommer"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Urlaub 2024"
    assert data["description"] == "Sommer"
    assert data["photo_count"] == 0
    assert "id" in data
    assert "created_at" in data


def test_create_album_default_description(client):
    resp = client.post("/api/albums/", json={"name": "Minimal"})
    assert resp.status_code == 201
    assert resp.json()["description"] == ""


def test_list_albums_sorted_newest_first(client):
    client.post("/api/albums/", json={"name": "Erst"})
    client.post("/api/albums/", json={"name": "Dann"})
    names = [a["name"] for a in client.get("/api/albums/").json()]
    assert names == ["Dann", "Erst"]


def test_list_albums_includes_photo_count(client, make_jpeg):
    album = client.post("/api/albums/", json={"name": "Mit Fotos"}).json()
    # Zwei Fotos hochladen und dem Album zuweisen
    for _ in range(2):
        client.post(
            "/api/photos/upload",
            files=[("files", ("p.jpg", make_jpeg(), "image/jpeg"))],
            params={"album_id": album["id"]},
        )
    resp = client.get("/api/albums/")
    assert resp.json()[0]["photo_count"] == 2


def test_update_album_name(client):
    album = client.post("/api/albums/", json={"name": "Alt"}).json()
    resp = client.patch(f"/api/albums/{album['id']}", json={"name": "Neu"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Neu"


def test_update_album_partial_keeps_other_fields(client):
    album = client.post("/api/albums/", json={"name": "X", "description": "Y"}).json()
    resp = client.patch(f"/api/albums/{album['id']}", json={"description": "Z"})
    assert resp.json()["name"] == "X"
    assert resp.json()["description"] == "Z"


def test_update_album_not_found(client):
    resp = client.patch("/api/albums/999", json={"name": "X"})
    assert resp.status_code == 404


def test_delete_album(client):
    album = client.post("/api/albums/", json={"name": "Löschen"}).json()
    resp = client.delete(f"/api/albums/{album['id']}")
    assert resp.status_code == 204
    assert client.get("/api/albums/").json() == []


def test_delete_album_not_found(client):
    resp = client.delete("/api/albums/999")
    assert resp.status_code == 404


def test_delete_album_cascades_photos(client, make_jpeg):
    album = client.post("/api/albums/", json={"name": "Cascade"}).json()
    client.post(
        "/api/photos/upload",
        files=[("files", ("p.jpg", make_jpeg(), "image/jpeg"))],
        params={"album_id": album["id"]},
    )
    client.delete(f"/api/albums/{album['id']}")
    # Album gelöscht → Foto muss ebenfalls weg sein
    assert client.get("/api/photos/").json() == []
