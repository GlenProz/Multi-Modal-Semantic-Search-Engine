"""Predict art movement for every embedded image; update Chroma metadata.

Adds these metadata fields to each nga_images row:
  pred_movement, pred_confidence (top-1)
  pred_alt1, pred_alt1_conf, pred_alt2, pred_alt2_conf
  pred_anachronistic (bool)  -- top-1 movement vs displaydate
"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from multimodal_search.config import IMAGES_DIR, DATA_DIR
from multimodal_search.embed.movement import predict_batch, extract_year, is_plausible
from multimodal_search.store.chroma import get_collection

BATCH = 128
COLLECTION = "nga_images"


def main() -> None:
    df = pd.read_parquet(DATA_DIR / "image_sample.parquet")
    df["path"] = df["uuid"].apply(lambda u: IMAGES_DIR / f"{u}.jpg")
    df = df[df["path"].apply(lambda p: p.exists() and p.stat().st_size > 0)].reset_index(drop=True)

    coll = get_collection(COLLECTION)
    have: set[str] = set()
    for start in range(0, len(df), 1000):
        ids = df["uuid"].iloc[start:start + 1000].tolist()
        got = coll.get(ids=ids, include=["metadatas"])
        for uid, meta in zip(got["ids"], got["metadatas"]):
            if meta and meta.get("pred_movement"):
                have.add(uid)
    if have:
        df = df[~df["uuid"].isin(have)].reset_index(drop=True)
        print(f"[skip] {len(have):,} already classified", flush=True)
    print(f"[classify] {len(df):,} images", flush=True)
    if len(df) == 0:
        return

    for start in range(0, len(df), BATCH):
        chunk = df.iloc[start:start + BATCH]
        preds = predict_batch(chunk["path"].tolist())
        existing = coll.get(ids=chunk["uuid"].tolist(), include=["metadatas"])
        merged = []
        for uid, current, top3, row in zip(
            existing["ids"], existing["metadatas"], preds, chunk.itertuples(index=False)
        ):
            meta = dict(current or {})
            if not top3:
                meta["pred_movement"] = ""
                meta["pred_confidence"] = 0.0
                meta["pred_anachronistic"] = False
            else:
                top, alt1, alt2 = top3[0], top3[1], top3[2]
                year = extract_year(row.displaydate)
                meta["pred_movement"] = top[0]
                meta["pred_confidence"] = round(top[1], 4)
                meta["pred_alt1"] = alt1[0]
                meta["pred_alt1_conf"] = round(alt1[1], 4)
                meta["pred_alt2"] = alt2[0]
                meta["pred_alt2_conf"] = round(alt2[1], 4)
                meta["pred_anachronistic"] = not is_plausible(top[0], year)
            merged.append(meta)
        coll.update(ids=existing["ids"], metadatas=merged)
        if (start // BATCH) % 10 == 0:
            print(f"[progress] {start + len(chunk):,}/{len(df):,}", flush=True)


if __name__ == "__main__":
    main()
