FROM python:3.11-slim

# HF Spaces run the container as uid 1000.
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    HF_HOME=/home/user/.cache/huggingface \
    DATA_DIR=/home/user/app/data \
    RELEASES_DIR=/home/user/app/data/releases \
    USE_MEMORY_STORE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /home/user/app

# CPU torch first — pin to match the index-build environment, and keep the
# CUDA wheels out (they'd balloon the image and aren't usable on free CPU).
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch==2.11.0 torchvision==0.26.0 \
        --index-url https://download.pytorch.org/whl/cpu

COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Source and the exported parquet index. The NumPy-backed store loads the
# parquet into memory at startup — no ChromaDB, no build-time index build
# (that OOM'd the free build machine for 271k vectors).
COPY --chown=user src ./src
COPY --chown=user data/releases ./data/releases

# Pre-fetch the query-time model weights so cold starts don't re-download.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')" && \
    python -c "import open_clip; open_clip.create_model_and_transforms('ViT-B-32', pretrained='laion2b_s34b_b79k'); open_clip.get_tokenizer('ViT-B-32')"

EXPOSE 7860
CMD ["python", "-m", "uvicorn", "multimodal_search.api.app:app", \
     "--app-dir", "src", "--host", "0.0.0.0", "--port", "7860"]
