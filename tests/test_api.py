"""Tests for FastAPI endpoints and input parameter validations."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from multimodal_search.api.app import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_endpoint(client: TestClient) -> None:
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert "text_count" in data
    assert "image_count" in data
    assert "dino_count" in data


def test_search_text_validation(client: TestClient) -> None:
    # Empty query should fail
    r_empty = client.get("/search/text?q=")
    assert r_empty.status_code == 422

    # k out of bounds (k < 1)
    r_k_low = client.get("/search/text?q=landscape&k=0")
    assert r_k_low.status_code == 422

    # k out of bounds (k > 100)
    r_k_high = client.get("/search/text?q=landscape&k=101")
    assert r_k_high.status_code == 422


def test_search_images_validation(client: TestClient) -> None:
    # Empty query should fail
    r_empty = client.get("/search/images?q=")
    assert r_empty.status_code == 422

    # k bounds
    r_k_low = client.get("/search/images?q=portrait&k=-5")
    assert r_k_low.status_code == 422


def test_search_visual_validation(client: TestClient) -> None:
    # Empty id should fail
    r_empty = client.get("/search/visual?id=")
    assert r_empty.status_code == 422

    # Invalid k should fail
    r_k = client.get("/search/visual?id=some-id&k=0")
    assert r_k.status_code == 422
