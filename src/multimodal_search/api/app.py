from fastapi import FastAPI
from ..search.query import search

app = FastAPI(title="NGA Semantic Search")


@app.get("/search")
def search_endpoint(q: str, k: int = 10):
    return {"query": q, "results": search(q, k=k)}
