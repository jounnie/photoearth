from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from .database import engine, Base
from .routers import photos, albums, ai

Base.metadata.create_all(bind=engine)

app = FastAPI(title="PhotoEarth API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(photos.router, prefix="/api")
app.include_router(albums.router, prefix="/api")
app.include_router(ai.router, prefix="/api")

# In production: serve React build
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")
