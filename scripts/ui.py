"""Streamlit UI. Run AFTER starting the FastAPI server:

  # terminal 1
  .venv\\Scripts\\python.exe -m uvicorn multimodal_search.api.app:app --app-dir src

  # terminal 2
  .venv\\Scripts\\python.exe -m streamlit run scripts/ui.py
"""
from __future__ import annotations
import os
import httpx
import streamlit as st

API = os.getenv("NGA_API", "http://127.0.0.1:8000")

MOVEMENTS = [
    "art_nouveau", "baroque", "expressionism", "impressionism",
    "post_impressionism", "realism", "renaissance", "romanticism", "surrealism",
]

st.set_page_config(page_title="NGA Semantic Search", layout="wide")
st.title("NGA Semantic Search")
st.caption(
    "National Gallery of Art open dataset — semantic search by meaning, not keywords. "
    "Text mode: MiniLM over metadata. Image mode: CLIP ViT-B/32 over pixels. "
    "Visual mode: DINOv2 structural similarity."
)

with st.sidebar:
    st.subheader("Controls")
    mode_label = st.radio(
        "Search mode",
        ["Image (CLIP, 63k)", "Text metadata (MiniLM, 145k)", "Visual similarity (DINOv2, 63k)"],
        help=(
            "Image: finds artworks whose pixels match the meaning of your query.\n"
            "Text: searches titles, medium, attribution, and alt-text.\n"
            "Visual: finds artworks that *look like* a chosen piece — same composition, texture, palette."
        ),
    )
    k = st.slider("Results", 4, 32, 12, step=4)
    cols_per_row = st.slider("Columns", 2, 6, 4)

    is_image_mode = mode_label.startswith("Image")
    is_visual_mode = mode_label.startswith("Visual")
    is_text_mode = mode_label.startswith("Text")

    if is_image_mode:
        st.divider()
        st.caption("**Filter by art movement**")
        selected_movements = st.multiselect(
            "Movements (leave empty for all)",
            options=MOVEMENTS,
            format_func=lambda m: m.replace("_", " ").title(),
        )

    st.divider()
    if st.button("🎲 Random artwork", use_container_width=True):
        try:
            r = httpx.get(f"{API}/random-artwork", timeout=10).json()
            st.session_state["random"] = r
        except Exception as e:
            st.error(f"API error: {e}")

    st.divider()
    try:
        health = httpx.get(f"{API}/health", timeout=5).json()
        dino = health.get("dino_count", 0)
        dino_str = f"\nDINOv2: {dino:,}" if dino else "\nDINOv2: not built yet"
        st.success(
            f"API ok\nText: {health['text_count']:,}\n"
            f"Images: {health['image_count']:,}{dino_str}"
        )
    except Exception:
        st.error(f"API down — start uvicorn at {API}")


# ── random artwork panel ──────────────────────────────────────────────────────

if "random" in st.session_state:
    rec = st.session_state.pop("random")
    m = rec["metadata"]
    st.subheader("🎲 Random")
    c1, c2 = st.columns([1, 2])
    with c1:
        if m.get("iiif"):
            st.image(m["iiif"], use_container_width=True)
    with c2:
        st.markdown(f"### {m.get('title') or '(untitled)'}")
        st.write(m.get("attribution") or "")
        st.write(m.get("date") or "")
        st.caption(f"{m.get('classification', '')} / {m.get('medium', '')}")
        if st.button("🔍 Find visually similar", key="rand_similar"):
            st.session_state["visual_seed_id"] = rec["uuid"]
            st.session_state["visual_seed_title"] = m.get("title", "(untitled)")
    st.divider()


# ── visual-similarity mode ────────────────────────────────────────────────────

