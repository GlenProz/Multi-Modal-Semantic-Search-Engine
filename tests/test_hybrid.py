"""Tests for hybrid search (RRF) and evaluation benchmark functions."""
from __future__ import annotations

from unittest.mock import MagicMock

import pandas as pd
import pytest

from multimodal_search.eval.benchmark import evaluate_movement_distribution, _accumulate_rank
from multimodal_search.search.hybrid import hybrid_search


def test_accumulate_rank_metrics() -> None:
    m = {"recall@1": 0.0, "recall@5": 0.0, "recall@10": 0.0, "mrr": 0.0}

    # Rank 1 hit
    _accumulate_rank(m, ["target", "other1", "other2"], "target")
    assert m["recall@1"] == 1.0
    assert m["recall@5"] == 1.0
    assert m["recall@10"] == 1.0
    assert m["mrr"] == 1.0

    # Rank 3 hit
    _accumulate_rank(m, ["other1", "other2", "target2"], "target2")
    assert m["recall@1"] == 1.0
    assert m["recall@5"] == 2.0
    assert m["recall@10"] == 2.0
    assert abs(m["mrr"] - (1.0 + 1.0 / 3)) < 1e-5

    # Miss (not in top 10)
    _accumulate_rank(m, ["other"] * 10, "missed_target")
    assert m["recall@1"] == 1.0
    assert m["recall@5"] == 2.0
    assert m["recall@10"] == 2.0


def test_evaluate_movement_distribution() -> None:
    data = [
        {"pred_movement": "renaissance", "pred_confidence": 0.8, "pred_anachronistic": False},
        {"pred_movement": "renaissance", "pred_confidence": 0.6, "pred_anachronistic": True},
        {"pred_movement": "baroque", "pred_confidence": 0.9, "pred_anachronistic": False},
        {"pred_movement": "baroque", "pred_confidence": 0.7, "pred_anachronistic": False},
    ]
    df = pd.DataFrame(data)
    summary = evaluate_movement_distribution(df)

    assert len(summary) == 2
    ren = summary[summary["movement"] == "renaissance"].iloc[0]
    assert ren["count"] == 2
    assert ren["% of total"] == 50.0
    assert ren["plausible %"] == 50.0
    assert ren["anachronistic %"] == 50.0
    assert ren["mean confidence"] == 0.7


def test_hybrid_search_rrf_scoring(monkeypatch: pytest.MonkeyPatch) -> None:
    # Mock text search returning objectid '100' (rank 1) and '200' (rank 2)
    mock_text = [
        {"objectid": "100", "score": 0.9, "metadata": {"title": "Art 100"}},
        {"objectid": "200", "score": 0.8, "metadata": {"title": "Art 200"}},
    ]
    monkeypatch.setattr(
        "multimodal_search.search.hybrid.text_search",
        lambda q, k: mock_text,
    )

    # Mock CLIP text encoder
    dummy_vec = MagicMock()
    dummy_vec.tolist.return_value = [0.1] * 512
    monkeypatch.setattr(
        "multimodal_search.search.hybrid.encode_texts",
        lambda texts: [dummy_vec],
    )

    # Mock image collection returning '200' (rank 1) and '300' (rank 2)
    mock_img_coll = MagicMock()
    mock_img_coll.query.return_value = {
        "ids": [["uuid_200", "uuid_300"]],
        "distances": [[0.2, 0.4]],
        "metadatas": [[
            {"objectid": "200", "title": "Art 200", "pred_movement": "baroque", "pred_anachronistic": False},
            {"objectid": "300", "title": "Art 300", "pred_movement": "realism", "pred_anachronistic": True},
        ]],
    }
    monkeypatch.setattr(
        "multimodal_search.search.hybrid.get_collection",
        lambda name: mock_img_coll,
    )

    # Hybrid search
    results = hybrid_search("test query", k=3, rrf_k=60)
    assert len(results) == 3

    # Object '200' appears in both text (rank 2) and image (rank 1), so it should rank first
    top = results[0]
    assert top["objectid"] == "200"
    assert top["text_score"] == 0.8
    assert top["image_score"] == 0.8
    assert top["uuid"] == "uuid_200"

    # Test exclude_anachronistic=True filters out '300'
    filtered = hybrid_search("test query", k=3, exclude_anachronistic=True)
    obj_ids = [r["objectid"] for r in filtered]
    assert "300" not in obj_ids
    assert "200" in obj_ids
    assert "100" in obj_ids
