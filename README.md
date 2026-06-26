# Multi-Modal Semantic Search Engine (NLP + Vision)

Semantic search over the [National Gallery of Art open dataset](https://github.com/NationalGalleryOfArt/opendata) — ~130k artworks across ~17 relational tables plus open-access IIIF media. Users query in natural language ("*moody European rainy-day landscapes*") and get ranked artworks by meaning, not keyword overlap.

Two parallel indexes:
- **Text (MiniLM)** — 145,560 artworks, embedded from joined metadata (title, medium, classification, attribution, dimensions, provenance).
- **Image (CLIP ViT-B/32)** — 54,998 artworks, embedded from the actual pictures. CLIP's shared text/image space means text queries retrieve images directly.

Both live in local ChromaDB; both are served by a FastAPI app; a Streamlit UI sits on top.

## Stack

| Layer | Choice |
|---|---|
| Text embeddings | `sentence-transformers/all-MiniLM-L6-v2` (384-d) |
| Multi-modal | `open_clip` `ViT-B-32` / `laion2b_s34b_b79k` (512-d) |
| Vector DB | ChromaDB, local file-backed |
| API | FastAPI + Uvicorn |
| UI | Streamlit |
| GPU | PyTorch 2.11 cu128, tested on RTX 3060 Ti (8 GB) |

## Layout

```
src/multimodal_search/
  ingest/      # NGA CSV loaders, artwork doc builder, image sampler
  embed/       # text (MiniLM) and clip (open_clip) encoders
  store/       # ChromaDB wrapper
  search/      # query → embedding → retrieval
  api/         # FastAPI app
scripts/
  fetch_nga_data.py     # download NGA tables -> data/raw/
  build_index.py        # MiniLM embed all 145k artworks -> nga_artworks
  fetch_images.py       # async-download N new IIIF thumbnails (incremental)
  build_image_index.py  # CLIP-embed images -> nga_images (skips already done)
  search.py             # CLI: text query, text index
  search_images.py      # CLI: text query, image index
  ui.py                 # Streamlit UI
data/
  raw/         # NGA CSVs (gitignored)
  images/      # downloaded artwork thumbnails (gitignored)
  chroma/      # local vector DB (gitignored)
```

## Setup (Windows + NVIDIA GPU)

```powershell
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip

# CUDA torch wheels FIRST — pinning here so the next install doesn't pull a CPU build
.venv\Scripts\python.exe -m pip install torch==2.11.0 torchvision --index-url https://download.pytorch.org/whl/cu128

.venv\Scripts\python.exe -m pip install -r requirements.txt

.venv\Scripts\python.exe -c "import torch; print('cuda:', torch.cuda.is_available())"
```

## Build the indexes

```powershell
.venv\Scripts\python.exe scripts\fetch_nga_data.py          # ~250 MB of CSVs
.venv\Scripts\python.exe scripts\build_index.py             # MiniLM, ~3 min on 3060 Ti

.venv\Scripts\python.exe scripts\fetch_images.py 5000       # async download, ~75 MB at 5k
.venv\Scripts\python.exe scripts\build_image_index.py       # CLIP, ~120 imgs/sec on 3060 Ti
```

`fetch_images.py` and `build_image_index.py` are both incremental — re-running grows the sample instead of repeating it. Run `fetch_images.py 50000` again later to scale up.

## Run the API + UI

Two terminals:

```powershell
# terminal 1 — FastAPI on http://127.0.0.1:8000
.venv\Scripts\python.exe -m uvicorn multimodal_search.api.app:app --app-dir src

# terminal 2 — Streamlit UI on http://127.0.0.1:8501
.venv\Scripts\python.exe -m streamlit run scripts\ui.py
```

API endpoints (also documented at <http://127.0.0.1:8000/docs>):
- `GET /search/images?q=...&k=10` — CLIP text → image vectors
- `GET /search/text?q=...&k=10` — MiniLM text → metadata vectors
- `GET /random-artwork` — random image from the indexed set
- `GET /health` — counts

## CLI (no UI needed)

```powershell
.venv\Scripts\python.exe scripts\search.py        "sleeping cat" 5
.venv\Scripts\python.exe scripts\search_images.py "moody European rainy day landscape" 10
```

## What works today

| Stage | Status |
|---|---|
| NGA ingest + flatten | done — 145,560 artwork docs |
| Text index (MiniLM) | done — `nga_artworks` collection |
| Image download (async) | done — incremental, 16-concurrent |
| Image index (CLIP) | done — `nga_images` collection, 54,998 rows |
| FastAPI service | done — text, image, random, health |
| Streamlit UI | done — search + random + thumbnail grid |
| Eval harness (recall@k / MRR) | not yet |
| Full-set image embed (~128k) | not yet (extrapolated ~18 min) |