if is_visual_mode:
    seed_id = st.session_state.get("visual_seed_id")
    seed_title = st.session_state.get("visual_seed_title", "")

    if seed_id:
        st.info(f"Seed artwork: **{seed_title}** (`{seed_id}`)")
        if st.button("✕ Clear seed"):
            del st.session_state["visual_seed_id"]
            del st.session_state["visual_seed_title"]
            st.rerun()
        try:
            with st.spinner("Searching..."):
                r = httpx.get(f"{API}/search/visual", params={"id": seed_id, "k": k}, timeout=60).json()
        except Exception as e:
            st.error(f"Search failed: {e}")
            st.stop()
        results = r.get("results", [])
        st.write(f"**{len(results)}** visually similar artworks")
        cols = st.columns(cols_per_row)
        for i, hit in enumerate(results):
            m = hit["metadata"]
            with cols[i % cols_per_row]:
                if m.get("iiif"):
                    st.image(m["iiif"], use_container_width=True)
                st.markdown(f"**{m.get('title') or '(untitled)'}**")
                st.caption(
                    f"{m.get('attribution', '')}\n\n"
                    f"{m.get('date', '')} · {m.get('classification', '')}\n\n"
                    f"score: `{hit['score']:.3f}`"
                )
                if st.button("🔍 Find similar", key=f"vs_{hit['uuid']}"):
                    st.session_state["visual_seed_id"] = hit["uuid"]
                    st.session_state["visual_seed_title"] = m.get("title", "(untitled)")
                    st.rerun()
    else:
        st.info(
            "Visual similarity searches for artworks that *look like* a chosen piece — "
            "same composition, texture, or palette, not just the same subject.\n\n"
            "To use it: run an **Image (CLIP)** search or press **🎲 Random artwork**, "
            "then click **🔍 Find visually similar** on any result card."
        )
    st.stop()


# ── text / image (CLIP) search ────────────────────────────────────────────────

query = st.text_input(
    "Query",
    "moody European rainy day landscape",
    placeholder="describe what you're looking for...",
)

if query:
    if is_image_mode:
        params: dict = {"q": query, "k": k}
        if selected_movements:
            params["movements"] = ",".join(selected_movements)
        endpoint = "/search/images"
    else:
        params = {"q": query, "k": k}
        endpoint = "/search/text"

    try:
        with st.spinner("Searching..."):
            r = httpx.get(f"{API}{endpoint}", params=params, timeout=60).json()
    except Exception as e:
        st.error(f"Search failed: {e}")
        st.stop()

    results = r.get("results", [])
    st.write(f"**{len(results)}** results")

    if is_image_mode:
        cols = st.columns(cols_per_row)
        for i, hit in enumerate(results):
            m = hit["metadata"]
            with cols[i % cols_per_row]:
                if m.get("iiif"):
                    st.image(m["iiif"], use_container_width=True)
                st.markdown(f"**{m.get('title') or '(untitled)'}**")
                st.caption(
                    f"{m.get('attribution', '')}\n\n"
                    f"{m.get('date', '')} · {m.get('classification', '')}\n\n"
                    f"score: `{hit['score']:.3f}`"
                )
                pred = m.get("pred_movement")
                if pred:
                    conf = m.get("pred_confidence", 0.0)
                    dot = "🟢" if conf >= 0.75 else ("🟡" if conf >= 0.40 else "🔴")
                    warn = " ⚠️" if m.get("pred_anachronistic") else ""
                    st.markdown(f"{dot} **{pred.replace('_', ' ')}** `{conf:.2f}`{warn}")
                    if conf < 0.40 and m.get("pred_alt1"):
                        st.caption(
                            f"or: {m['pred_alt1'].replace('_', ' ')} `{m.get('pred_alt1_conf', 0):.2f}` · "
                            f"{m.get('pred_alt2', '').replace('_', ' ')} `{m.get('pred_alt2_conf', 0):.2f}`"
                        )
                if st.button("🔍 Find visually similar", key=f"sim_{hit['uuid']}"):
                    st.session_state["visual_seed_id"] = hit["uuid"]
                    st.session_state["visual_seed_title"] = m.get("title", "(untitled)")
                    st.rerun()
    else:
        for hit in results:
            m = hit["metadata"]
            st.markdown(
                f"**{m.get('title') or '(untitled)'}** — {m.get('artists', '')} "
                f"({m.get('date', '')})  ·  score `{hit['score']:.3f}`"
            )
            st.caption(f"{m.get('classification', '')} / {m.get('medium', '')}  ·  id={hit['objectid']}")
            st.divider()
