from __future__ import annotations
import random
from functools import lru_cache
from fastapi import FastAPI, HTTPException
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
    return {
        "ok": True,
        "text_count": get_collection("nga_artworks").count(),
        "image_count": get_collection("nga_images").count(),
    }


@app.get("/search/text")
def search_text(q: str, k: int = 10):
    return {"query": q, "mode": "text", "results": text_search(q, k=k)}


@app.get("/search/images")
def search_images(q: str, k: int = 10):
    vec = encode_texts([q])[0].tolist()
    res = get_collection("nga_images").query(query_embeddings=[vec], n_results=k)
    out = [
        {
            "uuid": res["ids"][0][i],
            "score": 1 - res["distances"][0][i],
            "metadata": res["metadatas"][0][i],
        }
        for i in range(len(res["ids"][0]))
    ]
    return {"query": q, "mode": "image", "results": out}


@app.get("/random-artwork")
def random_artwork():
    ids = _all_image_ids()
    if not ids:
        raise HTTPException(404, "no images indexed")
    uid = random.choice(ids)
    rec = get_collection("nga_images").get(ids=[uid], include=["metadatas"])
    return {"uuid": uid, "metadata": rec["metadatas"][0]}
