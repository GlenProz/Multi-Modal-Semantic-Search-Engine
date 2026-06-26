"""Embed all downloaded images with DINOv2-base → nga_dino ChromaDB collection.

Incremental: skips images already in the collection.
Copies metadata from nga_images so visual-similarity results are self-contained.

Usage:
  .venv\\Scripts\\python.exe scripts\\build_dino_index.py
"""
from __future__ import annotations
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from multimodal_search.config import IMAGES_DIR, DATA_DIR
from multimodal_search.embed.dino import encode_images
from multimodal_search.store.chroma import get_collection

BATCH = 64
COLLECTION = "nga_dino"


def main() -> None:
    df = pd.read_parquet(DATA_DIR / "image_sample.parquet")
    df["path"] = df["uuid"].apply(lambda u: IMAGES_DIR / f"{u}.jpg")
    df = df[df["path"].apply(lambda p: p.exists() and p.stat().st_size > 0)].reset_index(drop=True)
    print(f"[dino] {len(df):,} images on disk", flush=True)

    dino_coll = get_collection(COLLECTION)
    img_coll = get_collection("nga_images")

    # find already-embedded IDs
    existing: set[str] = set()
    total_existing = dino_coll.count()
    for start in range(0, total_existing, 5_000):
        page = dino_coll.get(limit=5_000, offset=start, include=[])
        existing.update(page["ids"])
    if existing:
        df = df[~df["uuid"].isin(existing)].reset_index(drop=True)
        print(f"[dino] skip {len(existing):,} already embedded, {len(df):,} remaining", flush=True)

    if len(df) == 0:
        print("[dino] nothing to do", flush=True)
        return

    done = 0
    for start in range(0, len(df), BATCH):
        chunk = df.iloc[start:start + BATCH]
        valid_idx, vecs = encode_images(chunk["path"].tolist(), batch_size=BATCH)
        if not valid_idx:
            done += len(chunk)
            continue

        uuids = [chunk.iloc[i]["uuid"] for i in valid_idx]

        # fetch metadata from nga_images so results carry full artwork info
        meta_res = img_coll.get(ids=uuids, include=["metadatas"])
        meta_map = dict(zip(meta_res["ids"], meta_res["metadatas"]))
        metadatas = [meta_map.get(u, {}) or {} for u in uuids]

        dino_coll.add(
            ids=uuids,
            embeddings=vecs.tolist(),
            metadatas=metadatas,
        )
        done += len(chunk)
        if (start // BATCH) % 10 == 0:
            print(f"[progress] {done:,}/{len(df):,}", flush=True)

    print(f"[dino] done — {dino_coll.count():,} total in collection", flush=True)


if __name__ == "__main__":
    main()
