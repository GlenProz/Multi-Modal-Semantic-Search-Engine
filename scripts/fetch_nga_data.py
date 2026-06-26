"""Download NGA opendata CSVs into data/raw/."""
from __future__ import annotations
import sys
from pathlib import Path
import requests
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from multimodal_search.config import NGA_DATA_BASE, RAW_DIR

TABLES = [
    "objects", "constituents", "objects_constituents",
    "locations", "objects_dimensions", "objects_terms",
    "media_items", "media_relationships", "published_images",
]


def fetch(name: str) -> None:
    url = f"{NGA_DATA_BASE}/{name}.csv"
    dest = RAW_DIR / f"{name}.csv"
    if dest.exists():
        print(f"skip {name} (exists)")
        return
    r = requests.get(url, stream=True, timeout=60)
    r.raise_for_status()
    total = int(r.headers.get("content-length", 0))
    with open(dest, "wb") as f, tqdm(total=total, unit="B", unit_scale=True, desc=name) as pb:
        for chunk in r.iter_content(chunk_size=1 << 16):
            f.write(chunk)
            pb.update(len(chunk))


if __name__ == "__main__":
    for t in TABLES:
        try:
            fetch(t)
        except Exception as e:
            print(f"FAIL {t}: {e}")
