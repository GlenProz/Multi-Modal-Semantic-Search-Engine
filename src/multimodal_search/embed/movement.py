"""WikiArt art-movement classifier (HF ViT) + date-range plausibility check."""
from __future__ import annotations
import re
from functools import lru_cache
from pathlib import Path
import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification, ViTImageProcessor

MODEL_ID = "oschamp/vit-artworkclassifier"
PROCESSOR_FALLBACK = "google/vit-base-patch16-224"

MOVEMENT_DATES: dict[str, tuple[int, int]] = {
    "art_nouveau": (1890, 1910),
    "baroque": (1600, 1750),
    "expressionism": (1905, 1925),
    "impressionism": (1860, 1890),
    "post_impressionism": (1886, 1905),
    "realism": (1840, 1880),
    "renaissance": (1400, 1600),
    "romanticism": (1800, 1850),
    "surrealism": (1924, 1955),
}

_BCE_EXPLICIT_RE = re.compile(r"\b(?:b\.?c\.?e?|b\.?c\.?)\b", re.IGNORECASE)
_CENTURY_INDICATOR_RE = re.compile(r"\bcen(?:tury|turies|\.)?\b", re.IGNORECASE)
_ORDINAL_RE = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)\b", re.IGNORECASE)
_CENTURY_WORD_RE = re.compile(
    r"\b(twelfth|thirteenth|fourteenth|fifteenth|sixteenth|seventeenth|eighteenth|nineteenth|twentieth)[-\s]+cen",
    re.IGNORECASE,
)
_WORD_TO_CENTURY = {
    "twelfth": 12,
    "thirteenth": 13,
    "fourteenth": 14,
    "fifteenth": 15,
    "sixteenth": 16,
    "seventeenth": 17,
    "eighteenth": 18,
    "nineteenth": 19,
    "twentieth": 20,
}
_YEAR_BCE_RE = re.compile(r"\b(\d{1,4})\s*(?:b\.?c\.?e?|b\.?c\.?)\b", re.IGNORECASE)
_YEAR_RE = re.compile(r"\b(\d{3,4})s?\b")


def extract_year(s: str | None) -> int | None:
    """Extract a representative historical year from display date strings.

    Supports:
      - Standard 3-4 digit years (e.g. "1920", "c. 1275", "800")
      - Decades (e.g. "1860s" -> 1860)
      - Century notation (e.g. "15th century" -> 1450, "nineteenth century" -> 1850)
      - BCE dates as negative years (e.g. "c. 490 B.C." -> -490, "4th century B.C." -> -350)
    """
    if not s:
        return None
    s_str = str(s).strip()
    is_bce = bool(_BCE_EXPLICIT_RE.search(s_str))

    # 1. Explicit BCE year: "490 B.C.", "50 BCE"
    m_bce = _YEAR_BCE_RE.search(s_str)
    if m_bce:
        return -int(m_bce.group(1))

    # 2. Century notation (digits or words, including composite spans)
    cents: list[int] = []
    if _CENTURY_INDICATOR_RE.search(s_str):
        cents.extend(int(c) for c in _ORDINAL_RE.findall(s_str))
    for w in _CENTURY_WORD_RE.findall(s_str):
        cents.append(_WORD_TO_CENTURY[w.lower()])
    if cents:
        avg_c = sum(cents) / len(cents)
        yr = int((avg_c - 1) * 100 + 50)
        return -yr if is_bce else yr

    # 3. Standard 3-4 digit years and decades: "1920", "1860s", "c. 1275", "800"
    m_yr = _YEAR_RE.search(s_str)
    if m_yr:
        yr = int(m_yr.group(1))
        if 1 <= yr <= 2100:
            return -yr if is_bce else yr

    return None


def is_plausible(movement: str, year: int | None, slack: int = 25) -> bool:
    """True when artwork year falls inside (or near) the movement's historical span."""
    if year is None or movement not in MOVEMENT_DATES:
        return True
    lo, hi = MOVEMENT_DATES[movement]
    return (lo - slack) <= year <= (hi + slack)


@lru_cache(maxsize=1)
def _load():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    try:
        proc = AutoImageProcessor.from_pretrained(MODEL_ID)
    except Exception:
        proc = ViTImageProcessor.from_pretrained(PROCESSOR_FALLBACK)
    model = AutoModelForImageClassification.from_pretrained(MODEL_ID).to(device).eval()
    return proc, model, device, model.config.id2label


@torch.no_grad()
def predict_batch(paths: list[Path], batch_size: int = 64) -> list[list[tuple[str, float]]]:
    """Return top-3 (label, confidence) per image. Returns [] for any image that fails to load."""
    proc, model, device, id2label = _load()
    out: list[list[tuple[str, float]]] = []
    for i in range(0, len(paths), batch_size):
        batch = paths[i:i + batch_size]
        imgs, idx = [], []
        for j, p in enumerate(batch):
            try:
                imgs.append(Image.open(p).convert("RGB"))
                idx.append(j)
            except Exception:
                pass
        results: list[list[tuple[str, float]]] = [[] for _ in batch]
        if imgs:
            inputs = proc(images=imgs, return_tensors="pt").to(device)
            logits = model(**inputs).logits
            probs = torch.softmax(logits, dim=-1)
            top = torch.topk(probs, k=3, dim=-1)
            for k, j in enumerate(idx):
                results[j] = [
                    (id2label[top.indices[k, t].item()], float(top.values[k, t]))
                    for t in range(3)
                ]
        out.extend(results)
    return out
