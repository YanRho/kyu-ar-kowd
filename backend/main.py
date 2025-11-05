from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.responses import StreamingResponse, PlainTextResponse
from pydantic import BaseModel, AnyUrl
from urllib.parse import unquote
from io import BytesIO
import segno

from backend.db import Base, engine, get_db
from backend.models import QR
from backend import crud

# create tables at startup 
Base.metadata.create_all(bind=engine)

# Create the FastAPI instance
app = FastAPI(title="Kyu-Ar-API")


# a get endpoint at the root 
@app.get("/")
def read_root():
    return {"message": "Welcome to Kyu-Ar-API"} 


# Generate the QR code 
def qr_bytes(data: str, kind: str = "png", scale: int = 8, border: int = 2) -> BytesIO:
    if not data or data.strip() == "":
        raise HTTPException(status_code=400, details="Missing 'data' to encode")
    
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
    q = crud.create_qr(db, title=payload.title, target_url=str(payload.target_url, note=payload.note))
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
