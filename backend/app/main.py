# --- PYTHON LERNEN: FastAPI ---
# FastAPI ist ein Web-Framework für Python – es empfängt HTTP-Anfragen und sendet Antworten.
# "from X import Y" importiert nur Y aus dem Modul X (spart Speicher).
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # Middleware = läuft bei jeder Anfrage
from fastapi.staticfiles import StaticFiles         # Für HTML/JS/CSS-Dateien

# --- PYTHON LERNEN: Standardbibliothek ---
# "os" ist immer dabei (eingebaut in Python). Kein pip install nötig.
import os

# Relativer Import: "." = das aktuelle Paket (app/)
from .database import engine, Base
from .routers import photos, albums, ai

# --- PYTHON LERNEN: Funktionsaufruf auf Modulebene ---
# Dieser Code läuft einmal beim Starten. Er erstellt alle Tabellen in der Datenbank,
# falls sie noch nicht existieren (liest die Klassen aus models.py).
Base.metadata.create_all(bind=engine)

# --- PYTHON LERNEN: Objekte erstellen (Instanzen) ---
# FastAPI() ruft den Konstruktor auf und erzeugt ein Objekt.
# Das Objekt heißt "app" – FastAPI/uvicorn sucht nach diesem Namen.
app = FastAPI(title="PhotoEarth API")

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
