"""
RoomRatio API
=============
FastAPI backend exposing the AI color engine via REST.
Run with: uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import base64
import io

from color_engine import analyze_room, generate_complementary_palette

app = FastAPI(
    title="RoomRatio API",
    description="AI-powered 60-30-10 interior design color analysis",
    version="1.0.0",
)

# Allow frontend (Next.js on 3000, React Native) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health Check ───────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "app": "RoomRatio API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": ["/analyze", "/palette", "/docs"],
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


# ─── Room Analysis ──────────────────────────────────────────────────────────────

@app.post("/analyze")
async def analyze_room_image(file: UploadFile = File(...)):
    """
    Upload a room image and get full 60-30-10 color analysis.
    
    Returns:
    - Extracted color palette with percentages
    - 60/30/10 zone assignments
    - Balance score (0-100)
    - Design suggestions
    - Ideal complementary palette
    """
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail=f"File must be an image. Got: {file.content_type}"
        )

    # Read image bytes
    image_bytes = await file.read()

    if len(image_bytes) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="Image too large. Max 10MB.")

    try:
        result = analyze_room(image_bytes)
        return JSONResponse(content={
            "success": True,
            "filename": file.filename,
            **result,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/analyze/base64")
async def analyze_base64_image(payload: dict):
    """
    Analyze a room image provided as base64 string.
    Useful for React Native and web apps sending image data directly.
    
    Body: { "image": "base64string...", "filename": "room.jpg" }
    """
    image_b64 = payload.get("image", "")
    if not image_b64:
        raise HTTPException(status_code=400, detail="No image provided.")

    # Strip data URI prefix if present
    if "," in image_b64:
        image_b64 = image_b64.split(",")[1]

    try:
        image_bytes = base64.b64decode(image_b64)
        result = analyze_room(image_bytes)
        return JSONResponse(content={"success": True, **result})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# ─── Palette Generator ──────────────────────────────────────────────────────────

class PaletteRequest(BaseModel):
    dominant_hex: str  # e.g. "#C8A882"


@app.post("/palette")
def generate_palette(req: PaletteRequest):
    """
    Given a dominant color hex code, generate a complementary
    60-30-10 palette using color theory.
    """
    hex_color = req.dominant_hex.strip()
    if not hex_color.startswith("#") or len(hex_color) != 7:
        raise HTTPException(status_code=400, detail="Invalid hex color. Use format: #RRGGBB")

    try:
        palette = generate_complementary_palette(hex_color)
        return {"success": True, "palette": palette}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Sample Colors (for UI testing) ─────────────────────────────────────────────

@app.get("/sample-palettes")
def sample_palettes():
    """Return pre-built sample palettes for different room styles."""
    return {
        "palettes": [
            {
                "name": "Scandinavian Calm",
                "style": "Minimal & Airy",
                "dominant": {"hex": "#E8E0D5", "name": "Warm White"},
                "secondary": {"hex": "#7B9E87", "name": "Sage Green"},
                "accent": {"hex": "#C8A882", "name": "Natural Tan"},
            },
            {
                "name": "Warm Terracotta",
                "style": "Earthy & Bold",
                "dominant": {"hex": "#C8A882", "name": "Sand"},
                "secondary": {"hex": "#D4553A", "name": "Terracotta"},
                "accent": {"hex": "#1C1A17", "name": "Charcoal"},
            },
            {
                "name": "Modern Luxe",
                "style": "Dark & Dramatic",
                "dominant": {"hex": "#2C2C2C", "name": "Charcoal"},
                "secondary": {"hex": "#8B7355", "name": "Bronze"},
                "accent": {"hex": "#D4AF37", "name": "Gold"},
            },
            {
                "name": "Coastal Breeze",
                "style": "Fresh & Light",
                "dominant": {"hex": "#F0F4F8", "name": "Cloud White"},
                "secondary": {"hex": "#4A90A4", "name": "Ocean Blue"},
                "accent": {"hex": "#E8A87C", "name": "Sandy Coral"},
            },
        ]
    }
