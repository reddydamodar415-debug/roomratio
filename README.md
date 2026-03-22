# 🏠 RoomRatio MVP
### AI-Powered 60-30-10 Interior Color Analysis

---

## What's Built

```
roomratio/
├── backend/
│   ├── color_engine.py      # Core AI: color extraction + 60-30-10 engine
│   ├── main.py              # FastAPI REST API
│   └── requirements.txt     # Python dependencies
├── frontend/
│   └── index.html           # Full web app (works standalone too)
└── README.md
```

---

## Quick Start (5 minutes)

### 1. Run the Python Backend

```bash
cd roomratio/backend

# Install dependencies
pip install -r requirements.txt

# Start the API server
uvicorn main:app --reload --port 8000
```

API is now live at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs`

### 2. Open the Web App

```bash
# Option A: Open directly in browser (works standalone)
open roomratio/frontend/index.html

# Option B: Serve with Python
cd roomratio/frontend
python -m http.server 3000
# then visit http://localhost:3000
```

---

## API Endpoints

### `POST /analyze`
Upload a room image, get full 60-30-10 analysis.

```bash
curl -X POST http://localhost:8000/analyze \
  -F "file=@my-room.jpg"
```

**Response:**
```json
{
  "success": true,
  "score": {
    "score": 84,
    "grade": "Excellent",
    "dominant_pct": 59.2,
    "secondary_pct": 31.1,
    "accent_pct": 9.7
  },
  "zones": {
    "dominant": { "colors": [...], "target_pct": 60 },
    "secondary": { "colors": [...], "target_pct": 30 },
    "accent": { "colors": [...], "target_pct": 10 }
  },
  "suggestions": ["Your room is beautifully balanced!"],
  "ideal_palette": {
    "dominant": { "hex": "#C8A882", "name": "Sandy Tan" },
    "secondary": { "hex": "#7B9E87", "name": "Sage Green" },
    "accent": { "hex": "#D4553A", "name": "Terracotta" }
  }
}
```

### `POST /palette`
Generate a 60-30-10 palette from a dominant color.

```bash
curl -X POST http://localhost:8000/palette \
  -H "Content-Type: application/json" \
  -d '{"dominant_hex": "#C8A882"}'
```

### `GET /sample-palettes`
Get pre-built palettes for different room styles.

---

## How the AI Engine Works

### 1. Color Extraction (`color_engine.py`)
```
Room Image → Resize to 300px → Filter near-black/white pixels
→ K-Means Clustering (7 clusters) → Sort by visual dominance
```

### 2. 60-30-10 Zone Assignment
```
Colors sorted by % →
  Cumulative 0-62% = Dominant (walls, floors, large furniture)
  Cumulative 62-92% = Secondary (sofa, bed, curtains)
  Cumulative 92-100% = Accent (doors, trims, accessories)
```

### 3. Balance Scoring
```
Score = 100 - deviation_penalty
Dominant deviation × 0.8 (most important)
Secondary deviation × 0.6
Accent deviation × 0.4
```

### 4. Palette Generation
```
Dominant color → Color theory (HSL color wheel)
  Secondary = +30° analogous, slightly desaturated
  Accent = +120° triadic, more saturated
```

---

## Next Steps to Build

### Phase 2 - Add to Backend
- [ ] `POST /analyze/style` — Detect room style (Scandinavian, Industrial, etc.)
- [ ] `GET /products?colors=...` — Match products from affiliate catalog
- [ ] `POST /export/pdf` — Generate PDF mood board with Puppeteer
- [ ] Add PostgreSQL via Supabase for saving analyses

### Phase 3 - Mobile App
```bash
# Create React Native app
npx create-expo-app RoomRatio
cd RoomRatio
npm install
```
Point the API calls to `http://YOUR_LOCAL_IP:8000` from the mobile app.

### Phase 4 - Deploy
```bash
# Backend: Deploy to Railway or Render (free tier)
# Frontend: Deploy to Vercel (free tier)
# Database: Supabase free tier
```

---

## Tech Stack
| Layer | Technology |
|-------|-----------|
| AI Color Engine | Python + scikit-learn K-Means |
| Backend API | FastAPI + Uvicorn |
| Web Frontend | HTML + Vanilla JS (no framework needed for MVP) |
| Mobile (next) | React Native + Expo |
| Database (next) | Supabase (PostgreSQL) |
| Hosting (next) | Vercel (web) + Railway (API) |
