"""open_clip ViT-B/32 image + text encoders, GPU-batched."""
from __future__ import annotations
from functools import lru_cache
from pathlib import Path
import torch
from PIL import Image
import open_clip

MODEL = "ViT-B-32"
PRETRAINED = "laion2b_s34b_b79k"


@lru_cache(maxsize=1)
def _load():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, _, preprocess = open_clip.create_model_and_transforms(MODEL, pretrained=PRETRAINED)
    model = model.to(device).eval()
    tokenizer = open_clip.get_tokenizer(MODEL)
    return model, preprocess, tokenizer, device


@torch.no_grad()
def encode_images(paths: list[Path], batch_size: int = 64) -> tuple[list[int], torch.Tensor]:
    """Return (valid_indices, embeddings).

    valid_indices maps output rows back to input positions — images that fail
    to load or decode are skipped rather than filled with zeros.
    """
    model, preprocess, _, device = _load()
    all_vecs: list[torch.Tensor] = []
    all_valid: list[int] = []

    for start in range(0, len(paths), batch_size):
        batch = paths[start:start + batch_size]
        imgs, valid = [], []
        for j, p in enumerate(batch):
            try:
                imgs.append(preprocess(Image.open(p).convert("RGB")))
                valid.append(start + j)
            except Exception:
                pass
        if not imgs:
            continue
        x = torch.stack(imgs).to(device)
        feats = model.encode_image(x)
        feats = feats / feats.norm(dim=-1, keepdim=True)
        all_vecs.append(feats.cpu())
        all_valid.extend(valid)

    if not all_vecs:
        return [], torch.empty(0, 512)
    return all_valid, torch.cat(all_vecs, dim=0)


@torch.no_grad()
def encode_texts(texts: list[str]) -> torch.Tensor:
    model, _, tokenizer, device = _load()
    toks = tokenizer(texts).to(device)
    feats = model.encode_text(toks)
    feats = feats / feats.norm(dim=-1, keepdim=True)
    return feats.cpu()
