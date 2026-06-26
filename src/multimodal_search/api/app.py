from __future__ import annotations
import random
from functools import lru_cache
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from ..search.query import search as text_search
from ..embed.clip import encode_texts
from ..store.chroma import get_collection

app = FastAPI(title="NGA Semantic Search")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@lru_cache(maxsize=1)
def _all_image_ids() -> list[str]:
    return get_collection("nga_images").get(include=[])["ids"]


@app.get("/health")
def health():
    dino_count = 0
    try:
        dino_count = get_collection("nga_dino").count()
    except Exception:
        pass
    return {
        "ok": True,
        "text_count": get_collection("nga_artworks").count(),
        "image_count": get_collection("nga_images").count(),
        "dino_count": dino_count,
    }


@app.get("/search/text")
def search_text(q: str, k: int = 10):
    return {"query": q, "mode": "text", "results": text_search(q, k=k)}


@app.get("/search/images")
def search_images(
    q: str,
    k: int = 10,
    movements: Optional[str] = Query(default=None, description="Comma-separated movement filter, e.g. baroque,realism"),
):
    vec = encode_texts([q])[0].tolist()
    where = None
    if movements:
        mvlist = [m.strip() for m in movements.split(",") if m.strip()]
        if len(mvlist) == 1:
            where = {"pred_movement": mvlist[0]}
        elif len(mvlist) > 1:
            where = {"pred_movement": {"$in": mvlist}}
    kwargs = {"query_embeddings": [vec], "n_results": k}
    if where:
        kwargs["where"] = where
    res = get_collection("nga_images").query(**kwargs)
    out = [
        {
            "uuid": res["ids"][0][i],
            "score": 1 - res["distances"][0][i],
            "metadata": res["metadatas"][0][i],
        }
        for i in range(len(res["ids"][0]))
    ]
    return {"query": q, "mode": "image", "results": out}


@app.get("/search/visual")
def search_visual(id: str, k: int = 10):
    """Find artworks that visually resemble the given artwork (DINOv2 structural similarity)."""
    coll = get_collection("nga_dino")
    seed = coll.get(ids=[id], include=["embeddings", "metadatas"])
    if not seed["ids"]:
        raise HTTPException(404, f"UUID {id!r} not found in DINOv2 index")
    vec = seed["embeddings"][0]
    seed_meta = seed["metadatas"][0] or {}
    res = coll.query(query_embeddings=[vec], n_results=k + 1)
    out = [
        {
            "uuid": res["ids"][0][i],
            "score": 1 - res["distances"][0][i],
            "metadata": res["metadatas"][0][i],
        }
        for i in range(len(res["ids"][0]))
        if res["ids"][0][i] != id        # exclude the seed itself
    ][:k]
    return {"seed_id": id, "seed_title": seed_meta.get("title", ""), "mode": "visual", "results": out}


@app.get("/random-artwork")
def random_artwork():
    ids = _all_image_ids()
    if not ids:
        raise HTTPException(404, "no images indexed")
    uid = random.choice(ids)
    rec = get_collection("nga_images").get(ids=[uid], include=["metadatas"])
    return {"uuid": uid, "metadata": rec["metadatas"][0]}
