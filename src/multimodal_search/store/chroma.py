from __future__ import annotations
import os
from ..config import CHROMA_DIR, COLLECTION

# The hosted Space sets USE_MEMORY_STORE and uses the NumPy-backed store
# (no chromadb dependency, no build-time index). Local dev leaves it unset
# and uses real ChromaDB exactly as before.
if os.getenv("USE_MEMORY_STORE"):
    from .memory import get_collection  # noqa: F401
else:
    import chromadb

    def get_collection(name: str = COLLECTION):
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        return client.get_or_create_collection(
            name=name, metadata={"hnsw:space": "cosine"}
        )
