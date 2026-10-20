"""Evaluation harness for multimodal retrieval and movement plausibility."""
from __future__ import annotations

import time
from typing import Any

import pandas as pd

from ..search.hybrid import hybrid_search
from ..search.query import search as text_search
from ..api.app import search_images


def evaluate_retrieval(
    sample_df: pd.DataFrame,
    query_col: str = "assistivetext",
    target_col: str = "objectid",
    k: int = 10,
) -> dict[str, dict[str, float]]:
    """Evaluate retrieval quality (Recall@1, Recall@5, Recall@10, MRR, latency) across modes.

    Modes evaluated:
      - 'text': MiniLM over metadata & alt-text
      - 'image': CLIP over artwork thumbnails
      - 'hybrid': Reciprocal Rank Fusion over text + image
    """
    valid_samples = sample_df[
        sample_df[query_col].notna() & (sample_df[query_col].str.strip() != "")
    ].copy()

    modes = ["text", "image", "hybrid"]
    metrics: dict[str, dict[str, float]] = {
        m: {"recall@1": 0.0, "recall@5": 0.0, "recall@10": 0.0, "mrr": 0.0, "latency_ms": 0.0}
        for m in modes
    }

    n = len(valid_samples)
    if n == 0:
        return metrics

    for _, row in valid_samples.iterrows():
        query = str(row[query_col]).strip()
        target_id = str(row[target_col]).strip()

        # 1. Text mode
        t0 = time.perf_counter()
        res_text = text_search(query, k=k)
        metrics["text"]["latency_ms"] += (time.perf_counter() - t0) * 1000
        text_ids = [str(r.get("objectid", "")) for r in res_text]
        _accumulate_rank(metrics["text"], text_ids, target_id)

        # 2. Image mode
        t0 = time.perf_counter()
        res_img = search_images(q=query, k=k)
        metrics["image"]["latency_ms"] += (time.perf_counter() - t0) * 1000
        img_ids = [str(r["metadata"].get("objectid", "")) for r in res_img["results"]]
        _accumulate_rank(metrics["image"], img_ids, target_id)

        # 3. Hybrid mode
        t0 = time.perf_counter()
        res_hybrid = hybrid_search(query=query, k=k)
        metrics["hybrid"]["latency_ms"] += (time.perf_counter() - t0) * 1000
        hybrid_ids = [str(r.get("objectid", "")) for r in res_hybrid]
        _accumulate_rank(metrics["hybrid"], hybrid_ids, target_id)

    # Average metrics
    for m in modes:
        metrics[m]["recall@1"] = round(metrics[m]["recall@1"] / n, 4)
        metrics[m]["recall@5"] = round(metrics[m]["recall@5"] / n, 4)
        metrics[m]["recall@10"] = round(metrics[m]["recall@10"] / n, 4)
        metrics[m]["mrr"] = round(metrics[m]["mrr"] / n, 4)
        metrics[m]["latency_ms"] = round(metrics[m]["latency_ms"] / n, 2)

    return metrics


def _accumulate_rank(m_dict: dict[str, float], candidate_ids: list[str], target_id: str) -> None:
    if not target_id or target_id not in candidate_ids:
        return
    rank = candidate_ids.index(target_id) + 1
    if rank == 1:
        m_dict["recall@1"] += 1.0
    if rank <= 5:
        m_dict["recall@5"] += 1.0
    if rank <= 10:
        m_dict["recall@10"] += 1.0
    m_dict["mrr"] += 1.0 / rank


def evaluate_movement_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Analyze movement classification predictions, confidence, and anachronism rates."""
    classified = df[df["pred_movement"].notna() & (df["pred_movement"] != "")].copy()
    if len(classified) == 0:
        return pd.DataFrame()

    total = len(classified)
    summary_rows: list[dict[str, Any]] = []

    for mv, grp in classified.groupby("pred_movement"):
        count = len(grp)
        pct_of_total = (count / total) * 100
        anachronistic_count = grp["pred_anachronistic"].sum() if "pred_anachronistic" in grp else 0
        anach_pct = (anachronistic_count / count) * 100 if count else 0.0
        plausible_pct = 100.0 - anach_pct
        mean_conf = grp["pred_confidence"].mean() if "pred_confidence" in grp else 0.0

        summary_rows.append({
            "movement": mv,
            "count": count,
            "% of total": round(pct_of_total, 1),
            "plausible %": round(plausible_pct, 1),
            "anachronistic %": round(anach_pct, 1),
            "mean confidence": round(mean_conf, 3),
        })

    summary_df = pd.DataFrame(summary_rows).sort_values("count", ascending=False).reset_index(drop=True)
    return summary_df
