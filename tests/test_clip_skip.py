"""Tests for CLIP image encoding and corrupt-image skipping."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import torch
from PIL import Image

from multimodal_search.embed.clip import encode_images


def test_encode_images_skips_corrupt_files(tmp_path: Path, monkeypatch) -> None:
    # Create 1 valid image and 1 corrupt 0-byte file
    valid_img = tmp_path / "valid.jpg"
    Image.new("RGB", (10, 10), color="blue").save(valid_img)

    corrupt_img = tmp_path / "corrupt.jpg"
    corrupt_img.write_bytes(b"not an image file")

    missing_img = tmp_path / "missing.jpg"

    # Mock _load() so test runs instantaneously on CPU without loading heavy weights
    dummy_model = MagicMock()
    dummy_model.encode_image.side_effect = lambda x: torch.ones(x.shape[0], 512)
    dummy_preprocess = lambda img: torch.zeros(3, 224, 224)
    dummy_tokenizer = MagicMock()
    monkeypatch.setattr(
        "multimodal_search.embed.clip._load",
        lambda: (dummy_model, dummy_preprocess, dummy_tokenizer, "cpu"),
    )

    paths = [corrupt_img, valid_img, missing_img]
    valid_idx, vecs = encode_images(paths, batch_size=2)

    # Only index 1 (valid_img) should be present
    assert valid_idx == [1]
    assert vecs.shape == (1, 512)


def test_encode_images_all_corrupt(tmp_path: Path, monkeypatch) -> None:
    corrupt_img = tmp_path / "corrupt.jpg"
    corrupt_img.write_bytes(b"garbage")

    dummy_model = MagicMock()
    dummy_preprocess = lambda img: torch.zeros(3, 224, 224)
    dummy_tokenizer = MagicMock()
    monkeypatch.setattr(
        "multimodal_search.embed.clip._load",
        lambda: (dummy_model, dummy_preprocess, dummy_tokenizer, "cpu"),
    )

    valid_idx, vecs = encode_images([corrupt_img])
    assert valid_idx == []
    assert vecs.shape == (0, 512)
