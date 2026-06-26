from __future__ import annotations
from ..embed.text import embed
from ..store.chroma import get_collection


def search(query: str, k: int = 10):
    vec = embed([query])[0].tolist()
    res = get_collection().query(query_embeddings=[vec], n_results=k)
    out = []
    for i, doc_id in enumerate(res["ids"][0]):
        out.append({
            "objectid": doc_id,
            "score": 1 - res["distances"][0][i],
            "document": res["documents"][0][i],
            "metadata": res["metadatas"][0][i],
        })
    return out
