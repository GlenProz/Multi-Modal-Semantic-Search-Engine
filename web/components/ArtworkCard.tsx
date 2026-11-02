"use client";

import type { ImageResult } from "@/lib/api";
import { MovementBadge } from "./MovementBadge";

type Props = {
  result: ImageResult;
  onFindSimilar: (uuid: string) => void;
};

// Swap the IIIF thumbnail size up for a larger "view full size" link.
function fullSizeUrl(iiif?: string): string {
  if (!iiif) return "";
  return iiif.replace(/\/full\/[^/]+\//, "/full/!1600,1600/");
}

export function getMatchMetrics(result: ImageResult) {
  const isHybrid = result.text_score != null || result.image_score != null;

  if (isHybrid) {
    // Theoretical max RRF score for rank-1 in both text and visual candidate lists:
    // w_text / (60 + 1) + w_image / (60 + 1) = 0.5/61 + 0.5/61 = 1/61 ≈ 0.016393
    const maxRrf = 1.0 / 61.0;
    const rawNormalized = Math.round((result.score / maxRrf) * 100);
    const percent = Math.min(99, Math.max(1, rawNormalized));

    const breakdown: string[] = [];
    if (result.image_score != null) {
      breakdown.push(`Visual (CLIP): ${Math.round(result.image_score * 100)}% visual similarity`);
    } else {
      breakdown.push(`Visual (CLIP): No top-30 visual match`);
    }
    if (result.text_score != null) {
      breakdown.push(`Catalog (MiniLM): ${Math.round(result.text_score * 100)}% metadata match`);
    } else {
      breakdown.push(`Catalog (MiniLM): No direct catalog keyword match`);
    }

    return {
      percent,
      label: `${percent}% match`,
      title: `Hybrid RRF Match: ${percent}%\n• Fused RRF Score: ${result.score.toFixed(4)}\n• ${breakdown.join("\n• ")}\n\nRanked via Reciprocal Rank Fusion combining CLIP pixel embeddings and MiniLM archival catalog text.`,
      isHybrid: true,
      hasImageMatch: result.image_score != null,
      hasTextMatch: result.text_score != null,
    };
  }

  // Pure CLIP visual search or single-score
  const percent = Math.min(99, Math.max(1, Math.round(result.score * 100)));
  return {
    percent,
    label: `${percent}% match`,
    title: `Visual Semantic Similarity: ${percent}%\nCosine similarity between your search query and artwork pixel embeddings (OpenAI CLIP ViT-B/32).`,
    isHybrid: false,
    hasImageMatch: true,
    hasTextMatch: false,
  };
}

export function ArtworkCard({ result, onFindSimilar }: Props) {
  const m = result.metadata || {};
  const hasImage = Boolean(m.iiif);
  const fullUrl = fullSizeUrl(m.iiif);
  const metrics = getMatchMetrics(result);

  return (
    <div className="group flex flex-col overflow-hidden rounded-xl border border-stone-200/80 bg-white artwork-matte transition-all duration-300 hover:-translate-y-1 hover:border-amber-700/40 hover:shadow-lg dark:border-stone-800 dark:bg-stone-900/90 dark:hover:border-amber-500/30">
      <div className="relative block aspect-square overflow-hidden bg-stone-100 dark:bg-stone-950">
        {hasImage ? (
          <a
            href={fullUrl}
            target="_blank"
            rel="noopener noreferrer"
            title="Open high-resolution IIIF image"
            className="block h-full w-full"
          >
            {/* eslint-disable-next-line @next/next/no-img-element -- NGA IIIF host */}
            <img
              src={m.iiif}
              alt={m.title || "Artwork"}
              loading="lazy"
              className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.04]"
            />
          </a>
        ) : (
          <div className="flex h-full w-full flex-col items-center justify-center bg-stone-100/70 p-4 text-center dark:bg-stone-950/70">
            <span className="text-4xl opacity-30 select-none">🏛️</span>
            <span className="mt-2 font-serif text-xs italic text-stone-600 dark:text-stone-400">
              Archival Catalog Record
            </span>
            <span className="mt-0.5 text-[10px] text-stone-400 dark:text-stone-500">
              No digital scan in NGA image set
            </span>
          </div>
        )}

        {/* Top badges */}
        <div className="absolute inset-x-2 top-2 flex items-center justify-between gap-1">
          <span
            title={metrics.title}
            className="pointer-events-auto cursor-help rounded-full bg-black/75 px-2.5 py-0.5 text-[10px] font-medium tracking-wide text-white/95 backdrop-blur-sm transition-colors hover:bg-black"
          >
            {metrics.label}
          </span>
          {hasImage && (
            <a
              href={fullUrl}
              target="_blank"
              rel="noopener noreferrer"
              title="View full resolution in new tab"
              className="pointer-events-auto flex h-6 w-6 items-center justify-center rounded-full bg-black/60 text-[11px] text-white opacity-0 transition-opacity hover:bg-black/90 group-hover:opacity-100"
            >
              ↗
            </a>
          )}
        </div>
      </div>

      <div className="flex flex-1 flex-col justify-between p-4 gap-3">
        <div className="flex flex-col gap-1">
          <h3 className="gallery-serif line-clamp-2 text-base font-semibold leading-snug text-stone-900 transition-colors group-hover:text-amber-900 dark:text-stone-100 dark:group-hover:text-amber-400">
            {m.title || "Untitled"}
          </h3>
          <p className="line-clamp-1 text-xs text-stone-600 dark:text-stone-400">
            <span className="font-medium text-stone-800 dark:text-stone-200">
              {m.attribution || m.artists || "Unknown Artist"}
            </span>
            {m.date ? ` · ${m.date}` : ""}
          </p>
          {m.medium && (
            <p className="line-clamp-1 text-[11px] italic text-stone-500 dark:text-stone-500">
              {m.medium}
            </p>
          )}
        </div>

        <div className="flex flex-col gap-2.5 pt-1 border-t border-stone-100 dark:border-stone-800/80">
          {m.pred_movement ? (
            <MovementBadge
              movement={m.pred_movement}
              confidence={m.pred_confidence}
              anachronistic={m.pred_anachronistic}
            />
          ) : null}

          {result.uuid ? (
            <button
              onClick={() => onFindSimilar(result.uuid)}
              className="flex items-center justify-center gap-1.5 rounded-lg border border-stone-200 bg-stone-50/80 px-3 py-1.5 text-xs font-medium text-stone-700 transition-all hover:border-amber-600/50 hover:bg-amber-50/60 hover:text-amber-900 dark:border-stone-800 dark:bg-stone-800/50 dark:text-stone-300 dark:hover:border-amber-500/40 dark:hover:bg-amber-950/30 dark:hover:text-amber-300"
            >
              <span>✦</span>
              <span>Find visually similar</span>
            </button>
          ) : (
            <div className="flex items-center justify-center py-1 text-[11px] italic text-stone-400 dark:text-stone-500">
              Archival metadata match
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
