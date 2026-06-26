"""Embed downloaded images with CLIP → upsert into nga_images collection."""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from multimodal_search.config import IMAGES_DIR, DATA_DIR
from multimodal_search.embed.clip import encode_images
from multimodal_search.store.chroma import get_collection

BATCH = 256
COLLECTION = "nga_images"


def main() -> None:
    df = pd.read_parquet(DATA_DIR / "image_sample.parquet")
    df["path"] = df["uuid"].apply(lambda u: IMAGES_DIR / f"{u}.jpg")
    df = df[df["path"].apply(lambda p: p.exists() and p.stat().st_size > 0)].reset_index(drop=True)
    print(f"embedding {len(df):,} images")

    coll = get_collection(COLLECTION)

    for start in tqdm(range(0, len(df), BATCH), desc="batches"):
        chunk = df.iloc[start:start + BATCH]
        vecs = encode_images(chunk["path"].tolist())
        coll.upsert(
            ids=chunk["uuid"].tolist(),
            embeddings=[v.tolist() for v in vecs],
            documents=chunk["title"].fillna("").astype(str).tolist(),
            metadatas=[
                {
                    "objectid": int(r.objectid),
                    "title": str(r.title) if pd.notna(r.title) else "",
                    "date": str(r.displaydate) if pd.notna(r.displaydate) else "",
                    "attribution": str(r.attribution) if pd.notna(r.attribution) else "",
                    "classification": str(r.classification) if pd.notna(r.classification) else "",
                    "medium": str(r.medium) if pd.notna(r.medium) else "",
                    "iiif": f"https://api.nga.gov/iiif/{r.uuid}/full/!600,600/0/default.jpg",
                }
                for r in chunk.itertuples(index=False)
            ],
        )


if __name__ == "__main__":
    main()
