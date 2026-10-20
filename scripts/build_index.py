"""Flatten NGA tables → embed → upsert into ChromaDB."""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from multimodal_search.ingest.nga import build_artwork_documents
from multimodal_search.embed.text import embed
from multimodal_search.store.chroma import get_collection

BATCH = 1000


def main() -> None:
    df = build_artwork_documents()
    print(f"prepared {len(df):,} artwork documents")
    coll = get_collection()

    for start in range(0, len(df), BATCH):
        chunk = df.iloc[start:start + BATCH]
        vecs = embed(chunk["document"].tolist())
        coll.upsert(
            ids=chunk["objectid"].astype(str).tolist(),
            embeddings=[v.tolist() for v in vecs],
            documents=chunk["document"].tolist(),
            metadatas=[
                {
                    "title": str(r.title) if pd.notna(r.title) else "",
                    "artists": str(r.artists) if pd.notna(r.artists) else "",
                    "date": str(r.displaydate) if pd.notna(r.displaydate) else "",
                    "classification": str(r.classification) if pd.notna(r.classification) else "",
                    "medium": str(r.medium) if pd.notna(r.medium) else "",
                    "iiif": str(r.iiif) if pd.notna(r.iiif) else "",
                }
                for r in chunk.itertuples(index=False)
            ],
        )
        print(f"  upserted {start + len(chunk):,}/{len(df):,}")


if __name__ == "__main__":
    main()
