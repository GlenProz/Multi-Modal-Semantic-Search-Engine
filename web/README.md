# Art Search — web frontend

Custom Next.js UI for the [Multi-Modal Semantic Search
Engine](../README.md).

The heavy ML (CLIP / MiniLM / DINOv2 + the parquet index) runs on a
Hugging Face Space ([`KerChoo/nga-art-search`](https://huggingface.co/spaces/KerChoo/nga-art-search)).
This frontend is a static export deployed to **Cloudflare Pages** at
[`art.anchoranalytics.space`](https://art.anchoranalytics.space) (or `https://nga-art-search-5el.pages.dev`).

Its Cloudflare Pages Functions (`functions/api/*`) proxy queries to the Space, absorbing
cold starts and caching semantic search results at the Cloudflare edge (`X-Cache-Status: HIT` in ~130ms).

## How it works

- **Hybrid search** (`/api/search?mode=hybrid`) → Reciprocal Rank Fusion fusing text metadata + CLIP image pixels.
- **Visual search** (`/api/search?mode=images`) → CLIP text→image over the 63k image index.
- **Metadata search** (`/api/search?mode=text`) → MiniLM over the 145k text index.
- **Find similar** (`/api/similar?id=`) → DINOv2 structural similarity.
- **Surprise me** (`/api/random`) → random artwork, seeds a visual-similarity grid.

Movement badges encode the WikiArt classifier's confidence (🟢 ≥50% /
🟡 ≥30% / 🔴 lower) plus a ⚠️ flag when the predicted movement is
historically anachronistic for the artwork's date.

## Local Dev

```bash
cd web
npm install
npm run build
npx wrangler pages dev out
```

## Deploy to Cloudflare Pages

```bash
cd web
npm run deploy
```
