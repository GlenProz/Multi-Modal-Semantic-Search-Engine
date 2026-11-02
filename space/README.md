---
title: NGA Art Search
emoji: 🖼️
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# NGA Art Search — backend

FastAPI backend for the [Multi-Modal Semantic Search
Engine](https://github.com/GlenProz/Multi-Modal-Semantic-Search-Engine).
Serves semantic search over ~145k National Gallery of Art works:

- `GET /search/images?q=&k=&movements=` — CLIP text→image
- `GET /search/text?q=&k=` — MiniLM metadata search
- `GET /search/hybrid?q=&k=` — Reciprocal Rank Fusion across text + CLIP pixels
- `GET /search/visual?id=&k=` — DINOv2 visual similarity
- `GET /random-artwork`
- `GET /health`

The in-memory NumPy store loads the parquet snapshots at startup (`USE_MEMORY_STORE=1`);
MiniLM and CLIP encoders load on the first query. The public web frontend
proxies to these endpoints.
