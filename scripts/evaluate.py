"""Evaluation runner for retrieval metrics (Recall@K, MRR) and movement classifier distribution.

Usage:
  .venv\\Scripts\\python.exe scripts/evaluate.py
  .venv\\Scripts\\python.exe scripts/evaluate.py --samples 50
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from multimodal_search.config import DATA_DIR
from multimodal_search.eval import evaluate_movement_distribution, evaluate_retrieval
from multimodal_search.store.chroma import get_collection


def _format_table(df: pd.DataFrame) -> str:
    try:
        return df.to_markdown(index=False)
    except Exception:
        return df.to_string(index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate multimodal search retrieval & movements")
    parser.add_argument("--samples", type=int, default=50, help="Number of query samples to evaluate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for sampling")
    parser.add_argument("--movement-only", action="store_true", help="Run only movement evaluation")
    parser.add_argument("--retrieval-only", action="store_true", help="Run only retrieval evaluation")
    args = parser.parse_args()

    sample_parquet = DATA_DIR / "image_sample.parquet"
    if not sample_parquet.exists():
        print(f"[error] {sample_parquet} not found. Run scripts/fetch_images.py first.")
        return

    df = pd.read_parquet(sample_parquet)

    # 1. Movement classifier distribution evaluation
    if not args.retrieval_only:
        # Pull latest metadata from nga_images if available
        try:
            coll = get_collection("nga_images")
            all_uids = coll.get(limit=5000, include=["metadatas"])
            if all_uids["metadatas"]:
                meta_df = pd.DataFrame(all_uids["metadatas"])
                if "pred_movement" in meta_df.columns:
                    mv_summary = evaluate_movement_distribution(meta_df)
                    print("\n" + "=" * 60)
                    print("ART MOVEMENT CLASSIFICATION & ANACHRONISM SUMMARY")
                    print("=" * 60)
                    print(_format_table(mv_summary))
        except Exception as e:
            print(f"[movement eval note] {e}")

    # 2. Retrieval evaluation
    if not args.movement_only:
        print("\n" + "=" * 60)
        print(f"RETRIEVAL BENCHMARK (N={args.samples} test queries)")
        print("=" * 60)
        # Sample rows with non-empty assistivetext
        candidates = df[df["assistivetext"].notna() & (df["assistivetext"].str.strip() != "")].copy()
        if len(candidates) > args.samples:
            sample_eval = candidates.sample(n=args.samples, random_state=args.seed)
        else:
            sample_eval = candidates

        print(f"Running queries over {len(sample_eval)} ground-truth artworks...")
        metrics = evaluate_retrieval(sample_eval, query_col="assistivetext", target_col="objectid", k=10)

        # Format as table
        rows = []
        for mode, m in metrics.items():
            rows.append({
                "Mode": mode.capitalize(),
                "Recall@1": f"{m['recall@1']:.1%}",
                "Recall@5": f"{m['recall@5']:.1%}",
                "Recall@10": f"{m['recall@10']:.1%}",
                "MRR": f"{m['mrr']:.3f}",
                "Latency (ms)": f"{m['latency_ms']:.1f}",
            })

        table_df = pd.DataFrame(rows)
        print("\n" + _format_table(table_df))
        print("=" * 60)


if __name__ == "__main__":
    main()
