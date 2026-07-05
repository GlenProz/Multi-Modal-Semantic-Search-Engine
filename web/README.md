# Art Search — web frontend

Custom Next.js UI for the [Multi-Modal Semantic Search
Engine](../README.md). Part of the
[hobby-projects](https://github.com/GlenProz/hobby-projects) playground.

The heavy ML (CLIP / MiniLM / DINOv2 + the ChromaDB index) runs on a
Hugging Face Space — it can't run on Vercel, since embedding a query at
request time needs multi-GB PyTorch models. This frontend is a thin,
styled layer: its `app/api/*` routes proxy to that Space so the backend
URL stays server-side and the routes can absorb the Space's cold-start.

## How it works

- **Visual search** (`/api/search?mode=images`) → CLIP text→image over the
  63k image index. Returns thumbnails + movement badges.
- **Metadata search** (`/api/search?mode=text`) → MiniLM over the 145k text
  index (metadata-only, no thumbnails).
- **Find similar** (`/api/similar?id=`) → DINOv2 structural similarity.
- **Surprise me** → random artwork, then seeds a visual-similarity grid.

Movement badges encode the WikiArt classifier's confidence (🟢 ≥50% /
🟡 ≥30% / 🔴 lower) plus a ⚠️ flag when the predicted movement is
historically anachronistic for the artwork's date.

## Setup

1. Copy `.env.example` to `.env.local` and set `ART_API_URL` to the Space URL.
2. `npm install && npm run dev`

## Deploy

Deployed on Vercel with **Root Directory = `web`** (the repo root is the
Python backend). Set `ART_API_URL` in the Vercel project's env vars.
