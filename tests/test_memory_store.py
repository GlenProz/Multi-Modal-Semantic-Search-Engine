"""Tests for in-memory vector store (MemoryCollection)."""
from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from multimodal_search.store.memory import MemoryCollection


@pytest.fixture
def sample_parquet(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    # Set RELEASES_DIR to tmp_path
    monkeypatch.setattr("multimodal_search.store.memory.RELEASES_DIR", tmp_path)

    ids = ["art_1", "art_2", "art_3"]
    # 3 embeddings of dim 4
    embeddings = [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
    ]
    metadatas = [
        {"title": "Mona Lisa", "pred_movement": "renaissance", "year": 1503},
        {"title": "The Night Watch", "pred_movement": "baroque", "year": 1642},
        {"title": "The Starry Night", "pred_movement": "post_impressionism", "year": 1889},
    ]
    documents = [
        "Mona Lisa | Leonardo | Painting | Italian Renaissance portrait",
        "The Night Watch | Rembrandt | Painting | Dutch golden age",
        "The Starry Night | Van Gogh | Painting | Swirling night sky",
    ]

    df = {
        "id": ids,
        "embedding": embeddings,
        "metadata_json": [json.dumps(m) for m in metadatas],
        "document": documents,
    }
    schema = pa.schema([
        pa.field("id", pa.string()),
        pa.field("embedding", pa.list_(pa.float32())),
        pa.field("metadata_json", pa.string()),
        pa.field("document", pa.string()),
    ])
    table = pa.Table.from_pydict(df, schema=schema)
    file_path = tmp_path / "nga_artworks.parquet"
    pq.write_table(table, file_path)
    return file_path


def test_memory_collection_count_and_get(sample_parquet: Path) -> None:
    coll = MemoryCollection("nga_artworks")
    assert coll.count() == 3

    # Test get by id
    res = coll.get(ids=["art_2"], include=["embeddings", "metadatas", "documents"])
    assert res["ids"] == ["art_2"]
    assert res["metadatas"][0]["title"] == "The Night Watch"
    assert "Dutch golden age" in res["documents"][0]
    assert len(res["embeddings"][0]) == 4


def test_memory_collection_query(sample_parquet: Path) -> None:
    coll = MemoryCollection("nga_artworks")

    # Query vector close to art_1 ([1.0, 0.0, 0.0, 0.0])
    q = [0.9, 0.1, 0.0, 0.0]
    res = coll.query(query_embeddings=[q], n_results=2)
    assert len(res["ids"][0]) == 2
    assert res["ids"][0][0] == "art_1"
    assert res["documents"][0][0].startswith("Mona Lisa")
    assert res["distances"][0][0] < 0.1  # High similarity / low distance


def test_memory_collection_filtering(sample_parquet: Path) -> None:
    coll = MemoryCollection("nga_artworks")

    # Exact filter
    q = [0.5, 0.5, 0.5, 0.0]
    res = coll.query(query_embeddings=[q], n_results=10, where={"pred_movement": "baroque"})
    assert res["ids"][0] == ["art_2"]
    assert res["metadatas"][0][0]["title"] == "The Night Watch"

    # $in filter
    res_in = coll.query(
        query_embeddings=[q],
        n_results=10,
        where={"pred_movement": {"$in": ["renaissance", "post_impressionism"]}},
    )
    assert set(res_in["ids"][0]) == {"art_1", "art_3"}


def test_memory_collection_bounds_and_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("multimodal_search.store.memory.RELEASES_DIR", tmp_path)

    # Unknown collection raises ValueError
    with pytest.raises(ValueError, match="Unknown collection"):
        MemoryCollection("invalid_name")

    # Missing file raises FileNotFoundError
    with pytest.raises(FileNotFoundError, match="Parquet file for collection"):
        MemoryCollection("nga_artworks")
