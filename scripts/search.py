"""CLI: python scripts/search.py "moody rainy landscapes" [k]"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from multimodal_search.search.query import search


def main() -> None:
    if len(sys.argv) < 2:
        print('usage: python scripts/search.py "<query>" [k]')
        sys.exit(1)
    q = sys.argv[1]
    k = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    for i, r in enumerate(search(q, k=k), 1):
        m = r["metadata"]
        print(f"{i:>2}. [{r['score']:.3f}] {m.get('title')} — {m.get('artists')} ({m.get('date')})")
        print(f"     id={r['objectid']}  {m.get('classification')} / {m.get('medium')}")


if __name__ == "__main__":
    main()
