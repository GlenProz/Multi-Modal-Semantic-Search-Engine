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

st.set_page_config(page_title="NGA Semantic Search", layout="wide")
st.title("NGA Semantic Search")
st.caption(
    "National Gallery of Art open dataset — semantic search by meaning, not keywords. "
    "Text mode embeds metadata with MiniLM; Image mode embeds pixels with CLIP ViT-B/32."
)

with st.sidebar:
    st.subheader("Controls")
    mode_label = st.radio(
        "Search mode",
        ["Image (CLIP, 55k)", "Text metadata (MiniLM, 145k)"],
        help="Image mode searches the actual pictures. Text mode searches titles/medium/attribution.",
    )
    k = st.slider("Results", 4, 32, 12, step=4)
    cols_per_row = st.slider("Columns", 2, 6, 4)

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
        st.success(f"API ok\nText: {health['text_count']:,}\nImages: {health['image_count']:,}")
    except Exception:
        st.error(f"API down — start uvicorn at {API}")

query = st.text_input(
    "Query",
    "moody European rainy day landscape",
    placeholder="describe what you're looking for...",
)

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
    st.divider()

if query:
    is_image_mode = mode_label.startswith("Image")
    endpoint = "/search/images" if is_image_mode else "/search/text"
    try:
        with st.spinner("Searching..."):
            r = httpx.get(f"{API}{endpoint}", params={"q": query, "k": k}, timeout=60).json()
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
                    pretty = pred.replace("_", " ")
                    st.markdown(f"{dot} **{pretty}** `{conf:.2f}`{warn}")
                    if conf < 0.40 and m.get("pred_alt1"):
                        st.caption(
                            f"or: {m['pred_alt1'].replace('_', ' ')} `{m.get('pred_alt1_conf', 0):.2f}` · "
                            f"{m.get('pred_alt2', '').replace('_', ' ')} `{m.get('pred_alt2_conf', 0):.2f}`"
                        )
    else:
        for hit in results:
            m = hit["metadata"]
            st.markdown(
                f"**{m.get('title') or '(untitled)'}** — {m.get('artists', '')} "
                f"({m.get('date', '')})  ·  score `{hit['score']:.3f}`"
            )
            st.caption(f"{m.get('classification', '')} / {m.get('medium', '')}  ·  id={hit['objectid']}")
            st.divider()
