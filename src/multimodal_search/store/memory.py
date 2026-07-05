"""In-memory, NumPy-backed vector store — a drop-in replacement for the
ChromaDB collection interface used by the API.

Why: rebuilding a ChromaDB HNSW index for ~271k vectors at container-build
time exhausted the free Hugging Face build machine's memory. For a dataset
this size an exact brute-force cosine search over a normalized matrix is
fast (sub-100ms/query on CPU via BLAS) and needs no index construction — so
the Space just loads the exported parquet into memory at startup instead.

Selected in store/chroma.py when USE_MEMORY_STORE is set; local dev keeps
using real ChromaDB.

Only the surface the API actually calls is implemented: .query(), .get(),
.count(). Distances are returned as ``1 - cosine`` so the app's existing
``score = 1 - distance`` yields cosine similarity, matching ChromaDB's
cosine space.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

RELEASES_DIR = Path(
    os.getenv("RELEASES_DIR", os.getenv("DATA_DIR", "./data") + "/releases")
)

_FILES = {
    "nga_artworks": "nga_artworks.parquet",
    "nga_images": "nga_images.parquet",
    "nga_dino": "nga_dino.parquet",
}


class MemoryCollection:
    def __init__(self, name: str):
        path = RELEASES_DIR / _FILES[name]
        table = pq.read_table(path)
        self.ids: list[str] = [str(x) for x in table.column("id").to_pylist()]
        self.metas: list[dict] = [
            json.loads(x) for x in table.column("metadata_json").to_pylist()
        ]
        embs = np.asarray(table.column("embedding").to_pylist(), dtype=np.float32)
        norms = np.linalg.norm(embs, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self.embs = embs / norms
        self._id_to_idx = {i: n for n, i in enumerate(self.ids)}

    def count(self) -> int:
        return len(self.ids)

    def _matches(self, meta: dict, where: dict) -> bool:
        for field, cond in where.items():
            val = meta.get(field)
            if isinstance(cond, dict) and "$in" in cond:
                if val not in cond["$in"]:
                    return False
            elif val != cond:
                return False
        return True

    def query(
        self,
        query_embeddings,
        n_results: int = 10,
        where: dict | None = None,
        **_,
    ):
        q = np.asarray(query_embeddings[0], dtype=np.float32)
        norm = np.linalg.norm(q)
        if norm:
            q = q / norm

        sims = self.embs @ q  # cosine, since both sides are normalized

        if where:
            mask = np.fromiter(
                (self._matches(m, where) for m in self.metas),
                dtype=bool,
                count=len(self.metas),
            )
            cand = np.flatnonzero(mask)
        else:
            cand = np.arange(len(self.ids))

        if cand.size == 0:
            return {"ids": [[]], "distances": [[]], "metadatas": [[]], "documents": [[]]}

        k = min(n_results, cand.size)
        cand_sims = sims[cand]
        top_local = np.argpartition(-cand_sims, k - 1)[:k]
        top_local = top_local[np.argsort(-cand_sims[top_local])]
        top = cand[top_local]

        return {
            "ids": [[self.ids[i] for i in top]],
            "distances": [[float(1.0 - sims[i]) for i in top]],
            "metadatas": [[self.metas[i] for i in top]],
            "documents": [[None for _ in top]],
        }

    def get(self, ids=None, include=None, **_):
        include = include or []
        if ids is None:
            idxs = range(len(self.ids))
        else:
            idxs = [self._id_to_idx[i] for i in ids if i in self._id_to_idx]

        out: dict = {"ids": [self.ids[i] for i in idxs]}
        if "embeddings" in include:
            out["embeddings"] = [self.embs[i].tolist() for i in idxs]
        if "metadatas" in include:
            out["metadatas"] = [self.metas[i] for i in idxs]
        return out


@lru_cache(maxsize=8)
def get_collection(name: str = "nga_artworks") -> MemoryCollection:
    return MemoryCollection(name)
