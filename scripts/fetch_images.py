"""Async-download a sample of NGA IIIF thumbnails to data/images/.

Usage: python scripts/fetch_images.py [N=5000] [--seed SEED]

Skips UUIDs already present in image_sample.parquet so repeated runs grow the
sample instead of repeating it.
"""
from __future__ import annotations
import asyncio
import sys
from pathlib import Path
import pandas as pd
import httpx
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from multimodal_search.config import IMAGES_DIR
from multimodal_search.ingest.images import sample_image_rows

CONCURRENCY = 16
TIMEOUT = 30.0
SAMPLE_PARQUET = IMAGES_DIR.parent / "image_sample.parquet"


async def _fetch(client: httpx.AsyncClient, sem: asyncio.Semaphore, uuid: str, url: str, pbar) -> tuple[str, bool]:
    dest = IMAGES_DIR / f"{uuid}.jpg"
    if dest.exists() and dest.stat().st_size > 0:
        pbar.update(1)
        return uuid, True
    async with sem:
        try:
            r = await client.get(url, timeout=TIMEOUT, follow_redirects=True)
            r.raise_for_status()
            dest.write_bytes(r.content)
            ok = True
        except Exception:
            ok = False
        pbar.update(1)
        return uuid, ok


async def _run(df) -> dict[str, bool]:
    sem = asyncio.Semaphore(CONCURRENCY)
    results: dict[str, bool] = {}
    async with httpx.AsyncClient(headers={"User-Agent": "nga-semantic-search/0.1"}) as client:
        with tqdm(total=len(df), desc="download") as pbar:
            tasks = [_fetch(client, sem, r.uuid, r.iiifthumburl, pbar) for r in df.itertuples()]
            for fut in asyncio.as_completed(tasks):
                uuid, ok = await fut
                results[uuid] = ok
    return results


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    seed = 42
    if "--seed" in sys.argv:
        seed = int(sys.argv[sys.argv.index("--seed") + 1])

    existing = pd.read_parquet(SAMPLE_PARQUET) if SAMPLE_PARQUET.exists() else None
    exclude = set(existing["uuid"]) if existing is not None else set()
    print(f"existing sample: {len(exclude):,} rows; requesting {n:,} new")

    new_df = sample_image_rows(n, seed=seed, exclude=exclude)
    print(f"sampled {len(new_df):,} new rows -> {IMAGES_DIR}")
    results = asyncio.run(_run(new_df))
    ok = sum(results.values())
    print(f"downloaded {ok:,}/{len(new_df):,} (failed: {len(new_df) - ok})")

    combined = pd.concat([existing, new_df], ignore_index=True) if existing is not None else new_df
    combined.to_parquet(SAMPLE_PARQUET, index=False)
    print(f"total sample: {len(combined):,} rows")


if __name__ == "__main__":
    main()
