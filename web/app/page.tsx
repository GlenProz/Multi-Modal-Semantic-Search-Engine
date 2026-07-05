"use client";

import { useCallback, useEffect, useState } from "react";
import { MOVEMENTS, type ImageResult, type TextResult } from "@/lib/api";
import { ArtworkCard } from "@/components/ArtworkCard";

const EXAMPLE_QUERIES = [
  "moody European rainy-day landscape",
  "two figures embracing under a tree",
  "impressionist harbor scene",
  "a melancholy figure alone in a field",
];

type Mode = "images" | "text";

function prettyMovement(m: string): string {
  return m.replace(/_/g, " ");
}

export default function Home() {
  const [mode, setMode] = useState<Mode>("images");
  const [query, setQuery] = useState("");
  const [selectedMovements, setSelectedMovements] = useState<Set<string>>(new Set());

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [imageResults, setImageResults] = useState<ImageResult[]>([]);
  const [textResults, setTextResults] = useState<TextResult[]>([]);
  const [resultLabel, setResultLabel] = useState<string | null>(null);

  const [backendUp, setBackendUp] = useState<boolean | null>(null);

  // Probe the backend once on load so we can warn early if it isn't connected
  // (expected until the Hugging Face Space is deployed) or is still waking up.
  useEffect(() => {
    fetch("/api/health")
      .then((res) => setBackendUp(res.ok))
      .catch(() => setBackendUp(false));
  }, []);

  function toggleMovement(m: string) {
    setSelectedMovements((prev) => {
      const next = new Set(prev);
      if (next.has(m)) next.delete(m);
      else next.add(m);
      return next;
    });
  }

  const runSearch = useCallback(
    async (targetQuery: string, targetMode: Mode, movements: Set<string>) => {
      if (!targetQuery.trim()) return;

      setLoading(true);
      setError(null);
      setImageResults([]);
      setTextResults([]);

      const params = new URLSearchParams({ q: targetQuery, mode: targetMode });
      if (targetMode === "images" && movements.size > 0) {
        params.set("movements", Array.from(movements).join(","));
      }

      try {
        const res = await fetch(`/api/search?${params.toString()}`);
        const body = await res.json();
        if (!res.ok) {
          setError(body.error ?? "Something went wrong.");
          return;
        }
        if (targetMode === "text") {
          setTextResults(body.results ?? []);
        } else {
          setImageResults(body.results ?? []);
        }
        setResultLabel(`Results for “${targetQuery}”`);
      } catch {
        setError("Couldn't reach the search backend. Try again.");
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const findSimilar = useCallback(async (uuid: string) => {
    setLoading(true);
    setError(null);
    setTextResults([]);
    window.scrollTo({ top: 0, behavior: "smooth" });

    try {
      const res = await fetch(`/api/similar?id=${encodeURIComponent(uuid)}`);
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? "Something went wrong.");
        return;
      }
      setMode("images");
      setImageResults(body.results ?? []);
      setResultLabel(
        body.seed_title ? `Visually similar to “${body.seed_title}”` : "Visually similar"
      );
    } catch {
      setError("Couldn't reach the search backend. Try again.");
    } finally {
      setLoading(false);
    }
  }, []);

  const surpriseMe = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/random");
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? "Something went wrong.");
        setLoading(false);
        return;
      }
      // Seed a visual-similarity grid from a random artwork — a discovery flow.
      await findSimilar(body.uuid);
    } catch {
      setError("Couldn't reach the search backend. Try again.");
      setLoading(false);
    }
  }, [findSimilar]);

  return (
    <div className="flex flex-col flex-1 items-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex w-full max-w-5xl flex-col gap-8 px-6 py-16">
        <div className="flex flex-col gap-3">
          <h1 className="text-3xl font-semibold tracking-tight text-black dark:text-zinc-50">
            Art Search
          </h1>
          <p className="max-w-2xl text-lg leading-7 text-zinc-600 dark:text-zinc-400">
            Semantic search over ~130k National Gallery of Art works. Describe what
            you want in plain language and get results ranked by meaning — visually
            (CLIP) or by metadata (MiniLM), not by keyword overlap.
          </p>
        </div>

        {backendUp === false && (
          <p className="rounded-lg bg-amber-500/10 px-4 py-3 text-sm text-amber-700 dark:text-amber-400">
            The search backend isn&apos;t reachable right now — it may be waking up
            (the free ML host sleeps when idle), or it isn&apos;t connected yet.
          </p>
        )}

        {/* Mode toggle */}
        <div className="flex gap-1 self-start rounded-lg border border-black/[.08] p-1 text-sm dark:border-white/[.1]">
          <button
            onClick={() => setMode("images")}
            className={`rounded-md px-3 py-1.5 font-medium transition-colors ${
              mode === "images"
                ? "bg-foreground text-background"
                : "text-zinc-600 hover:bg-black/[.04] dark:text-zinc-400 dark:hover:bg-white/[.06]"
            }`}
          >
            Visual (CLIP)
          </button>
          <button
            onClick={() => setMode("text")}
            className={`rounded-md px-3 py-1.5 font-medium transition-colors ${
              mode === "text"
                ? "bg-foreground text-background"
                : "text-zinc-600 hover:bg-black/[.04] dark:text-zinc-400 dark:hover:bg-white/[.06]"
            }`}
          >
            Metadata (MiniLM)
          </button>
        </div>

        {/* Search bar */}
        <div className="flex flex-col gap-3 sm:flex-row">
          <input
            type="text"
            value={query}
            placeholder={
              mode === "images"
                ? "Describe a scene, mood, or subject…"
                : "Search titles, media, attributions by meaning…"
            }
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") runSearch(query, mode, selectedMovements);
            }}
            className="flex-1 rounded-lg border border-black/[.08] bg-white px-4 py-2.5 text-sm text-black dark:border-white/[.1] dark:bg-zinc-950 dark:text-zinc-50"
          />
          <button
            onClick={() => runSearch(query, mode, selectedMovements)}
            disabled={loading}
            className="rounded-lg bg-foreground px-5 py-2.5 text-sm font-medium text-background transition-colors hover:bg-[#383838] disabled:opacity-50 dark:hover:bg-[#ccc]"
          >
            {loading ? "Searching…" : "Search"}
          </button>
          {mode === "images" && (
            <button
              onClick={surpriseMe}
              disabled={loading}
              className="rounded-lg border border-black/[.08] px-5 py-2.5 text-sm font-medium transition-colors hover:bg-black/[.04] disabled:opacity-50 dark:border-white/[.145] dark:hover:bg-[#1a1a1a]"
            >
              Surprise me
            </button>
          )}
        </div>

        {/* Example queries */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="text-zinc-500">Try:</span>
          {EXAMPLE_QUERIES.map((ex) => (
            <button
              key={ex}
              onClick={() => {
                setQuery(ex);
                runSearch(ex, mode, selectedMovements);
              }}
              className="rounded-full border border-black/[.08] px-3 py-1 text-zinc-600 transition-colors hover:bg-black/[.04] dark:border-white/[.1] dark:text-zinc-400 dark:hover:bg-white/[.06]"
            >
              {ex}
            </button>
          ))}
        </div>

        {/* Movement filter (visual mode only) */}
        {mode === "images" && (
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-zinc-500">Movement:</span>
            {MOVEMENTS.map((m) => {
              const active = selectedMovements.has(m);
              return (
                <button
                  key={m}
                  onClick={() => toggleMovement(m)}
                  className={`rounded-full px-2.5 py-1 text-xs font-medium capitalize transition-colors ${
                    active
                      ? "bg-foreground text-background"
                      : "border border-black/[.08] text-zinc-600 hover:bg-black/[.04] dark:border-white/[.1] dark:text-zinc-400 dark:hover:bg-white/[.06]"
                  }`}
                >
                  {prettyMovement(m)}
                </button>
              );
            })}
            {selectedMovements.size > 0 && (
              <button
                onClick={() => setSelectedMovements(new Set())}
                className="text-xs text-zinc-500 underline"
              >
                clear
              </button>
            )}
          </div>
        )}

        {error && (
          <p className="rounded-lg bg-red-500/10 px-4 py-3 text-sm text-red-600 dark:text-red-400">
            {error}
          </p>
        )}

        {loading && (
          <div className="flex flex-col items-center gap-2 py-16 text-sm text-zinc-500">
            <span>Searching…</span>
            <span className="text-xs">
              First search after idle can take ~30s while the model host wakes up.
            </span>
          </div>
        )}

        {/* Results */}
        {!loading && resultLabel && (
          <div className="flex flex-col gap-4">
            <h2 className="text-sm font-medium text-zinc-500">{resultLabel}</h2>

            {mode === "images" && imageResults.length > 0 && (
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
                {imageResults.map((r) => (
                  <ArtworkCard key={r.uuid} result={r} onFindSimilar={findSimilar} />
                ))}
              </div>
            )}

            {mode === "text" && textResults.length > 0 && (
              <ul className="flex flex-col gap-3">
                {textResults.map((r) => (
                  <li
                    key={r.objectid}
                    className="flex flex-col gap-1 rounded-xl border border-black/[.08] bg-white p-4 dark:border-white/[.1] dark:bg-zinc-950"
                  >
                    <div className="flex items-baseline justify-between gap-3">
                      <span className="font-medium text-black dark:text-zinc-50">
                        {r.metadata.title || "Untitled"}
                      </span>
                      <span className="shrink-0 text-xs text-zinc-400">
                        {Math.round(r.score * 100)}% match
                      </span>
                    </div>
                    <span className="text-sm text-zinc-600 dark:text-zinc-400">
                      {r.metadata.artists || "Unknown"}
                    </span>
                    <span className="text-xs text-zinc-500">
                      {[r.metadata.classification, r.metadata.medium, r.metadata.date]
                        .filter(Boolean)
                        .join(" · ")}
                    </span>
                  </li>
                ))}
              </ul>
            )}

            {((mode === "images" && imageResults.length === 0) ||
              (mode === "text" && textResults.length === 0)) && (
              <p className="text-sm text-zinc-500">No results for that query.</p>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
