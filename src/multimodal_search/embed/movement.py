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

_YEAR_RE = re.compile(r"\b(1[3-9]\d{2}|20\d{2})\b")


def extract_year(s: str | None) -> int | None:
    if not s:
        return None
    m = _YEAR_RE.search(str(s))
    return int(m.group(1)) if m else None


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
