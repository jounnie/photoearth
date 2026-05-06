# PhotoEarth — Konzept

Desktop-App zum Verwalten von Fotos mit Fokus auf Aufnahmeort. Fotos werden lokal gespeichert, GPS-Daten aus EXIF gelesen oder nacherfasst, und auf einer interaktiven Karte angezeigt.

## Kernfunktionen

- **Foto-Import** — lokale Dateien, OneDrive-Ordner (sync), Drag & Drop
- **GPS-Erkennung** — automatisch aus EXIF, manuell per Kartenklick, oder via AI (Claude Vision)
- **Alben** — Fotos in Alben organisieren, Album-CRUD
- **Karte** — alle Fotos mit gültigem GPS auf Leaflet-Karte, gefiltert nach Album/GPS-Typ
- **GPS-Nacherfassung** — für Fotos ohne oder mit ungültigen Koordinaten (0,0)

## GPS-Zustände

| Zustand | Bedeutung |
|---|---|
| `ok` | Gültige EXIF-Koordinaten oder manuell gesetzt |
| `zero` | GPS vorhanden, aber 0.0 / 0.0 (ungültig, Kamerafehler) |
| `none` | Keine GPS-Daten im EXIF |

## AI-Standorterkennung

Claude Vision analysiert das Bild und schätzt den Aufnahmeort anhand von visuellen Hinweisen (Architektur, Landschaft, Schilder, etc.). Funktioniert gut bei Städten und bekannten Sehenswürdigkeiten, weniger zuverlässig bei Innenräumen oder generischen Landschaften. Ergebnis wird als `location_source: "ai"` gespeichert und kann manuell korrigiert werden.

## Stack

| Schicht | Technologie |
|---|---|
| Frontend | React + Vite + TypeScript |
| Karte | Leaflet (react-leaflet) |
| Backend | FastAPI (Python) |
| Datenbank | SQLite via SQLAlchemy |
| EXIF | Pillow + piexif |
| AI | Anthropic SDK (Claude Vision) |
| Packages | uv |
| Packaging | PyInstaller (Backend) + Vite Build |

## Architektur

```
photoearth/
├── backend/
│   └── app/
│       ├── main.py           # FastAPI, CORS, Static-Files
│       ├── models.py         # SQLAlchemy: Album, Photo
│       ├── schemas.py        # Pydantic I/O
│       ├── database.py       # SQLite engine
│       ├── exif_utils.py     # EXIF/GPS parsing
│       └── routers/
│           ├── photos.py     # Upload, GPS-Update, Delete
│           ├── albums.py     # CRUD
│           └── ai.py         # Claude Vision → Standort
├── frontend/
│   └── src/
│       ├── App.tsx
│       └── components/
│           ├── Map.tsx
│           ├── PhotoList.tsx
│           └── AlbumPanel.tsx
└── IDEA.md
```

## API-Endpunkte

```
GET    /api/photos                    # alle Fotos (optional: ?album_id=)
POST   /api/photos/upload             # Fotos hochladen (multipart)
GET    /api/photos/{id}/image         # Bilddatei servieren
PATCH  /api/photos/{id}/gps          # GPS manuell setzen
PATCH  /api/photos/{id}/album        # Album zuweisen
DELETE /api/photos/{id}              # Foto löschen

GET    /api/albums                    # alle Alben
POST   /api/albums                    # Album erstellen
PATCH  /api/albums/{id}              # Album umbenennen
DELETE /api/albums/{id}              # Album löschen

POST   /api/ai/{id}/detect-location  # Claude Vision → GPS + Name
```

## GPS-Priorität

Wenn sowohl EXIF-GPS als auch manuell gesetzte Koordinaten vorhanden sind, haben **manuelle Koordinaten Vorrang** (`manual_lat/lng` überschreibt `exif_lat/lng`). `location_source` zeigt die Herkunft: `exif` | `manual` | `ai`.

## Packaging (Produktion)

1. `vite build` → `frontend/dist/`
2. FastAPI serviert `dist/` als statische Files auf Port 8000
3. PyInstaller bündelt das Backend als `.exe`
4. Nutzer startet `.exe`, öffnet `localhost:8000` im Browser

## Offene Punkte / Nächste Schritte

- [ ] Frontend React-Komponenten implementieren
- [ ] Reverse Geocoding (Koordinaten → Ortsname, z.B. via Nominatim)
- [ ] Foto-Vorschau / Lightbox
- [ ] Bulk-GPS-Erkennung via AI (mehrere Fotos gleichzeitig)
- [ ] Google Photos Import via Takeout-ZIP
- [ ] Karten-Filter nach Album, Datum, GPS-Typ
