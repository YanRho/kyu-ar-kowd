from fastapi import FastAPI, Query, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse, PlainTextResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, AnyUrl
from typing import Optional, Dict, Any
from urllib.parse import unquote
from io import BytesIO

import os
import segno
from PIL import Image, ImageDraw, ImageColor

from backend.db import Base, engine, get_db
from backend.models import QR
from backend import crud
from backend.utils import mask_ip

# --- Initialize ---
Base.metadata.create_all(bind=engine)
app = FastAPI(title="Kyu-AR-API")

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Root endpoint ---
@app.get("/")
def read_root():
    return {"message": "Welcome to Kyu-AR-API"}


# ======================
# 🎨 QR GENERATION LOGIC
# ======================

def qr_bytes(
    data: str,
    kind: str = "png",
    scale: int = 8,
    border: int = 2,
    dark_color: str = "black",
    light_color: str = "white",
    gradient: bool = False,
    grad_type: str = "vertical",
) -> BytesIO:
    if not data.strip():
        raise HTTPException(status_code=400, detail="Missing data to encode")

    qr = segno.make(data, micro=False)
    buf = BytesIO()

    # --- Normal solid color QR
    if not gradient:
        qr.save(buf, kind="png", scale=scale, border=border, dark=dark_color, light=light_color)
        buf.seek(0)
        return buf

    # --- Gradient mode
    tmp = BytesIO()
    qr.save(tmp, kind="png", scale=scale, border=border)
    tmp.seek(0)
    qr_img = Image.open(tmp).convert("L")  # grayscale mask
    w, h = qr_img.size

    # Binary mask (1-bit)
    mask = qr_img.point(lambda p: 255 - p).convert("L")

    # Create gradient image
    grad = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(grad)
    c0 = ImageColor.getrgb(dark_color)
    c1 = ImageColor.getrgb(light_color)

    if grad_type == "vertical":
        for y in range(h):
            t = y / (h - 1)
            r = int(c0[0] * (1 - t) + c1[0] * t)
            g = int(c0[1] * (1 - t) + c1[1] * t)
            b = int(c0[2] * (1 - t) + c1[2] * t)
            draw.line([(0, y), (w, y)], fill=(r, g, b))

    elif grad_type == "horizontal":
        for x in range(w):
            t = x / (w - 1)
            r = int(c0[0] * (1 - t) + c1[0] * t)
            g = int(c0[1] * (1 - t) + c1[1] * t)
            b = int(c0[2] * (1 - t) + c1[2] * t)
            draw.line([(x, 0), (x, h)], fill=(r, g, b))

    elif grad_type == "radial":
        cx, cy = w / 2, h / 2
        max_r = (cx**2 + cy**2) ** 0.5
        for y in range(h):
            for x in range(w):
                dx, dy = x - cx, y - cy
                t = min(1.0, (dx**2 + dy**2) ** 0.5 / max_r)
                r = int(c0[0] * (1 - t) + c1[0] * t)
                g = int(c0[1] * (1 - t) + c1[1] * t)
                b = int(c0[2] * (1 - t) + c1[2] * t)
                grad.putpixel((x, y), (r, g, b))

    # Composite gradient with white background using the QR mask
    white_bg = Image.new("RGB", (w, h), "white")
    final_img = Image.composite(grad, white_bg, mask)

    final_img.save(buf, format="PNG")
    buf.seek(0)
    return buf




