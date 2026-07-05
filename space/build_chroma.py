"""Rebuild the ChromaDB index from the exported parquet files.

Runs once at Docker image-build time so the running container has all three
collections ready — no rebuild on cold start (HF free Spaces have no
persistent volume, so a startup rebuild would repeat on every wake).

Standalone on purpose: talks to chromadb directly rather than importing the
app package, and creates collections with the same name + cosine metric the
API expects (see src/multimodal_search/store/chroma.py).
"""
from __future__ import annotations
import json
import os
from pathlib import Path

import pyarrow.parquet as pq
import chromadb
from chromadb.config import Settings

CHROMA_DIR = os.environ.get("CHROMA_DIR", "./data/chroma")
RELEASES = Path(os.environ.get("RELEASES_DIR", "./data/releases"))

COLLECTIONS = [
    ("nga_artworks", "nga_artworks.parquet"),  # MiniLM text index (145k)
    ("nga_images", "nga_images.parquet"),       # CLIP image index (63k)
    ("nga_dino", "nga_dino.parquet"),           # DINOv2 visual-similarity (63k)
]

BATCH = 2_000


def clean_meta(m: dict) -> dict:
    # ChromaDB rejects None-valued metadata; drop those keys.
    return {k: v for k, v in m.items() if v is not None}


def main() -> None:
    client = chromadb.PersistentClient(
        path=CHROMA_DIR, settings=Settings(anonymized_telemetry=False)
    )
    for name, fname in COLLECTIONS:
        path = RELEASES / fname
        if not path.exists():
            print(f"[skip] {fname} missing", flush=True)
            continue
        coll = client.get_or_create_collection(
            name=name, metadata={"hnsw:space": "cosine"}
        )
        if coll.count() > 0:
            print(f"[skip] {name} already built ({coll.count():,} rows)", flush=True)
            continue

        table = pq.read_table(path)
        ids = [str(x) for x in table.column("id").to_pylist()]
        embs = table.column("embedding").to_pylist()
        metas = [clean_meta(json.loads(x)) for x in table.column("metadata_json").to_pylist()]

        total = len(ids)
        print(f"[build] {name}: {total:,} rows", flush=True)
        for i in range(0, total, BATCH):
            coll.add(
                ids=ids[i : i + BATCH],
                embeddings=embs[i : i + BATCH],
                metadatas=metas[i : i + BATCH],
            )
            print(f"  {min(i + BATCH, total):,}/{total:,}", flush=True)

    print("[build] done", flush=True)


if __name__ == "__main__":
    main()
