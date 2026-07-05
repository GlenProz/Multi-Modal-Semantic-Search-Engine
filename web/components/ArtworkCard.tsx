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
    <div className="group flex flex-col overflow-hidden rounded-xl border border-black/[.08] bg-white dark:border-white/[.1] dark:bg-zinc-950">
      <a
        href={fullSizeUrl(m.iiif)}
        target="_blank"
        rel="noopener noreferrer"
        className="relative block aspect-square overflow-hidden bg-zinc-100 dark:bg-zinc-900"
      >
        {/* eslint-disable-next-line @next/next/no-img-element -- NGA IIIF host, not worth a next/image remotePatterns entry for a hobby demo */}
        <img
          src={m.iiif}
          alt={m.title}
          loading="lazy"
          className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-[1.03]"
        />
        <span className="absolute right-2 top-2 rounded bg-black/60 px-1.5 py-0.5 text-[10px] font-medium text-white opacity-0 transition-opacity group-hover:opacity-100">
          {Math.round(result.score * 100)}% match
        </span>
      </a>

      <div className="flex flex-1 flex-col gap-2 p-3">
        <div className="flex flex-col gap-0.5">
          <span className="line-clamp-2 text-sm font-medium leading-snug text-black dark:text-zinc-50">
            {m.title || "Untitled"}
          </span>
          <span className="line-clamp-1 text-xs text-zinc-600 dark:text-zinc-400">
            {m.attribution || "Unknown"}
            {m.date ? ` · ${m.date}` : ""}
          </span>
        </div>

        <MovementBadge
          movement={m.pred_movement}
          confidence={m.pred_confidence}
          anachronistic={m.pred_anachronistic}
        />

        <button
          onClick={() => onFindSimilar(result.uuid)}
          className="mt-auto rounded-lg border border-black/[.08] px-2.5 py-1.5 text-xs font-medium transition-colors hover:bg-black/[.04] dark:border-white/[.145] dark:hover:bg-[#1a1a1a]"
        >
          Find visually similar
        </button>
      </div>
    </div>
  );
}
