from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .database import Base


class Album(Base):
    __tablename__ = "albums"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    photos = relationship("Photo", back_populates="album", cascade="all, delete-orphan")


class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_name = Column(String, nullable=False)
    album_id = Column(Integer, ForeignKey("albums.id"), nullable=True)

    # GPS aus EXIF
    exif_lat = Column(Float, nullable=True)
    exif_lng = Column(Float, nullable=True)

    # Manuell gesetzt oder via AI
    manual_lat = Column(Float, nullable=True)
    manual_lng = Column(Float, nullable=True)
    location_name = Column(String, nullable=True)   # z.B. "Zürich, Schweiz"
    location_source = Column(String, nullable=True)  # "exif" | "manual" | "ai"

    taken_at = Column(DateTime, nullable=True)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    album = relationship("Album", back_populates="photos")

    @property
    def lat(self):
        return self.manual_lat if self.manual_lat is not None else self.exif_lat

    @property
    def lng(self):
        return self.manual_lng if self.manual_lng is not None else self.exif_lng

    @property
    def gps_type(self):
        lat, lng = self.lat, self.lng
        if lat is None:
            return "none"
        if lat == 0.0 and lng == 0.0:
            return "zero"
        return "ok"
