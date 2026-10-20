"""Tests for historical date extraction and movement plausibility."""
from __future__ import annotations

import pytest
from multimodal_search.embed.movement import extract_year, is_plausible


@pytest.mark.parametrize(
    ("date_str", "expected_year"),
    [
        ("1920", 1920),
        ("c. 1275", 1275),
        ("800", 800),
        ("1860s", 1860),
        ("1780s", 1780),
        ("1500-1510", 1500),
        ("1650/1655", 1650),
        ("November 22, 1963", 1963),
        ("c. 490 B.C.", -490),
        ("1500 BCE", -1500),
        ("50 BC", -50),
        ("16th century", 1550),
        ("15th century", 1450),
        ("late 15th - early 16th century", 1500),
        ("nineteenth century", 1850),
        ("4th century B.C.", -350),
        ("3rd/2nd century B.C.", -200),
        ("n.d.", None),
        ("date unknown", None),
        ("", None),
        (None, None),
    ],
)
def test_extract_year(date_str: str | None, expected_year: int | None) -> None:
    assert extract_year(date_str) == expected_year


def test_is_plausible_movements() -> None:
    # Renaissance: 1400-1600 (slack 25 -> 1375-1625)
    assert is_plausible("renaissance", 1500)
    assert is_plausible("renaissance", 1375)
    assert is_plausible("renaissance", 1625)
    assert not is_plausible("renaissance", 1374)
    assert not is_plausible("renaissance", 1626)

    # Ancient & BCE artifacts are caught as anachronistic
    assert not is_plausible("renaissance", -490)
    assert not is_plausible("baroque", -350)
    assert not is_plausible("baroque", 1920)

    # Impressionism: 1860-1890 (slack 25 -> 1835-1915)
    assert is_plausible("impressionism", 1875)
    assert is_plausible("impressionism", 1860)
    assert not is_plausible("impressionism", 1750)

    # Unknown date or movement defaults to plausible (no proof of anachronism)
    assert is_plausible("renaissance", None)
    assert is_plausible("unknown_movement", 1900)
