# Multi-Modal Semantic Search Engine (NLP + Vision)

Semantic search over the [National Gallery of Art open dataset](https://github.com/NationalGalleryOfArt/opendata) (~130k artworks, ~17 relational tables + open-access media URLs). Users query in natural language — e.g. *"moody European rainy-day landscapes from the 19th century"* — and get back ranked artworks by meaning, not keywords.

## Phases

**Phase 1 — Text MVP**
- Ingest NGA CSV tables → flatten each artwork into a single descriptive document (title, medium, classification, attribution, culture, dimensions, provenance text, etc.).
- Embed with `sentence-transformers/all-MiniLM-L6-v2`.
- Store in ChromaDB (local, file-backed).
- CLI + minimal FastAPI search endpoint.

**Phase 2 — Multi-modal (CLIP)**
- Async-download a sampled subset of `iiifurl` images.
- Embed images with CLIP `ViT-B/32` vision encoder; embed text with the same CLIP text encoder.
- Joint vector space → query by text *or* image; rerank Phase-1 results.

**Phase 3 — Polish for portfolio**
- Streamlit demo UI with thumbnails.
- Migrate vector store to Supabase pgvector for a "cloud-deployed" story.
- Evaluation harness: held-out query set, recall@k, qualitative examples.

## Layout

```
src/multimodal_search/
  ingest/      # load + clean NGA CSVs into unified artwork docs
  embed/       # text + image embedding pipelines
  store/       # vector DB wrappers (chroma now, pgvector later)
  search/      # query → embedding → retrieval
  api/         # FastAPI app
data/
  raw/         # NGA CSVs (gitignored)
  images/      # downloaded artwork images (gitignored)
  chroma/      # local vector DB (gitignored)
notebooks/     # exploration
scripts/       # one-off CLI entrypoints (ingest, embed, search)
```

## Quickstart

```bash
python -m venv .venv && .venv\Scripts\activate    # Windows
pip install -r requirements.txt
python scripts/fetch_nga_data.py
python scripts/build_index.py
python scripts/search.py "moody rainy landscapes"
```
