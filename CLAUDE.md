# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Backend (run from `backend/`)
```bash
uv sync --group dev                              # Install all dependencies incl. dev
uv run uvicorn app.main:app --reload             # Start dev server on :8000
uv run pytest tests/ -v --tb=short --cov=app     # Run all tests with coverage
uv run pytest tests/test_photos.py::test_upload_photo -v  # Run a single test
```
CI requires `--cov-fail-under=75`; currently at ~97%.

### Frontend (run from `frontend/`)
```bash
npm run dev      # Start Vite dev server on :5173
npm run build    # Type-check + build to frontend/dist/
npm run lint     # ESLint
```

### Combined (Windows)
```
dev.bat          # Opens both servers in separate terminal windows
```

## Architecture

PhotoEarth is a local-first photo manager focused on GPS data. The FastAPI backend serves both the REST API and the production frontend bundle (React/Vite) as static files — so in production there is only one process at `:8000`.

### Request flow
```
Browser → Vite proxy /api/* → FastAPI (port 8000)
       → direct :5173       → FastAPI via CORS (dev only)
```

### Backend (`backend/app/`)
- **`main.py`** — mounts three routers (`/api/photos`, `/api/albums`, `/api/ai`) and serves `frontend/dist/` as static files; `Base.metadata.create_all()` runs at startup
- **`models.py`** — `Album` and `Photo` SQLAlchemy models; `Photo` has computed properties `lat`/`lng` (manual overrides EXIF) and `gps_type` (`"ok"` / `"zero"` / `"none"`)
- **`schemas.py`** — Pydantic I/O models; `LocationSource = Literal["exif", "manual", "ai"]` enforces valid values at the API boundary
- **`exif_utils.py`** — Pillow-based EXIF extraction; returns typed `ExifMetadata(TypedDict)`; uses public `image.getexif()` + `get_ifd()` API
- **`routers/photos.py`** — async upload (aiofiles), `_process_upload()` helper isolates per-file logic from DB operations
- **`routers/ai.py`** — calls Claude Opus 4.7 with base64 image; `_load_image_as_base64()` isolates file I/O; `LocationResult` Pydantic model parses the JSON response
- **`routers/albums.py`** — CRUD + photo count via a separate `GROUP BY` query; uses `model_copy(update=...)` to set `photo_count` without post-construction mutation

### Frontend (`frontend/src/`)
- `App.tsx` — top-level state (selected album, photo list, map/list toggle)
- `api/client.ts` — all Axios calls, baseURL `/api`
- Map view uses Leaflet/react-leaflet; data fetched with TanStack React Query

### GPS priority
`photo.lat` / `photo.lng` → `manual_lat/lng` if set, else `exif_lat/lng`. `gps_type` is computed, not stored.

## Testing
- Tests use an in-memory SQLite with `StaticPool` (all connections share one DB instance — required for isolation)
- `conftest.py` provides: `client` (FastAPI TestClient + DB override + `tmp_path` upload dir), `make_jpeg()` factory (creates minimal JPEGs with optional GPS EXIF via piexif)
- AI tests mock `app.routers.ai.client` with `unittest.mock.patch` — no real API calls
- `tests/helpers.py` contains `to_dms()` for converting decimal degrees to EXIF rational format, shared by `conftest.py` and `test_exif_utils.py`
