"""Import pre-built index from parquet files (downloaded from the GitHub Release).

Downloads the parquet files from the latest GitHub Release if they don't already
exist in data/releases/, then loads them into local ChromaDB.

Usage:
  # download manually from the GitHub Releases page, place in data/releases/, then:
  .venv\\Scripts\\python.exe scripts\\import_index.py

  # or pass --download to fetch automatically (requires internet):
  .venv\\Scripts\\python.exe scripts\\import_index.py --download
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from multimodal_search.config import DATA_DIR
from multimodal_search.store.chroma import get_collection

RELEASES_DIR = DATA_DIR / "releases"
RELEASES_DIR.mkdir(parents=True, exist_ok=True)

RELEASE_URL = (
    "https://github.com/GlenProz/Multi-Modal-Semantic-Search-Engine"
    "/releases/latest/download"
)
FILES = ["nga_artworks.parquet", "nga_images.parquet"]

BATCH = 2_000


def download_files() -> None:
    import httpx
    for fname in FILES:
        dest = RELEASES_DIR / fname
        if dest.exists():
            print(f"[skip] {fname} already present", flush=True)
            continue
        url = f"{RELEASE_URL}/{fname}"
        print(f"[download] {url}", flush=True)
        with httpx.stream("GET", url, follow_redirects=True, timeout=300) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            done = 0
            with open(dest, "wb") as f:
                for chunk in r.iter_bytes(chunk_size=1 << 20):
                    f.write(chunk)
                    done += len(chunk)
                    if total:
                        print(f"  {done / 1_048_576:.1f} / {total / 1_048_576:.1f} MB", flush=True)
        print(f"  saved {dest}", flush=True)


def import_collection(name: str, parquet_path: Path) -> None:
    if not parquet_path.exists():
        raise FileNotFoundError(
            f"{parquet_path} not found — run with --download or place the file manually."
        )

    table = pq.read_table(parquet_path)
    ids = table["id"].to_pylist()
    embeddings = [list(e) for e in table["embedding"].to_pylist()]
    metadatas = [json.loads(m) for m in table["metadata_json"].to_pylist()]

    coll = get_collection(name)
    existing = set(coll.get(ids=ids[:1], include=[])["ids"])  # quick probe
    if coll.count() > 0:
        print(f"[import] {name}: collection already has {coll.count():,} rows — skipping", flush=True)
        return

    total = len(ids)
    print(f"[import] {name}: {total:,} rows", flush=True)
    for start in range(0, total, BATCH):
        end = min(start + BATCH, total)
        coll.add(
            ids=ids[start:end],
            embeddings=embeddings[start:end],
            metadatas=metadatas[start:end],
        )
        print(f"  {end:,}/{total:,}", flush=True)
    print(f"[import] {name}: done", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--download", action="store_true", help="Fetch parquet files from GitHub Release")
    args = parser.parse_args()

    if args.download:
        download_files()

    import_collection("nga_artworks", RELEASES_DIR / "nga_artworks.parquet")
    import_collection("nga_images",   RELEASES_DIR / "nga_images.parquet")
    print("[import] all done — run uvicorn + streamlit to start searching", flush=True)


if __name__ == "__main__":
    main()
