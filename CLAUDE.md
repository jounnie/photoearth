# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Combined (Windows)
```
dev.bat          # Opens both servers in separate terminal windows
```

Per-stack commands, architecture, and testing notes live in each subdirectory's own CLAUDE.md, loaded automatically when working there: `backend/CLAUDE.md` (FastAPI/Python), `backend-java/CLAUDE.md` (Spring Boot port — must match the FastAPI API contract), `frontend/CLAUDE.md` (React/Vite).

## Architecture

PhotoEarth is a local-first photo manager focused on GPS data. The backend (either `backend/` or `backend-java/` — they implement the same API) serves both the REST API and the production frontend bundle (React/Vite) as static files — so in production there is only one process at `:8000`.

### Request flow
```
Browser → Vite proxy /api/* → backend (port 8000)
       → direct :5173       → backend via CORS (dev only)
```

### GPS priority
`photo.lat` / `photo.lng` → `manual_lat/lng` if set, else `exif_lat/lng`. `gps_type` is computed, not stored.
