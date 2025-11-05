from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import StreamingResponse, PlainTextResponse
from urllib.parse import unquote
from io import BytesIO
import segno

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
    
    
