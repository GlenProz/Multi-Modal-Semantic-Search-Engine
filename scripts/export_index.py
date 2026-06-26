"""Export ChromaDB collections to parquet for redistribution as a pre-built index.

Produces two files in data/releases/:
  nga_artworks.parquet  — 145k MiniLM text-index rows (id, embedding, metadata)
  nga_images.parquet    — 63k  CLIP image-index rows  (id, embedding, metadata)

NOTE: stop the uvicorn server before running this — ChromaDB holds exclusive locks
on the HNSW binary files while the server is up.

Usage:
  .venv\\Scripts\\python.exe scripts\\export_index.py
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from multimodal_search.config import DATA_DIR
from multimodal_search.store.chroma import get_collection

RELEASES_DIR = DATA_DIR / "releases"
RELEASES_DIR.mkdir(parents=True, exist_ok=True)

PAGE = 5_000


def export_collection(name: str, out_path: Path) -> None:
    coll = get_collection(name)
    total = coll.count()
    print(f"[export] {name}: {total:,} rows -> {out_path.name}", flush=True)

    ids_all, embeddings_all, metadata_all = [], [], []
    offset = 0
    while offset < total:
        page = coll.get(
            limit=PAGE,
            offset=offset,
            include=["embeddings", "metadatas"],
        )
        ids_all.extend(page["ids"])
        embeddings_all.extend(page["embeddings"])
        metadata_all.extend(page["metadatas"])
        offset += len(page["ids"])
        print(f"  {offset:,}/{total:,}", flush=True)
        if not page["ids"]:
            break

    df = pd.DataFrame({
        "id": ids_all,
        "embedding": embeddings_all,
        "metadata_json": [json.dumps(m or {}) for m in metadata_all],
    })

    schema = pa.schema([
        pa.field("id", pa.string()),
        pa.field("embedding", pa.list_(pa.float32())),
        pa.field("metadata_json", pa.string()),
    ])
    table = pa.Table.from_pandas(df, schema=schema)
    pq.write_table(table, out_path, compression="snappy")
    size_mb = out_path.stat().st_size / 1_048_576
    print(f"  saved {size_mb:.1f} MB", flush=True)


def main() -> None:
    export_collection("nga_artworks", RELEASES_DIR / "nga_artworks.parquet")
    export_collection("nga_images",   RELEASES_DIR / "nga_images.parquet")
    print("[export] done", flush=True)


if __name__ == "__main__":
    main()
