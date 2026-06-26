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
def encode_images(paths: list[Path], batch_size: int = 64) -> torch.Tensor:
    model, preprocess, _, device = _load()
    out = []
    for i in range(0, len(paths), batch_size):
        batch = paths[i:i + batch_size]
        imgs = []
        for p in batch:
            try:
                imgs.append(preprocess(Image.open(p).convert("RGB")))
            except Exception:
                imgs.append(None)
        keep = [(j, t) for j, t in enumerate(imgs) if t is not None]
        if not keep:
            out.append(torch.zeros(len(batch), 512))
            continue
        idx, tensors = zip(*keep)
        x = torch.stack(tensors).to(device)
        feats = model.encode_image(x)
        feats = feats / feats.norm(dim=-1, keepdim=True)
        full = torch.zeros(len(batch), feats.shape[1], device=device)
        for k, j in enumerate(idx):
            full[j] = feats[k]
        out.append(full.cpu())
    return torch.cat(out, dim=0)


@torch.no_grad()
def encode_texts(texts: list[str]) -> torch.Tensor:
    model, _, tokenizer, device = _load()
    toks = tokenizer(texts).to(device)
    feats = model.encode_text(toks)
    feats = feats / feats.norm(dim=-1, keepdim=True)
    return feats.cpu()
