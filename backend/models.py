from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text 
from .db import Base

class QR(Base):
    __tablename__ = "qrcodes"
    
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(16), unique=True, index=True, nullable=False)
    title = Column(String(200), nullable=False)
    target_url = Column(Text, nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    scans_count = Column(Integer, default=0)
    
