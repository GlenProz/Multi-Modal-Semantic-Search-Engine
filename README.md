# Multi-Modal Semantic Search Engine (NLP + Vision)

Semantic search over the [National Gallery of Art open dataset](https://github.com/NationalGalleryOfArt/opendata) — ~130k artworks, ~17 relational tables, open-access IIIF media. Query in natural language (*"moody European rainy-day landscapes"*, *"two figures embracing under a tree"*) and get ranked results by meaning, not keyword overlap.

Three parallel systems working together:

- **Text (MiniLM, 145k artworks)** — metadata joined across 17 NGA tables (title, medium, attribution, provenance, dimensions) plus AI-generated visual alt-text (`assistivetext`), all embedded with `all-MiniLM-L6-v2`. Meaning-aware: *"oil on canvas"* and *"painted in oil"* are neighbors in vector space.
- **Image (CLIP ViT-B/32, 63k artworks)** — actual artwork pixels embedded into CLIP's shared text/image space. A text query retrieves images directly by visual meaning, not by their labels.
- **Movement classifier (WikiArt ViT-B/16, 63k artworks)** — each artwork is classified into one of nine Western art movements with a confidence score and a historical plausibility check. Results surface as color-coded badges: 🟢 confident match, 🟡 uncertain, 🔴 low confidence, ⚠️ historically anachronistic.

All three indexes live in local ChromaDB, served by a FastAPI app, with a Streamlit UI on top.

---

## Stack

| Layer | Choice |
|---|---|
| Text embeddings | `sentence-transformers/all-MiniLM-L6-v2` (384-d) |
| Multi-modal embeddings | `open_clip` `ViT-B-32` / `laion2b_s34b_b79k` (512-d) |
| Movement classifier | `oschamp/vit-artworkclassifier` (WikiArt ViT-B/16, 9 classes) |
| Vector DB | ChromaDB, local file-backed |
| API | FastAPI + Uvicorn |
| UI | Streamlit |
| GPU | PyTorch 2.11 cu128, tested on RTX 3060 Ti (8 GB) |

---

## How the search works

```
Text query ("impressionist harbor scene")
    │
    ├─► MiniLM encoder (384-d) ─► cosine search in nga_artworks ─► ranked metadata matches
    │
    └─► CLIP text encoder (512-d) ─► cosine search in nga_images ─► ranked image matches
                                            │
                                            └─► each result has: title, attribution, date,
                                                IIIF thumbnail, movement badge, confidence, anachronism flag
```

CLIP's key property: text and images share the same embedding space. A query for *"melancholy figure alone in a field"* retrieves images where the pixels encode that mood — even if the artwork has no metadata at all.

---

## The movement classifier: cross-domain limits as a feature

The `oschamp/vit-artworkclassifier` model was fine-tuned on [WikiArt](https://www.wikiart.org/) — a dataset of Western paintings from 1300–1960. The NGA collection is far broader: ancient Egyptian artifacts, Japanese Ukiyo-e prints, Renaissance sculptures, 20th-century photography, and decorative arts.

When forced to assign one of nine painting-era movement labels to a Greek amphora or a Meiji-era woodblock print, the model does its best — and the date-range plausibility check catches the mismatch. **44.8% of artworks are flagged anachronistic**, which is not a bug: it's honest signal that the model's training distribution doesn't match the NGA's collection diversity.

This is a useful portfolio talking point:

> *"The high anachronism rate shows what happens when a classification model is applied outside its training domain. Rather than hiding this, the UI surfaces it with ⚠️ flags, so a user immediately understands when to trust the prediction and when the model is being asked something it wasn't designed for."*

The `is_plausible()` function in [`src/multimodal_search/embed/movement.py`](src/multimodal_search/embed/movement.py) applies a ±25-year slack window around each movement's historical span. A Baroque label on a 1920 photograph fails this check; a Baroque label on a 1680 oil painting passes.

**Movement distribution (63,249 artworks):**

| Movement | Count | % |
|---|---|---|
| art_nouveau | 25,326 | 40% |
| baroque | 10,256 | 16% |
| renaissance | 7,610 | 12% |
| romanticism | 7,046 | 11% |
| realism | 5,294 | 8% |
| expressionism | 3,638 | 6% |
| surrealism | 1,730 | 3% |
| impressionism | 1,284 | 2% |
| post_impressionism | 1,065 | 2% |

`art_nouveau` at 40% reflects the NGA's large collection of ornate decorative prints, drawings, and engravings — which share visual surface features with Art Nouveau patterns even when they're not historically Art Nouveau works.

---

## Layout

```
src/multimodal_search/
  ingest/
    nga.py          # NGA CSV loaders, joins 17 tables, appends assistivetext
    images.py       # samples open-access primary-view images (incremental)
  embed/
    text.py         # MiniLM encoder (lru_cache, batched)
    clip.py         # open_clip ViT-B/32 GPU encoder — text and image paths
    movement.py     # WikiArt ViT-B/16 classifier + date-range plausibility check
  store/
    chroma.py       # PersistentClient wrapper, cosine metric
  search/
    query.py        # text query → MiniLM → nga_artworks
  api/
    app.py          # FastAPI: /search/text, /search/images, /random-artwork, /health

scripts/
  fetch_nga_data.py       # download NGA tables → data/raw/
  build_index.py          # MiniLM embed all 145k artworks → nga_artworks
  fetch_images.py         # async-download N new IIIF thumbnails (incremental, 16-concurrent)
  build_image_index.py    # CLIP-embed images → nga_images (skips already-embedded)
  classify_movements.py   # WikiArt ViT classify all images → update nga_images metadata
  search.py               # CLI: text query, text index
  search_images.py        # CLI: text query, image index
  ui.py                   # Streamlit UI

data/
  raw/         # NGA CSVs (gitignored)
  images/      # downloaded IIIF thumbnails (gitignored)
  chroma/      # local vector DB (gitignored)
```

---

## Setup (Windows + NVIDIA GPU)

```powershell
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip

# CUDA torch wheels first — must pin before other installs pull a CPU build
.venv\Scripts\python.exe -m pip install torch==2.11.0 torchvision --index-url https://download.pytorch.org/whl/cu128

.venv\Scripts\python.exe -m pip install -r requirements.txt

# verify GPU is visible
.venv\Scripts\python.exe -c "import torch; print('cuda:', torch.cuda.is_available())"
```

Linux/Mac (no CUDA): replace the `cu128` wheel with the standard `pip install torch torchvision` — CPU inference is slower but works.

---

## Build the indexes

```powershell
# 1. Fetch NGA open data (~250 MB of CSVs)
.venv\Scripts\python.exe scripts\fetch_nga_data.py

# 2. Text index: MiniLM embed all 145k artworks (~3 min on RTX 3060 Ti)
.venv\Scripts\python.exe scripts\build_index.py

# 3. Download artwork thumbnails — start small, scale up
.venv\Scripts\python.exe scripts\fetch_images.py 5000    # ~75 MB, ~1 min
.venv\Scripts\python.exe scripts\fetch_images.py 63000   # adds ~58k more (incremental)

# 4. Image index: CLIP-embed all downloaded images (~120 imgs/sec on 3060 Ti)
.venv\Scripts\python.exe scripts\build_image_index.py

# 5. Movement classifier: WikiArt ViT across all embedded images (~66 imgs/sec on 3060 Ti)
.venv\Scripts\python.exe scripts\classify_movements.py
```

Steps 3–5 are all incremental — re-running grows the dataset instead of repeating work.

---

## Run the API + UI

Two terminals:

```powershell
# terminal 1 — FastAPI on http://127.0.0.1:8000
.venv\Scripts\python.exe -m uvicorn multimodal_search.api.app:app --app-dir src

# terminal 2 — Streamlit UI on http://127.0.0.1:8501
.venv\Scripts\python.exe -m streamlit run scripts\ui.py
```

API endpoints (auto-documented at `http://127.0.0.1:8000/docs`):

| Endpoint | Description |
|---|---|
| `GET /search/text?q=...&k=10` | MiniLM text → metadata vectors |
| `GET /search/images?q=...&k=10` | CLIP text → image vectors |
| `GET /random-artwork` | random artwork from the image-indexed set |
| `GET /health` | collection counts |

---

## CLI (no UI needed)

```powershell
.venv\Scripts\python.exe scripts\search.py        "sleeping cat" 5
.venv\Scripts\python.exe scripts\search_images.py "moody European rainy day landscape" 10
```

---

## What works today

| Stage | Status |
|---|---|
| NGA ingest + 17-table join | done — 145,560 artwork docs |
| assistivetext enrichment | done — AI-generated visual alt-text per artwork |
| Text index (MiniLM) | done — `nga_artworks`, 145,560 rows |
| Image download (async, incremental) | done — 63,249 thumbnails |
| Image index (CLIP ViT-B/32) | done — `nga_images`, 63,249 rows |
| Movement classifier (WikiArt ViT) | done — top-3 predictions + confidence + anachronism flag |
| FastAPI service | done — text, image, random, health |
| Streamlit UI | done — search + random + thumbnail grid + movement badges |
| Eval harness (recall@k / MRR) | planned |
| Hosted public demo | planned |

---

## Pre-built index (skip the GPU work)

Building the indexes from scratch takes ~30 minutes of GPU time. If you just want to search, download the pre-built vector indexes from the [GitHub Releases page](https://github.com/GlenProz/Multi-Modal-Semantic-Search-Engine/releases/latest):

- `nga_artworks.parquet` — 145k MiniLM text vectors + metadata
- `nga_images.parquet` — 63k CLIP image vectors + metadata + movement predictions

Place both files in `data/releases/`, then import:

```powershell
# fast path: import pre-built index (skip fetch_nga_data + build_index + fetch_images + build_image_index + classify_movements)
.venv\Scripts\python.exe scripts\import_index.py

# or let the script fetch the files automatically:
.venv\Scripts\python.exe scripts\import_index.py --download
```

Then go straight to **Run the API + UI** below. The artwork images are served live from NGA's CDN — no local image files needed.

To export a fresh snapshot of your own indexes (after re-embedding or updating):

```powershell
# stop uvicorn first (ChromaDB files are locked while the server is running)
.venv\Scripts\python.exe scripts\export_index.py
# output: data/releases/nga_artworks.parquet + nga_images.parquet
```

---

## Sharing / hosting

The pre-built index covers the full NGA open-access collection. Anyone can clone the repo, run `import_index.py --download`, and be searching in a few minutes with no GPU required.

A hosted demo (no download at all) is on the roadmap: migrate to Qdrant Cloud, deploy FastAPI to Railway or Fly.io, Streamlit UI to HuggingFace Spaces. Artwork images are already on NGA's CDN via IIIF URLs, so no image hosting is needed.

---

## Data

All artwork data is from the [National Gallery of Art open dataset](https://github.com/NationalGalleryOfArt/opendata), released under [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/). Images are served by NGA's IIIF API and subject to NGA's terms of use.
