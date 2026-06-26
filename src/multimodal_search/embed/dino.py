"""DINOv2 image encoder for visual-structure similarity search.

Distinct from CLIP: DINOv2 captures composition, texture, and spatial layout
rather than semantic meaning — finds artworks that *look* like the query image.
"""
from __future__ import annotations
from functools import lru_cache
from pathlib import Path

import torch
import torch.nn.functional as F
from PIL import Image
from transformers import AutoImageProcessor, AutoModel

MODEL_ID = "facebook/dinov2-base"  # 768-d CLS token, 86M params


@lru_cache(maxsize=1)
def _load():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    proc = AutoImageProcessor.from_pretrained(MODEL_ID)
    model = AutoModel.from_pretrained(MODEL_ID).to(device).eval()
    return proc, model, device


@torch.no_grad()
def encode_images(paths: list[Path], batch_size: int = 64) -> tuple[list[int], torch.Tensor]:
    """Return (valid_indices, embeddings).

    valid_indices maps output rows back to input positions — images that fail
    to load are skipped rather than filled with zeros, so callers know which
    paths produced vectors.
    """
    proc, model, device = _load()
    all_vecs: list[torch.Tensor] = []
    all_valid: list[int] = []

    for start in range(0, len(paths), batch_size):
        batch = paths[start:start + batch_size]
        imgs, valid = [], []
        for j, p in enumerate(batch):
            try:
                imgs.append(Image.open(p).convert("RGB"))
                valid.append(start + j)
            except Exception:
                pass
        if not imgs:
            continue
        inputs = proc(images=imgs, return_tensors="pt").to(device)
        out = model(**inputs)
        feats = out.last_hidden_state[:, 0, :]      # CLS token → [B, 768]
        feats = F.normalize(feats, dim=-1)
        all_vecs.append(feats.cpu())
        all_valid.extend(valid)

    if not all_vecs:
        return [], torch.empty(0, 768)
    return all_valid, torch.cat(all_vecs, dim=0)
