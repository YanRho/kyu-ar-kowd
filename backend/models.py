from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from .db import Base


# QR Code model for storing the QR code metdata
class QR(Base):
    __tablename__ = "qrcodes"
    
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(16), unique=True, index=True, nullable=False)
    title = Column(String(200), nullable=False)
    target_url = Column(Text, nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    scans_count = Column(Integer, default=0)
    
# Scan Event model for tracking QR code scans
class ScanEvent(Base):
    __tablename__ = "scanevents"
    
    id = Column(Integer, primary_key=True, index=True)
    qr_id = Column(Integer, ForeignKey("qrcodes.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.now(timezone.utc))
    referrer = Column(String(500), nullable=True)
    user_agent = Column(String(500), nullable=True)
    ip = Column(String(100), nullable=True)
    
    qr = relationship("QR", back_populates="scans")
    
QR.scans = relationship("ScanEvent", back_populates="qr", cascade="all, delete-orphan")
