# --- PYTHON LERNEN: FastAPI ---
# FastAPI ist ein Web-Framework für Python – es empfängt HTTP-Anfragen und sendet Antworten.
# "from X import Y" importiert nur Y aus dem Modul X (spart Speicher).
import base64
import logging
import os
import secrets
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # Middleware = läuft bei jeder Anfrage
from fastapi.staticfiles import StaticFiles         # Für HTML/JS/CSS-Dateien
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Relativer Import: "." = das aktuelle Paket (app/)
from .database import engine, Base
from .routers import photos, albums, ai

# --- PYTHON LERNEN: Funktionsaufruf auf Modulebene ---
# Dieser Code läuft einmal beim Starten. Er erstellt alle Tabellen in der Datenbank,
# falls sie noch nicht existieren (liest die Klassen aus models.py).
Base.metadata.create_all(bind=engine)

app = FastAPI(title="PhotoEarth API")


# --- PYTHON LERNEN: Middleware-Klasse ---
# Middleware läuft bei JEDER Anfrage, bevor sie die Route erreicht.
# BaseHTTPMiddleware ist die Basisklasse von Starlette (das Framework unter FastAPI).
class _BasicAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Wenn PHOTOEARTH_PASSWORD nicht gesetzt ist → Auth deaktiviert (lokal)
        password = os.environ.get("PHOTOEARTH_PASSWORD", "")
        if not password:
            return await call_next(request)

        auth = request.headers.get("Authorization", "")
        if auth.startswith("Basic "):
            try:
                # base64-dekodieren: "dXNlcjpwYXNz" → "user:pass"
                decoded = base64.b64decode(auth[6:]).decode()
                username, _, pwd = decoded.partition(":")
                expected_user = os.environ.get("PHOTOEARTH_USER", "admin")
                # secrets.compare_digest verhindert Timing-Angriffe
                if (secrets.compare_digest(username, expected_user) and
                        secrets.compare_digest(pwd, password)):
                    return await call_next(request)
            except Exception:
                pass

        # WWW-Authenticate: Basic → Browser zeigt Login-Dialog
        return Response(
            "Unauthorized",
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="PhotoEarth"'},
        )


app.add_middleware(_BasicAuthMiddleware)


# --- PYTHON LERNEN: Logging ---
# logging ist das eingebaute Python-Modul für strukturierte Log-Ausgaben.
# getLogger(__name__) erzeugt einen Logger mit dem Namen des aktuellen Moduls.
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    # Format: Zeitstempel + Level + Nachricht
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class _RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        # Extract username from Basic Auth header for the audit trail.
        # Falls back to "-" when auth is disabled (local dev).
        user = "-"
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Basic "):
            try:
                decoded = base64.b64decode(auth[6:]).decode()
                user = decoded.partition(":")[0] or "-"
            except Exception:
                pass

        # Include query string when present (e.g. ?album_id=3 shows what was filtered)
        path = request.url.path
        if request.url.query:
            path = f"{path}?{request.url.query}"

        logger.info(
            "%s %s %s user=%s %.0fms",
            request.method,
            path,
            response.status_code,
            user,
            duration_ms,
        )
        return response


app.add_middleware(_RequestLogMiddleware)

# --- PYTHON LERNEN: Methoden aufrufen ---
# app.add_middleware() ist eine Methode des app-Objekts.
# CORS = Cross-Origin Resource Sharing: erlaubt dem Browser, Anfragen an eine andere URL zu senden.
# Ohne CORS würde der Browser die Anfragen vom Frontend blockieren.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_methods=["*"],   # "*" = alle HTTP-Methoden erlaubt (GET, POST, ...)
    allow_headers=["*"],
)

# --- PYTHON LERNEN: Router einbinden ---
# Router gruppieren zusammengehörige Endpunkte (z.B. alle /photos/... Routen).
# prefix="/api" hängt "/api" vor alle Routen des Routers.
app.include_router(photos.router, prefix="/api")
app.include_router(albums.router, prefix="/api")
app.include_router(ai.router, prefix="/api")

# --- PYTHON LERNEN: os.path für Dateipfade ---
# os.path.join() verbindet Pfadteile plattformunabhängig (/ auf Linux, \ auf Windows).
# __file__ ist eine eingebaute Variable: der Pfad der aktuellen Python-Datei.
# ".." geht eine Verzeichnisebene nach oben.
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")

# --- PYTHON LERNEN: if-Bedingung ---
# os.path.exists() gibt True zurück wenn der Pfad existiert, sonst False.
if os.path.exists(frontend_dist):
    # Im Produktionsbetrieb: die fertig gebaute React-App ausliefern
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")
