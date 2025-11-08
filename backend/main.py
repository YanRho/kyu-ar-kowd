from fastapi import FastAPI, Query, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse, PlainTextResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, AnyUrl
from urllib.parse import unquote
from io import BytesIO
from PIL import ImageColor
import segno
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.colormasks import (
    RadialGradiantColorMask,
    SquareGradiantColorMask,
    HorizontalGradiantColorMask,
    VerticalGradiantColorMask,
)

from backend.db import Base, engine, get_db
from backend.models import QR
from backend import crud
from backend.utils import mask_ip

# --- Initialize ---
Base.metadata.create_all(bind=engine)
app = FastAPI(title="Kyu-Ar-API")

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Root ---
@app.get("/")
def read_root():
    return {"message": "Welcome to Kyu-Ar-API"}


# --- QR Generator (supports gradients, no eye color) ---
def qr_bytes(
    data: str,
    kind: str = "png",
    scale: int = 8,
    border: int = 2,
    fg1: str = "#000000",
    fg2: str = "#000000",
    bg: str = "#ffffff",
    gradient: bool = False,
    direction: str = "horizontal",
):
    """Generate QR code image bytes with optional gradients."""
    if not data or data.strip() == "":
        raise HTTPException(status_code=400, detail="Missing 'data' to encode")

    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(unquote(data))
    qr.make(fit=True)

    if kind == "png":
        if gradient:
            # Apply gradient mask based on direction
            if direction == "horizontal":
                mask = HorizontalGradiantColorMask(
                    back_color=ImageColor.getrgb(bg),
                    left_color=ImageColor.getrgb(fg1),
                    right_color=ImageColor.getrgb(fg2),
                )
            elif direction == "vertical":
                mask = VerticalGradiantColorMask(
                    back_color=ImageColor.getrgb(bg),
                    top_color=ImageColor.getrgb(fg1),
                    bottom_color=ImageColor.getrgb(fg2),
                )
            elif direction == "radial":
                mask = RadialGradiantColorMask(
                    back_color=ImageColor.getrgb(bg),
                    center_color=ImageColor.getrgb(fg1),
                    edge_color=ImageColor.getrgb(fg2),
                )
            elif direction == "square":
                mask = SquareGradiantColorMask(
                    back_color=ImageColor.getrgb(bg),
                    center_color=ImageColor.getrgb(fg1),
                    edge_color=ImageColor.getrgb(fg2),
                )
            else:
                mask = HorizontalGradiantColorMask(
                    back_color=ImageColor.getrgb(bg),
                    left_color=ImageColor.getrgb(fg1),
                    right_color=ImageColor.getrgb(fg2),
                )

            img = qr.make_image(image_factory=StyledPilImage, color_mask=mask)
        else:
            img = qr.make_image(fill_color=fg1, back_color=bg)

        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf

    elif kind == "svg":
        qr_seg = segno.make(data, micro=False)
        buf = BytesIO()
        qr_seg.save(buf, kind="svg", scale=scale, border=border, dark=fg1, light=bg)
        buf.seek(0)
        return buf
    else:
        raise HTTPException(status_code=400, detail="Unsupported format.")


# --- QR endpoints ---
@app.get("/qr.png")
def qr_png(
    data: str = Query(..., description="Data to encode"),
    fg1: str = Query("#000000"),
    fg2: str = Query("#000000"),
    bg: str = Query("#ffffff"),
    gradient: bool = Query(False),
    direction: str = Query("horizontal"),
):
    buf = qr_bytes(data, kind="png", fg1=fg1, fg2=fg2, bg=bg, gradient=gradient, direction=direction)
    return StreamingResponse(buf, media_type="image/png")


@app.get("/qr.svg")
def qr_svg(
    data: str = Query(..., description="Data to encode"),
):
    buf = qr_bytes(data, kind="svg")
    return StreamingResponse(buf, media_type="image/svg+xml")


@app.get("/qr/echo", response_class=PlainTextResponse)
def qr_echo(data: str):
    return unquote(data)


# --- Database-backed QR Management APIs ---
class QRIn(BaseModel):
    title: str
    target_url: AnyUrl
    note: str | None = None


class QROut(BaseModel):
    id: int
    slug: str
    title: str
    target_url: str
    note: str | None = None
    created_at: str
    scans_count: int

    @staticmethod
    def from_model(m: QR):
        return QROut(
            id=m.id,
            slug=m.slug,
            title=m.title,
            target_url=m.target_url,
            note=m.note,
            created_at=m.created_at.isoformat(),
            scans_count=m.scans_count,
        )


# Create new QR record
@app.post("/api/qr", response_model=QROut)
def api_create_qr(payload: QRIn, db=Depends(get_db)):
    q = crud.create_qr(db, title=payload.title, target_url=str(payload.target_url), note=payload.note)
    return QROut.from_model(q)


# List QR records
@app.get("/api/qrs", response_model=list[QROut])
def api_list_qr(db=Depends(get_db)):
    items = crud.list_qrs(db)
    return [QROut.from_model(x) for x in items]


# Get QR by slug
@app.get("/api/qr/{slug}", response_model=QROut)
def api_get_qr(slug: str, db=Depends(get_db)):
    q = crud.get_qr_by_slug(db, slug)
    if not q:
        raise HTTPException(404, "QR code not found")
    return QROut.from_model(q)


# Redirect and log scans
@app.get("/r/{slug}")
def redirect_to_target(slug: str, request: Request, db=Depends(get_db)):
    q = crud.get_qr_by_slug(db, slug)
    if not q:
        raise HTTPException(404, "QR not found")

    ref = request.headers.get("referer")
    ua = request.headers.get("user-agent")
    ip = request.client.host if request.client else None
    crud.record_scan(db, q, ref, ua, mask_ip(ip))

    return RedirectResponse(q.target_url, status_code=302)


# QR stats
@app.get("/api/qr/{slug}/stats")
def stats(slug: str, db=Depends(get_db)):
    q = crud.get_qr_by_slug(db, slug)
    if not q:
        raise HTTPException(404, "Not found")

    return {
        "slug": q.slug,
        "title": q.title,
        "scans_count": q.scans_count,
        "created_at": q.created_at.isoformat(),
        "recent": [
            {
                "ts": s.timestamp.isoformat(),
                "referrer": s.referrer,
                "user_agent": s.user_agent,
                "ip": s.ip,
            }
            for s in sorted(q.scans, key=lambda s: s.timestamp, reverse=True)[:50]
        ],
    }
