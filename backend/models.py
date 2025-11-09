from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from .db import Base


# QR Code model for storing the QR code metadata
class QR(Base):
    __tablename__ = "qrs"

    id = Column(Integer, primary_key=True)
    slug = Column(String, unique=True, index=True)
    title = Column(String)
    type = Column(String, default="URL")
    target_url = Column(String)
    data = Column(JSON, nullable=True)  # store extra metadata like wifi, contact info
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    scans_count = Column(Integer, default=0)

    # Relationship to scans
    scans = relationship("ScanEvent", back_populates="qr", cascade="all, delete-orphan")


# Scan Event model for tracking QR code scans
class ScanEvent(Base):
    __tablename__ = "scanevents"

    id = Column(Integer, primary_key=True, index=True)
    qr_id = Column(Integer, ForeignKey("qrs.id", ondelete="CASCADE"), nullable=False)  # ✅ fixed here
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    referrer = Column(String(500), nullable=True)
    user_agent = Column(String(500), nullable=True)
    ip = Column(String(100), nullable=True)

    # Relationship back to QR
    qr = relationship("QR", back_populates="scans")
