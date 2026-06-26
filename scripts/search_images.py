"""CLI: text query → CLIP text encoder → search nga_images collection.

Usage: python scripts/search_images.py "moody rainy landscape" [k=10]
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from multimodal_search.embed.clip import encode_texts
from multimodal_search.store.chroma import get_collection


def main() -> None:
    if len(sys.argv) < 2:
        print('usage: python scripts/search_images.py "<query>" [k]')
        sys.exit(1)
    q = sys.argv[1]
    k = int(sys.argv[2]) if len(sys.argv) > 2 else 10

    vec = encode_texts([q])[0].tolist()
    res = get_collection("nga_images").query(query_embeddings=[vec], n_results=k)

    for i, uid in enumerate(res["ids"][0], 1):
        m = res["metadatas"][0][i - 1]
        d = res["distances"][0][i - 1]
        print(f"{i:>2}. [{1 - d:.3f}] {m.get('title')} — {m.get('attribution')} ({m.get('date')})")
        print(f"     {m.get('classification')} / {m.get('medium')}")
        print(f"     {m.get('iiif')}")


if __name__ == "__main__":
    main()
