"use client";

import type { ImageResult } from "@/lib/api";
import { MovementBadge } from "./MovementBadge";

type Props = {
  result: ImageResult;
  onFindSimilar: (uuid: string) => void;
};

// Swap the IIIF thumbnail size up for a larger "view full size" link.
function fullSizeUrl(iiif: string): string {
  return iiif.replace(/\/full\/[^/]+\//, "/full/!1600,1600/");
}

export function ArtworkCard({ result, onFindSimilar }: Props) {
  const m = result.metadata;
  return (
    <div className="group flex flex-col overflow-hidden rounded-xl border border-stone-200/80 bg-white artwork-matte transition-all duration-300 hover:-translate-y-1 hover:border-amber-700/40 hover:shadow-lg dark:border-stone-800 dark:bg-stone-900/90 dark:hover:border-amber-500/30">
      <div className="relative block aspect-square overflow-hidden bg-stone-100 dark:bg-stone-950">
        <a
          href={fullSizeUrl(m.iiif)}
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

        {/* Top badges */}
        <div className="pointer-events-none absolute inset-x-2 top-2 flex items-center justify-between gap-1">
          <span className="rounded-full bg-black/60 px-2 py-0.5 text-[10px] font-medium tracking-wide text-white/90 backdrop-blur-sm">
            {Math.round(result.score * 100)}% match
          </span>
          <a
            href={fullSizeUrl(m.iiif)}
            target="_blank"
            rel="noopener noreferrer"
            title="View full resolution in new tab"
            className="pointer-events-auto flex h-6 w-6 items-center justify-center rounded-full bg-black/60 text-[11px] text-white opacity-0 transition-opacity hover:bg-black/90 group-hover:opacity-100"
          >
            ↗
          </a>
        </div>
      </div>

      <div className="flex flex-1 flex-col justify-between p-4 gap-3">
        <div className="flex flex-col gap-1">
          <h3 className="gallery-serif line-clamp-2 text-base font-semibold leading-snug text-stone-900 transition-colors group-hover:text-amber-900 dark:text-stone-100 dark:group-hover:text-amber-400">
            {m.title || "Untitled"}
          </h3>
          <p className="line-clamp-1 text-xs text-stone-600 dark:text-stone-400">
            <span className="font-medium text-stone-800 dark:text-stone-200">{m.attribution || "Unknown Artist"}</span>
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

          <button
            onClick={() => onFindSimilar(result.uuid)}
            className="flex items-center justify-center gap-1.5 rounded-lg border border-stone-200 bg-stone-50/80 px-3 py-1.5 text-xs font-medium text-stone-700 transition-all hover:border-amber-600/50 hover:bg-amber-50/60 hover:text-amber-900 dark:border-stone-800 dark:bg-stone-800/50 dark:text-stone-300 dark:hover:border-amber-500/40 dark:hover:bg-amber-950/30 dark:hover:text-amber-300"
          >
            <span>✦</span>
            <span>Find visually similar</span>
          </button>
        </div>
      </div>
    </div>
  );
}
