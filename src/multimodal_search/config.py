import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(os.getenv("DATA_DIR", "./data")).resolve()
RAW_DIR = DATA_DIR / "raw"
CHROMA_DIR = Path(os.getenv("CHROMA_DIR", str(DATA_DIR / "chroma"))).resolve()
IMAGES_DIR = DATA_DIR / "images"

NGA_DATA_BASE = os.getenv(
    "NGA_DATA_BASE",
    "https://raw.githubusercontent.com/NationalGalleryOfArt/opendata/main/data",
)
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
COLLECTION = os.getenv("COLLECTION", "nga_artworks")

for d in (RAW_DIR, CHROMA_DIR, IMAGES_DIR):
    d.mkdir(parents=True, exist_ok=True)
