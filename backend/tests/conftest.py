"""
Gemeinsame Fixtures für alle Tests.

conftest.py wird von pytest automatisch eingelesen – alle hier definierten
Fixtures stehen in jedem Test-File zur Verfügung ohne expliziten Import.
"""
import io

import piexif
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from tests.helpers import to_dms


@pytest.fixture
def db_engine():
    """In-Memory SQLite-Datenbank, wird nach jedem Test komplett geleert."""
    # StaticPool: alle DB-Verbindungen teilen dieselbe In-Memory-Instanz.
    # Ohne StaticPool bekommt jede Verbindung eine leere neue Datenbank.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """Einzelne Datenbank-Sitzung pro Test."""
    Session = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session, tmp_path, monkeypatch):
    """
    FastAPI-TestClient mit:
    - isolierter In-Memory-Datenbank (kein echtes photoearth.db)
    - temporärem Upload-Verzeichnis (kein Schreiben in app/uploads/)
    """
    monkeypatch.setattr("app.routers.photos.UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr("app.routers.ai.UPLOAD_DIR", str(tmp_path))

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def make_jpeg():
    """
    Factory-Fixture: gibt eine Funktion zurück, die ein minimales JPEG erzeugt.

    Verwendung im Test:
        def test_foo(make_jpeg):
            data = make_jpeg()                   # ohne GPS
            data = make_jpeg(lat=47.3, lng=8.5)  # mit GPS
    """
    def _make(lat: float | None = None, lng: float | None = None) -> bytes:
        img = Image.new("RGB", (50, 50), color=(100, 150, 200))

        if lat is not None and lng is not None:
            gps_ifd = {
                piexif.GPSIFD.GPSLatitudeRef: b"N" if lat >= 0 else b"S",
                piexif.GPSIFD.GPSLatitude: to_dms(lat),
                piexif.GPSIFD.GPSLongitudeRef: b"E" if lng >= 0 else b"W",
                piexif.GPSIFD.GPSLongitude: to_dms(lng),
            }
            exif_bytes = piexif.dump({"GPS": gps_ifd})
            buf = io.BytesIO()
            img.save(buf, format="JPEG", exif=exif_bytes)
        else:
            buf = io.BytesIO()
            img.save(buf, format="JPEG")

        return buf.getvalue()

    return _make
