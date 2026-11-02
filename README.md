# Multi-Modal Semantic Search Engine (NLP + Vision)

> 🎨 **Live Web Demo:** [**art.anchoranalytics.space**](https://art.anchoranalytics.space)  
> *Search 145,000 National Gallery of Art masterpieces live — powered by OpenCLIP, DINOv2, and MiniLM with Cloudflare Edge acceleration.*

[![Live Demo](https://img.shields.io/badge/Live_Demo-art.anchoranalytics.space-amber?style=for-the-badge&logo=cloudflare&logoColor=white)](https://art.anchoranalytics.space)
[![Hugging Face Space](https://img.shields.io/badge/Backend-HF_Space-purple?style=for-the-badge&logo=huggingface&logoColor=white)](https://huggingface.co/spaces/KerChoo/nga-art-search)
[![Tests](https://img.shields.io/badge/Tests-35%20passing-emerald?style=for-the-badge&logo=pytest&logoColor=white)](tests/)
[![Dataset](https://img.shields.io/badge/Dataset-NGA_Open_Data-blue?style=for-the-badge)](https://github.com/NationalGalleryOfArt/opendata)

---

## Overview

Semantic search over the [National Gallery of Art open dataset](https://github.com/NationalGalleryOfArt/opendata) — **145k artworks, 17 relational tables, and open-access IIIF media**. Query in natural language (*"moody European rainy-day landscapes"*, *"two figures embracing under a tree"*, *"dramatic baroque chiaroscuro"*) and retrieve ranked results by meaning and aesthetic mood, not keyword overlap.

Four parallel neural systems working together:

- **⚡ Hybrid Search (Reciprocal Rank Fusion, 145k artworks)** — Late-fusion ranker matching on NGA `objectid`. Merges text metadata context and image pixel aesthetics so results satisfy both visual feeling and archival facts.
- **🖼️ Image Embeddings (CLIP ViT-B/32, 63k artworks)** — Artwork pixels embedded into CLIP's joint text/image latent space. A text query retrieves paintings by visual meaning even if catalog metadata is missing.
- **🔍 Visual Similarity (DINOv2 ViT-S/14, 63k artworks)** — Self-supervised vision features capturing composition, brushwork, and structural neighbors without label bias.
- **🏷️ Movement Classifier (WikiArt ViT-B/16, 63k artworks)** — Classifies artworks into nine Western movements with confidence scoring and a historical plausibility check. Results surface as color-coded badges: 🟢 confident match, 🟡 uncertain, 🔴 low confidence, ⚠️ historically anachronistic.

---

## 1. Try It Online (Zero Setup)

You can explore the full collection immediately on the hosted production app:

👉 [**art.anchoranalytics.space**](https://art.anchoranalytics.space) (Mirror: [nga-art-search-5el.pages.dev](https://nga-art-search-5el.pages.dev))

- **What you can try:**
  - Search natural-language visual moods (*"solitary figure in a misty morning field"*)
  - Switch between **⚡ Hybrid (RRF)**, **🖼️ Visual (CLIP)**, and **📜 Catalog (MiniLM)** modes
  - Filter results dynamically by historical movement (*Baroque, Impressionism, Surrealism, etc.*)
  - Click **"Find visually similar"** on any artwork to explore its DINOv2 structural neighbors
  - Click **"Surprise Me"** to pick a random work and kick off serendipitous discovery
- **Cloudflare Edge Acceleration:** Search queries are cached at Cloudflare edge data centers globally. Popular queries return in **~130ms** (`X-Cache-Status: HIT`).
- **Zero Media Overhead:** All artwork images stream directly from the National Gallery of Art's public IIIF CDN (`media.nga.gov`).

---

## 2. Run It Locally

You can run the engine on your own machine. Choose either the **Fast Path** (instant setup with pre-built indexes) or the **Full Pipeline** (embed everything from scratch on your GPU).

### Option A: Fast Path (< 3 minutes, No GPU Required)

The pre-built vector snapshots cover the entire NGA collection (~271k vectors across MiniLM, CLIP, and DINOv2). You can download them directly from [GitHub Releases](https://github.com/GlenProz/Multi-Modal-Semantic-Search-Engine/releases/latest) and run locally on CPU:

```powershell
# 1. Clone the repository
git clone https://github.com/GlenProz/Multi-Modal-Semantic-Search-Engine.git
cd Multi-Modal-Semantic-Search-Engine

# 2. Set up Python virtual environment (using uv)
uv venv
uv pip install -r requirements.txt

# 3. Download and import the pre-built vector indexes
uv run python scripts/import_index.py --download

# 4. Start the FastAPI backend
uv run uvicorn multimodal_search.api.app:app --app-dir src --port 8000
```

In a second terminal, launch your preferred UI:

```powershell
# Streamlit UI (port 8501)
uv run streamlit run scripts/ui.py

# OR Next.js Web UI (port 3000)
cd web
npm install
npm run dev
```

Visit `http://localhost:8501` for Streamlit or `http://localhost:3000` for Next.js. Images stream live from NGA's IIIF servers — no image downloads needed.

---

### Option B: Build From Scratch (GPU Pipeline, ~30 mins on RTX 3060 Ti)

To ingest the raw data and recompute embeddings from scratch:

```powershell
# 1. Install CUDA-enabled PyTorch first
uv pip install torch==2.11.0 torchvision --index-url https://download.pytorch.org/whl/cu128
uv pip install -r requirements.txt

# 2. Fetch raw NGA relational tables (~250 MB CSVs)
uv run python scripts/fetch_nga_data.py

# 3. Ingest tables and generate MiniLM text index (145k docs, ~3 min)
uv run python scripts/build_index.py

# 4. Download thumbnail images (incremental, 16 concurrent workers)
uv run python scripts/fetch_images.py 5000     # sample test
uv run python scripts/fetch_images.py 63000    # full open-access set

# 5. Build OpenCLIP ViT-B/32 image index (~120 imgs/sec)
uv run python scripts/build_image_index.py

# 6. Build DINOv2 structural similarity index (~150 imgs/sec)
uv run python scripts/build_dino_index.py

# 7. Classify art movements with WikiArt ViT (~66 imgs/sec)
uv run python scripts/classify_movements.py
```

To export your local index for sharing or deployment:

```powershell
uv run python scripts/export_index.py
# Exports: data/releases/nga_artworks.parquet, nga_images.parquet, nga_dino.parquet
```

---

## Stack & Architecture

| Layer | Choice | Details |
|---|---|---|
| **Text Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` | 384-d, joined across 17 relational tables + `assistivetext` |
| **Multi-Modal Embeddings** | `open_clip ViT-B-32` (`laion2b_s34b_b79k`) | 512-d, joint text/image visual latent space |
| **Visual Structural Embeddings** | `facebook/dinov2-small` (`dinov2_vits14`) | 384-d, self-supervised composition & texture similarity |
| **Art Movement Classifier** | `oschamp/vit-artworkclassifier` | WikiArt ViT-B/16, 9 classes + date plausibility check |
| **Hybrid Search** | Reciprocal Rank Fusion (RRF) | Fuses text metadata rank and pixel rank on `objectid` |
| **Vector Storage** | Local ChromaDB + NumPy memory store | Zero-cost in-memory option for serverless deployments |
| **API Backend** | FastAPI + Uvicorn | Async endpoints: `/search/hybrid`, `/search/images`, `/search/visual`, `/search/text` |
| **Hosted Backend** | Hugging Face Space (Docker) | CPU-optimized container with pre-fetched model weights |
| **Web Frontend** | Next.js 16 + Tailwind CSS | Deployed on Cloudflare Pages with edge caching |
| **Testing** | `pytest` | 35 automated unit tests covering date math, bounds, RRF, and storage |

---

## How Hybrid Search (RRF) Works

```
User Query: "17th century Dutch still life with lemon and flowers"
    │
    ├──► [MiniLM Text Encoder] ──► Cosine search over nga_artworks
    │                                └─► Ranked by catalog facts (date, medium, title, terms)
    │
    └──► [CLIP Text Encoder]   ──► Cosine search over nga_images
                                     └─► Ranked by visual pixels (mood, color palette, lighting)
                                            │
                                            ▼
                  [Reciprocal Rank Fusion (RRF)]
                     RRF_Score = 1/(60 + Rank_text) + 1/(60 + Rank_clip)
                                            │
                                            ▼
                     Filtered by Date Plausibility & Movement
                                            │
                                            ▼
                           Top-K Artworks Returned with Badges
```

A text-only search for *"moody rainy day"* fails on traditional catalog keywords because curators don't write "moody" in museum records. A vision-only search might return a modern photograph when you wanted an antique oil painting. **Hybrid RRF** ensures works score high only when visual aesthetics and archival records align.

---

## Cross-Domain Movement Classification: Out-of-Distribution Detection

The `oschamp/vit-artworkclassifier` model was trained exclusively on Western oil paintings from 1300–1960 ([WikiArt](https://www.wikiart.org/)). The NGA collection is far broader: ancient Roman coins, Greek pottery, 10th-century Asian prints, and contemporary photography.

Rather than hiding when the model is applied outside its training distribution, the engine checks the predicted movement against the artwork's historical dates (`beginyear` / `endyear` or parsed display dates) using a ±25-year slack window:

- **44.8% of artworks are flagged ⚠️ anachronistic** (e.g. labeling a 500 BCE Greek vase as "Art Nouveau" or a 1970 print as "Baroque").
- The UI exposes this honestly via confidence badges (🟢 $\ge 50\%$, 🟡 $\ge 30\%$, 🔴 $< 30\%$) and warning flags, illustrating real-world machine learning domain shift in an educational, transparent way.

---

## Quantitative Evaluation Benchmark

The project includes an automated evaluation harness in [`scripts/evaluate.py`](scripts/evaluate.py) testing **Recall@K (1, 5, 10)**, **Mean Reciprocal Rank (MRR)**, and **query latency percentiles** across retrieval strategies:

```powershell
uv run python scripts/evaluate.py --queries 50 --k 10
```

Sample benchmark output:

| Strategy | Recall@1 | Recall@5 | Recall@10 | MRR | Latency (p50) | Latency (p95) |
|---|---|---|---|---|---|---|
| **Text Only (MiniLM)** | 0.54 | 0.78 | 0.86 | 0.63 | 12 ms | 28 ms |
| **Image Only (CLIP)** | 0.48 | 0.72 | 0.82 | 0.57 | 18 ms | 42 ms |
| **Hybrid (RRF)** | **0.68** | **0.88** | **0.94** | **0.75** | 24 ms | 56 ms |

---

## API Endpoints

FastAPI endpoints (auto-documented at `http://localhost:8000/docs`):

| Endpoint | Method | Parameters | Description |
|---|---|---|---|
| `/search/hybrid` | `GET` | `q`, `k=24`, `movements` | Reciprocal Rank Fusion across text + CLIP pixels |
| `/search/images` | `GET` | `q`, `k=24`, `movements` | OpenCLIP text→image vector search |
| `/search/visual` | `GET` | `id`, `k=24` | DINOv2 visual neighbor search |
| `/search/text` | `GET` | `q`, `k=24` | MiniLM metadata & curatorial text search |
| `/random-artwork` | `GET` | None | Returns random artwork from image-indexed collection |
| `/health` | `GET` | None | Live vector counts across all three indexes |

---

## Verification & Testing

Run the automated test suite covering date parsing, bounds checking, vector indexing, image skipping, and hybrid RRF search:

```powershell
uv run pytest
# 35 passed in ~15s
```

---

## License & Data Attribution

- Artwork metadata and images courtesy of the [National Gallery of Art Open Access Dataset](https://github.com/NationalGalleryOfArt/opendata), released under [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
- Code released under the [MIT License](LICENSE).
- Live website operated by Glen Prozanski / Anchor Analytics LLC at [art.anchoranalytics.space](https://art.anchoranalytics.space).
