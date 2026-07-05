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
Serves semantic search over ~130k National Gallery of Art works:

- `GET /search/images?q=&k=&movements=` — CLIP text→image
- `GET /search/text?q=&k=` — MiniLM metadata search
- `GET /search/visual?id=&k=` — DINOv2 visual similarity
- `GET /random-artwork`
- `GET /health`

The ChromaDB index is rebuilt from parquet and baked into the image at build
time; MiniLM and CLIP load lazily on the first query. The public frontend
(hosted separately on Vercel) proxies to these endpoints.
