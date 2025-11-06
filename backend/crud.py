from sqlalchemy.orm import Session
from .models import QR, ScanEvent
from .utils import gen_slug
from typing import List
from datetime import datetime, timezone


# Create a new QR code record
def create_qr(db: Session, title: str, target_url: str, note: str | None = None) -> QR:
    slug = gen_slug()
    # ensure uniqueness 
    while db.query(QR).filter_by(slug=slug).first() is not None: 
        slug = gen_slug()
    q = QR(slug=slug, title=title, target_url=target_url, note=note)
    db.add(q)
    db.commit()
    db.refresh(q)
    return q

# List QR codes with optional limit
def list_qrs(db: Session, limit: int = 100) -> List[QR]:
    return db.query(QR).order_by(QR.created_at.desc()).limit(limit).all()

# Get a QR code by its slug
def get_qr_by_slug(db: Session, slug: str) -> QR | None:
    return db.query(QR).filter_by(slug=slug).first()

# Record a scan event for a given QR code
def record_scan(db: Session, qr: QR, referrer: str | None, user_agent: str | None, ip: str | None):
    ev = ScanEvent(qr_id=qr.id, timestamp=datetime.now(timezone.utc), referrer=referrer, user_agent=user_agent, ip=ip)
    qr.scans_count += 1
    db.add(ev)
    db.add(qr)
    db.commit()
    db.refresh(qr)
    return ev