@app.get("/qr.png")
def qr_png(
    request: Request,
    data: str | None = Query(None, description="Raw text or URL to encode"),
    slug: str | None = Query(None, description="Slug of a saved QR entry"),
    scale: int = Query(8, ge=1, le=20),
    border: int = Query(2, ge=0, le=10),

    # 🎨 Color and gradient params
    dark_color: str = Query("black", description="Dark module color"),
    light_color: str = Query("white", description="Light background color"),
    gradient: bool = Query(False, description="Enable gradient fill for modules"),
    grad_type: str = Query(
        "vertical",
        regex="^(vertical|horizontal|radial)$",
        description="Gradient direction: vertical, horizontal, or radial"
    ),

    db=Depends(get_db),
):
    """
    Generate a PNG QR code with optional gradient coloring and slug support.
    """
    # Retrieve data if not directly provided
    if not data:
        if not slug:
            raise HTTPException(status_code=400, detail="Missing 'data' or 'slug'")
        q = crud.get_qr_by_slug(db, slug)
        if not q:
            raise HTTPException(status_code=404, detail="QR not found")

        base = os.getenv("PUBLIC_BASE_URL") or str(request.base_url).rstrip("/")
        data = f"{base}/r/{q.slug}"

    # 🧠 Call our gradient-aware QR generator
    img = qr_bytes(
        data=data,
        kind="png",
        scale=scale,
        border=border,
        dark_color=dark_color,
        light_color=light_color,
        gradient=gradient,
        grad_type=grad_type,
    )

    return StreamingResponse(img, media_type="image/png")


@app.get("/qr.svg")
def qr_svg(data: str = Query(..., description="Text/URL to encode")):
    buf = qr_bytes(data, kind="svg")
    return StreamingResponse(buf, media_type="image/svg+xml")


@app.get("/qr/echo", response_class=PlainTextResponse)
def qr_echo(data: str):
    return unquote(data)


# ======================
# 📦 DATABASE MODELS + API
# ======================

class QRIn(BaseModel):
    title: str
    type: str = "URL"  # "URL", "WIFI", "VCARD", "TEXT"
    target_url: Optional[AnyUrl] = None
    data: Optional[Dict[str, Any]] = None
    note: Optional[str] = None


class QROut(BaseModel):
    id: int
    slug: str
    title: str
    type: str
    target_url: str
    note: Optional[str] = None
    created_at: str
    scans_count: int

    @staticmethod
    def from_model(m: QR):
        return QROut(
            id=m.id,
            slug=m.slug,
            title=m.title,
            type=m.type,
            target_url=m.target_url,
            note=m.note,
            created_at=m.created_at.isoformat(),
            scans_count=m.scans_count,
        )


# --- Create a new QR ---
@app.post("/api/qr", response_model=QROut)
def api_create_qr(payload: QRIn, db=Depends(get_db)):
    """Create and store QR code metadata based on type."""
    qr_text = ""

    if payload.type == "URL":
        qr_text = str(payload.target_url)
    elif payload.type == "WIFI":
        info = payload.data or {}
        ssid = info.get("ssid", "")
        password = info.get("password", "")
        enc = info.get("encryption", "nopass")
        qr_text = f"WIFI:T:{enc};S:{ssid};P:{password};;"
    elif payload.type == "VCARD":
        info = payload.data or {}
        name = info.get("name", "")
        phone = info.get("phone", "")
        email = info.get("email", "")
        qr_text = (
            "BEGIN:VCARD\nVERSION:3.0\n"
            f"N:{name}\nTEL:{phone}\nEMAIL:{email}\nEND:VCARD"
        )
    elif payload.type == "TEXT":
        info = payload.data or {}
        qr_text = info.get("content", "")
    else:
        raise HTTPException(400, "Unsupported QR type")

    q = crud.create_qr(
        db,
        title=payload.title,
        target_url=qr_text,
        note=payload.note,
    )

    return QROut.from_model(q)


# --- List all QRs ---
@app.get("/api/qrs", response_model=list[QROut])
def api_list_qr(db=Depends(get_db)):
    items = crud.list_qrs(db)
    return [QROut.from_model(x) for x in items]


# --- Get QR by slug ---
@app.get("/api/qr/{slug}", response_model=QROut)
def api_get_qr(slug: str, db=Depends(get_db)):
    q = crud.get_qr_by_slug(db, slug)
    if not q:
        raise HTTPException(404, "QR code not found")
    return QROut.from_model(q)


# --- Redirect & record scan ---
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


# --- QR stats ---
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
