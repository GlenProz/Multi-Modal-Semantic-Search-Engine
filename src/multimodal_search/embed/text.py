from __future__ import annotations
from functools import lru_cache
from sentence_transformers import SentenceTransformer
from ..config import EMBED_MODEL


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    return SentenceTransformer(EMBED_MODEL)


def embed(texts: list[str], batch_size: int = 64):
    return get_model().encode(
        texts, batch_size=batch_size, show_progress_bar=True, normalize_embeddings=True
    )
