from sqlalchemy.orm import Session
from .models import QR, ScanEvent
from .utils import gen_slug
from typing import List
from datetime import datetime, timezone


def create_qr(
    db: Session,
    title: str,
    target_url: str | None = None,
    note: str | None = None,
    type: str = "URL",
    data: dict | None = None,
) -> QR:
    slug = gen_slug(title)

    # ensure uniqueness
    base_slug = slug
    i = 2
    while db.query(QR).filter_by(slug=slug).first() is not None:
        slug = f"{base_slug}-{i}"
        i += 1

    q = QR(
        slug=slug,
        title=title,
        type=type,
        target_url=target_url,
        data=data,
        note=note,
        created_at=datetime.now(timezone.utc),
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return q



def list_qrs(db: Session, limit: int = 100) -> List[QR]:
    """Return the most recent QR records."""
    return db.query(QR).order_by(QR.created_at.desc()).limit(limit).all()


def get_qr_by_slug(db: Session, slug: str) -> QR | None:
    """Retrieve a QR record by its slug."""
    return db.query(QR).filter_by(slug=slug).first()


def record_scan(db: Session, qr: QR, referrer: str | None, user_agent: str | None, ip: str | None):
    """Log a scan event and increment QR's scan counter."""
    ev = ScanEvent(
        qr_id=qr.id,
        timestamp=datetime.now(timezone.utc),
        referrer=referrer,
        user_agent=user_agent,
        ip=ip,
    )
    qr.scans_count += 1
    db.add(ev)
    db.add(qr)
    db.commit()
    db.refresh(qr)
    return ev
