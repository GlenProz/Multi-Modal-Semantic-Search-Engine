from __future__ import annotations
import chromadb
from ..config import CHROMA_DIR, COLLECTION


def get_collection(name: str = COLLECTION):
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})
