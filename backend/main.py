from fastapi import FastAPI, Query, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse, PlainTextResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, AnyUrl
from urllib.parse import unquote
from io import BytesIO
import segno

from backend.db import Base, engine, get_db
from backend.models import QR
from backend import crud
from backend.utils import mask_ip

# create tables at startup 
Base.metadata.create_all(bind=engine)

# Create the FastAPI instance
app = FastAPI(title="Kyu-Ar-API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# a get endpoint at the root 
@app.get("/")
def read_root():
    return {"message": "Welcome to Kyu-Ar-API"} 


# Generate the QR code 
def qr_bytes(data: str, kind: str = "png", scale: int = 8, border: int = 2) -> BytesIO:
    if not data or data.strip() == "":
        raise HTTPException(status_code=400, detail="Missing 'data' to encode")
    
    # Accept already-encoded query strings
    payload = unquote(data)
    qr = segno.make(payload, micro=False)
    buf = BytesIO()
    if kind == "png":
        qr.save(buf, kind="png", scale=scale, border=border)
    elif kind == "svg":
        qr.save(buf, kind="svg", xmldecl=False)
    else:
        raise HTTPException(status_code=400, detail="Unsupported kind. Use 'png' or 'svg'.")
    buf.seek(0)
    return buf
    
# Endpoint to generate PNG and SVG QR codes    
    
@app.get("/qr.png")
def qr_png(
    data: str = Query(..., description="Text/URL to encode"),
    scale: int = Query(8, ge=1, le=20),
    border: int = Query(2, ge=0, le=10),
):
    buf = qr_bytes(data, kind="png", scale=scale, border=border)
    return StreamingResponse(buf, media_type="image/png")
    
@app.get("/qr.svg")
def qr_svg(
    data: str = Query(..., description="Text/URL to encode"),
): 
    buf = qr_bytes(data, kind="svg")
    return StreamingResponse(buf, media_type="image/svg+xml")
    
@app.get("/qr/echo", response_class=PlainTextResponse)
def qr_echo(data: str):
    return unquote(data)


# DB-backend QR API 

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
    
# Create a new QR code record
@app.post("/api/qr", response_model=QROut)
def api_create_qr(payload: QRIn, db=Depends(get_db)):
    q = crud.create_qr(db, title=payload.title, target_url=str(payload.target_url), note=payload.note)
    return QROut.from_model(q)

# List QR Codes
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


# Redirect endpoint and scan recording so that we can track scans 
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

# Stats endpoint for a QR code so that we can see scan events 
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
