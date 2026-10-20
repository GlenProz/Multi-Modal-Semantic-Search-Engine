"""Hybrid multi-modal search combining text metadata (MiniLM) and visual pixels (CLIP).

Uses Reciprocal Rank Fusion (RRF) to combine ranked retrieval lists from both
vector spaces, matching artworks on NGA `objectid`.
"""
from __future__ import annotations

from typing import Any

from ..embed.clip import encode_texts
from ..search.query import search as text_search
from ..store.chroma import get_collection


def hybrid_search(
    query: str,
    k: int = 10,
    w_text: float = 0.5,
    w_image: float = 0.5,
    movements: list[str] | None = None,
    exclude_anachronistic: bool = False,
    rrf_k: int = 60,
) -> list[dict[str, Any]]:
    """Perform hybrid search over text and image collections using Reciprocal Rank Fusion.

    Parameters:
      query: natural language search query.
      k: number of final results to return.
      w_text: weight assigned to text metadata rank (0.0 to 1.0).
      w_image: weight assigned to image pixel rank (0.0 to 1.0).
      movements: optional list of movement strings to filter images by.
      exclude_anachronistic: whether to exclude artworks flagged as historically anachronistic.
      rrf_k: smoothing constant for RRF (standard default is 60).
    """
    candidate_k = max(k * 3, 30)

    # 1. Text retrieval (MiniLM over metadata + alt-text)
    text_results = text_search(query, k=candidate_k)

    # 2. Image retrieval (CLIP over artwork pixels)
    img_coll = get_collection("nga_images")
    vec = encode_texts([query])[0].tolist()
    where: dict[str, Any] | None = None
    if movements:
        mvlist = [m.strip() for m in movements if m.strip()]
        if len(mvlist) == 1:
            where = {"pred_movement": mvlist[0]}
        elif len(mvlist) > 1:
            where = {"pred_movement": {"$in": mvlist}}

    query_kwargs: dict[str, Any] = {"query_embeddings": [vec], "n_results": candidate_k}
    if where:
        query_kwargs["where"] = where
    img_res = img_coll.query(**query_kwargs)

    image_results: list[dict[str, Any]] = [
        {
            "uuid": img_res["ids"][0][i],
            "score": 1 - img_res["distances"][0][i],
            "metadata": img_res["metadatas"][0][i] or {},
        }
        for i in range(len(img_res["ids"][0]))
    ]

    # 3. Build lookup maps keyed by objectid (as string)
    text_by_obj: dict[str, tuple[int, dict[str, Any]]] = {}
    for rank, item in enumerate(text_results, start=1):
        obj_id = str(item.get("objectid", ""))
        if obj_id:
            text_by_obj[obj_id] = (rank, item)

    image_by_obj: dict[str, tuple[int, dict[str, Any]]] = {}
    for rank, item in enumerate(image_results, start=1):
        meta = item["metadata"]
        obj_id = str(meta.get("objectid", ""))
        if obj_id:
            image_by_obj[obj_id] = (rank, item)

    # 4. Compute RRF scores across union of candidate object IDs
    all_obj_ids = set(text_by_obj.keys()) | set(image_by_obj.keys())
    scored: list[dict[str, Any]] = []

    for obj_id in all_obj_ids:
        t_entry = text_by_obj.get(obj_id)
        i_entry = image_by_obj.get(obj_id)

        # Anachronism filter
        if exclude_anachronistic and i_entry:
            if i_entry[1]["metadata"].get("pred_anachronistic"):
                continue

        score = 0.0
        if t_entry:
            rank_t = t_entry[0]
            score += w_text * (1.0 / (rrf_k + rank_t))
        if i_entry:
            rank_i = i_entry[0]
            score += w_image * (1.0 / (rrf_k + rank_i))

        # Merge metadata
        merged_meta: dict[str, Any] = {}
        if t_entry:
            merged_meta.update(t_entry[1].get("metadata") or {})
        if i_entry:
            merged_meta.update(i_entry[1].get("metadata") or {})

        uuid_val = i_entry[1]["uuid"] if i_entry else ""
        doc_val = t_entry[1].get("document") if t_entry else None

        scored.append({
            "objectid": obj_id,
            "uuid": uuid_val,
            "score": round(score, 6),
            "text_score": round(t_entry[1]["score"], 4) if t_entry else None,
            "image_score": round(i_entry[1]["score"], 4) if i_entry else None,
            "metadata": merged_meta,
            "document": doc_val,
        })

    # Sort descending by fused RRF score
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:k]
