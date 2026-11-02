"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { MOVEMENTS, type ImageResult, type TextResult } from "@/lib/api";
import { ArtworkCard } from "@/components/ArtworkCard";

const EXAMPLE_QUERIES = [
  {
    icon: "🕯️",
    label: "Candlelit Solitude",
    query: "tenebrous candlelight illuminating a solitary thinker in shadows",
    category: "Chiaroscuro & Optics",
  },
  {
    icon: "🌊",
    label: "Sublime Storm at Sea",
    query: "raging ocean storm waves crashing against treacherous jagged cliffs",
    category: "The Romantic Sublime",
  },
  {
    icon: "💀",
    label: "Allegorical Vanitas",
    query: "allegorical vanitas with skull hourglass and fading blooms",
    category: "Symbolism & Mortality",
  },
  {
    icon: "🌧️",
    label: "Wet Cobblestone Nocturne",
    query: "misty nocturnal city street reflections on wet cobblestones",
    category: "Atmospheric Impressionism",
  },
  {
    icon: "🏛️",
    label: "Gothic Gargoyle Perch",
    query: "grotesque gargoyle perched high above a soaring gothic cathedral",
    category: "Gothic & Grotesque",
  },
  {
    icon: "👶",
    label: "Maternal Tenderness",
    query: "intimate maternal tenderness cradling a sleeping child",
    category: "Emotional Intimacy",
  },
  {
    icon: "🏰",
    label: "Labyrinthine Vaults",
    query: "labyrinthine vaulted stone corridors with dramatic receding perspective",
    category: "Spatial Geometry",
  },
  {
    icon: "🍂",
    label: "Golden Hour Mist",
    query: "golden hour haze filtering through autumn trees",
    category: "Optics & Luminism",
  },
  {
    icon: "🎻",
    label: "Tavern Revelers",
    query: "raucous tavern revelers singing and playing lutes and violins",
    category: "Genre Narrative",
  },
  {
    icon: "🌿",
    label: "Overgrown Classical Ruins",
    query: "ancient decaying classical stone ruins overtaken by wild overgrown ivy",
    category: "Romantic Decay",
  },
];

type Mode = "hybrid" | "images" | "text";

function prettyMovement(m: string): string {
  return m.replace(/_/g, " ");
}

export default function Home() {
  const [mode, setMode] = useState<Mode>("hybrid");
  const [query, setQuery] = useState("");
  const [selectedMovements, setSelectedMovements] = useState<Set<string>>(new Set());
  const [onlyWithImages, setOnlyWithImages] = useState(true);
  const [activeInspiration, setActiveInspiration] = useState<string | null>(null);
  const resultsRef = useRef<HTMLElement>(null);

  const scrollToResults = useCallback(() => {
    setTimeout(() => {
      resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 100);
  }, []);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [imageResults, setImageResults] = useState<ImageResult[]>([]);
  const [textResults, setTextResults] = useState<TextResult[]>([]);
  const [resultLabel, setResultLabel] = useState<string | null>(null);

  const [backendUp, setBackendUp] = useState<boolean | null>(null);
  const [stats, setStats] = useState<{ text?: number; images?: number; dino?: number }>({
    text: 145560,
    images: 63249,
    dino: 63249,
  });

  const displayedImageResults = useMemo(() => {
    if (mode === "hybrid" && onlyWithImages) {
      return imageResults.filter((r) => Boolean(r.metadata?.iiif));
    }
    return imageResults;
  }, [mode, onlyWithImages, imageResults]);

  // Probe the backend on load
  useEffect(() => {
    fetch("/api/health")
      .then(async (res) => {
        if (res.ok) {
          const data = await res.json();
          setBackendUp(true);
          setStats({
            text: data.text_count,
            images: data.image_count,
            dino: data.dino_count,
          });
        } else {
          setBackendUp(false);
        }
      })
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
      if (targetMode !== "text" && movements.size > 0) {
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
        setResultLabel(`Found ${body.results?.length ?? 0} works for “${targetQuery}”`);
      } catch {
        setError("Couldn't reach the search backend. It may be waking up, please try again.");
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
    scrollToResults();

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
        body.seed_title ? `Visually similar to “${body.seed_title}”` : "Visually similar artworks"
      );
    } catch {
      setError("Couldn't reach the visual search backend. Try again in a moment.");
    } finally {
      setLoading(false);
    }
  }, []);

  const selectInspiration = useCallback(
    (ex: (typeof EXAMPLE_QUERIES)[number]) => {
      setQuery(ex.query);
      setActiveInspiration(ex.label);
      runSearch(ex.query, mode, selectedMovements);
      scrollToResults();
    },
    [mode, selectedMovements, runSearch, scrollToResults]
  );

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
      // Seed a visual-similarity discovery flow from a random artwork
      await findSimilar(body.uuid);
    } catch {
      setError("Couldn't reach the search backend. Try again.");
      setLoading(false);
    }
  }, [findSimilar]);

  return (
    <div className="flex min-h-screen flex-col bg-[#fbfaf8] text-stone-900 selection:bg-amber-100 selection:text-amber-900 dark:bg-[#0c0a09] dark:text-stone-100 dark:selection:bg-amber-950 dark:selection:text-amber-200">
      {/* Top Gallery Header */}
      <header className="sticky top-0 z-40 border-b border-stone-200/80 bg-[#fbfaf8]/90 backdrop-blur-md dark:border-stone-800/80 dark:bg-[#0c0a09]/90">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3.5">
          <div className="flex items-center gap-3">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-stone-900 text-stone-100 text-sm font-serif font-bold dark:bg-stone-100 dark:text-stone-900">
              🏛️
            </span>
            <div className="flex flex-col">
              <span className="text-xs font-mono uppercase tracking-widest text-stone-500 dark:text-stone-400">
                Anchor Analytics · Atelier
              </span>
              <span className="text-sm font-semibold tracking-tight">
                National Gallery of Art Semantic Explorer
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3 text-xs">
            {backendUp !== null && (
              <span className="hidden sm:inline-flex items-center gap-1.5 rounded-full border border-stone-200 bg-white px-2.5 py-1 text-[11px] font-mono text-stone-600 dark:border-stone-800 dark:bg-stone-900 dark:text-stone-300">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                {(stats.text || 145560).toLocaleString()} works indexed
              </span>
            )}
            <a
              href="https://github.com/GlenProz/Multi-Modal-Semantic-Search-Engine"
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-lg border border-stone-200 bg-white px-3 py-1.5 font-medium text-stone-700 transition-colors hover:border-stone-400 hover:text-black dark:border-stone-800 dark:bg-stone-900 dark:text-stone-300 dark:hover:border-stone-600 dark:hover:text-white"
            >
              GitHub ↗
            </a>
          </div>
        </div>
      </header>

      {/* Hero Atmosphere Section */}
      <section className="relative overflow-hidden pt-12 pb-8 sm:pt-16 sm:pb-12">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <span className="inline-block rounded-full border border-amber-600/20 bg-amber-500/10 px-3.5 py-1 text-xs font-serif italic text-amber-800 dark:text-amber-300">
            Multi-Modal Vision & NLP Catalog
          </span>

          <h1 className="gallery-serif mt-4 text-4xl font-normal tracking-tight text-stone-900 sm:text-5xl lg:text-6xl dark:text-stone-50">
            Explore 145,000 Masterpieces
            <span className="block italic text-stone-700 dark:text-stone-300">by Meaning & Mood</span>
          </h1>

          <p className="mx-auto mt-4 max-w-2xl text-base leading-relaxed text-stone-600 sm:text-lg dark:text-stone-400">
            Search beyond museum tags. Natural-language query across the National Gallery of Art
            combining neural pixel embeddings (<span className="font-mono text-xs">CLIP</span>), visual
            neighbors (<span className="font-mono text-xs">DINOv2</span>), and curatorial alt-text (<span className="font-mono text-xs">MiniLM</span>).
          </p>
        </div>
      </section>

      {/* Main Search Station */}
      <section className="mx-auto w-full max-w-4xl px-6 pb-8">
        <div className="rounded-2xl border border-stone-200/90 bg-white p-4 shadow-xl shadow-stone-200/40 sm:p-6 dark:border-stone-800/90 dark:bg-stone-900/80 dark:shadow-none">
          {/* Mode Tabs & Explanation */}
          <div className="mb-4 flex flex-col gap-2.5 border-b border-stone-100 pb-4 dark:border-stone-800/80">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex gap-1.5 rounded-xl bg-stone-100/80 p-1 text-xs sm:text-sm dark:bg-stone-800/60">
                <button
                  onClick={() => setMode("hybrid")}
                  className={`flex items-center gap-1.5 rounded-lg px-3.5 py-1.5 font-medium transition-all ${
                    mode === "hybrid"
                      ? "bg-white text-stone-950 shadow-sm dark:bg-stone-700 dark:text-white"
                      : "text-stone-600 hover:text-stone-900 dark:text-stone-400 dark:hover:text-stone-200"
                  }`}
                >
                  <span>⚡</span>
                  <span>Hybrid (RRF)</span>
                </button>
                <button
                  onClick={() => setMode("images")}
                  className={`flex items-center gap-1.5 rounded-lg px-3.5 py-1.5 font-medium transition-all ${
                    mode === "images"
                      ? "bg-white text-stone-950 shadow-sm dark:bg-stone-700 dark:text-white"
                      : "text-stone-600 hover:text-stone-900 dark:text-stone-400 dark:hover:text-stone-200"
                  }`}
                >
                  <span>🖼️</span>
                  <span>Visual (CLIP)</span>
                </button>
                <button
                  onClick={() => setMode("text")}
                  className={`flex items-center gap-1.5 rounded-lg px-3.5 py-1.5 font-medium transition-all ${
                    mode === "text"
                      ? "bg-white text-stone-950 shadow-sm dark:bg-stone-700 dark:text-white"
                      : "text-stone-600 hover:text-stone-900 dark:text-stone-400 dark:hover:text-stone-200"
                  }`}
                >
                  <span>📜</span>
                  <span>Catalog (MiniLM)</span>
                </button>
              </div>

              <button
                onClick={surpriseMe}
                disabled={loading}
                title="Pick a random artwork from the 63k image index and explore its visual neighbors"
                className="flex items-center gap-1.5 rounded-lg border border-amber-600/30 bg-amber-50/70 px-3 py-1.5 text-xs font-medium text-amber-900 transition-colors hover:bg-amber-100 disabled:opacity-50 dark:border-amber-500/30 dark:bg-amber-950/40 dark:text-amber-200 dark:hover:bg-amber-900/40"
              >
                <span>🎲</span>
                <span>Surprise Me</span>
              </button>
            </div>

            {/* Mode Explanation */}
            <div className="flex items-baseline gap-2 px-1 text-xs text-stone-500 dark:text-stone-400">
              <span className="font-serif italic text-amber-800 dark:text-amber-300 shrink-0">How it works:</span>
              <p className="leading-relaxed">
                {mode === "hybrid" && (
                  <>
                    <strong className="font-medium text-stone-700 dark:text-stone-300">Reciprocal Rank Fusion (RRF)</strong> fuses pixel aesthetics with archival catalog metadata for the most balanced, meaning-aware search.
                  </>
                )}
                {mode === "images" && (
                  <>
                    <strong className="font-medium text-stone-700 dark:text-stone-300">CLIP</strong> embeds raw artwork pixels into a joint vision/language space to retrieve visual moods, lighting, and textures without relying on manual tags.
                  </>
                )}
                {mode === "text" && (
                  <>
                    <strong className="font-medium text-stone-700 dark:text-stone-300">MiniLM</strong> searches across 17 museum catalog tables, artist names, media, and curatorial alt-text by semantic meaning rather than exact keywords.
                  </>
                )}
              </p>
            </div>
          </div>

          {/* Search Input Bar */}
          <div className="relative flex flex-col gap-2.5 sm:flex-row">
            <div className="relative flex-1">
              <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-4 text-stone-400">
                🔍
              </span>
              <input
                type="text"
                value={query}
                placeholder={
                  mode === "text"
                    ? "Search titles, media, artists, provenance by meaning…"
                    : mode === "hybrid"
                    ? "Search by scene, subject, lighting, or mood (fusing text & pixels)…"
                    : "Describe the visual scene (e.g. moody rainy street, portrait in candlelight)…"
                }
                onChange={(e) => {
                  setQuery(e.target.value);
                  setActiveInspiration(null);
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter") runSearch(query, mode, selectedMovements);
                }}
                className="w-full rounded-xl border border-stone-200 bg-stone-50/50 py-3.5 pl-11 pr-10 text-sm text-stone-900 placeholder:text-stone-400 focus:border-amber-700 focus:bg-white focus:outline-none focus:ring-2 focus:ring-amber-700/20 dark:border-stone-700 dark:bg-stone-950 dark:text-stone-100 dark:placeholder:text-stone-500 dark:focus:border-amber-500 dark:focus:bg-stone-950 dark:focus:ring-amber-500/30"
              />
              {query && (
                <button
                  onClick={() => {
                    setQuery("");
                    setActiveInspiration(null);
                  }}
                  className="absolute inset-y-0 right-0 flex items-center pr-3 text-xs text-stone-400 hover:text-stone-700 dark:hover:text-stone-200"
                >
                  ✕
                </button>
              )}
            </div>

            <button
              onClick={() => runSearch(query, mode, selectedMovements)}
              disabled={loading || !query.trim()}
              className="flex items-center justify-center gap-2 rounded-xl bg-stone-900 px-6 py-3.5 text-sm font-semibold text-stone-100 transition-all hover:bg-amber-950 disabled:opacity-40 dark:bg-stone-100 dark:text-stone-900 dark:hover:bg-amber-100"
            >
              {loading ? (
                <>
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-stone-300 border-t-stone-900 dark:border-stone-700 dark:border-t-white" />
                  <span>Searching…</span>
                </>
              ) : (
                <span>Search Gallery</span>
              )}
            </button>
          </div>

          {/* Curated Semantic Prompt Inspirations */}
          <div className="mt-4 flex flex-col gap-2 pt-1 border-t border-stone-100/80 dark:border-stone-800/60">
            <div className="flex items-center justify-between">
              <span className="font-serif text-xs italic text-stone-500 dark:text-stone-400">
                Semantic Inspirations <span className="font-sans not-italic text-[11px] text-stone-400 dark:text-stone-500">(deep moods, lighting & narrative concepts):</span>
              </span>
              <span className="text-[11px] font-mono text-stone-400 dark:text-stone-500 hidden sm:inline">
                Instant edge cache ⚡
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-2 text-xs">
              {EXAMPLE_QUERIES.map((ex) => {
                const isActive = activeInspiration === ex.label;
                return (
                  <button
                    key={ex.label}
                    onClick={() => selectInspiration(ex)}
                    title={`[${ex.category}]\nSearch query: "${ex.query}"\n(Click to explore)`}
                    className={`group flex items-center gap-1.5 rounded-full px-3 py-1 text-xs transition-all ${
                      isActive
                        ? "border border-amber-600 bg-amber-100/90 text-amber-950 shadow-sm ring-1 ring-amber-500/40 dark:border-amber-500 dark:bg-amber-950/70 dark:text-amber-200"
                        : "border border-stone-200/90 bg-stone-50/80 text-stone-700 hover:border-amber-600/50 hover:bg-amber-50/80 hover:text-amber-950 hover:shadow-sm dark:border-stone-800 dark:bg-stone-800/50 dark:text-stone-300 dark:hover:border-amber-500/40 dark:hover:bg-amber-950/40 dark:hover:text-amber-200"
                    }`}
                  >
                    <span className="text-xs transition-transform group-hover:scale-110">{ex.icon}</span>
                    <span className="font-medium">{ex.label}</span>
                    {isActive && (
                      <span className="h-1.5 w-1.5 rounded-full bg-amber-600 dark:bg-amber-400 animate-pulse" />
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Movement Filter Pills (Hybrid & Visual Modes) */}
          {mode !== "text" && (
            <div className="mt-4 pt-3.5 border-t border-stone-100 flex flex-wrap items-center justify-between gap-3 dark:border-stone-800/80">
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="text-xs font-serif text-stone-500 dark:text-stone-400 mr-1">Movement filter:</span>
                {MOVEMENTS.map((m) => {
                  const active = selectedMovements.has(m);
                  return (
                    <button
                      key={m}
                      onClick={() => toggleMovement(m)}
                      className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize transition-all ${
                        active
                          ? "bg-stone-900 text-stone-100 shadow-sm dark:bg-stone-100 dark:text-stone-900"
                          : "border border-stone-200 text-stone-600 hover:border-stone-300 hover:bg-stone-100/50 dark:border-stone-800 dark:text-stone-400 dark:hover:bg-stone-800/50"
                      }`}
                    >
                      {prettyMovement(m)}
                    </button>
                  );
                })}
                {selectedMovements.size > 0 && (
                  <button
                    onClick={() => setSelectedMovements(new Set())}
                    className="ml-2 text-xs text-amber-700 underline dark:text-amber-400 hover:opacity-80"
                  >
                    Clear filters
                  </button>
                )}
              </div>

              {/* Digitized images filter (Hybrid mode) */}
              {mode === "hybrid" && (
                <label
                  title="Only show artworks that have open-access digital scans (hides catalog-only records)"
                  className="inline-flex items-center gap-2 rounded-lg border border-stone-200/90 bg-stone-50/70 px-2.5 py-1 text-xs text-stone-700 transition-colors hover:bg-stone-100 cursor-pointer select-none dark:border-stone-800 dark:bg-stone-800/40 dark:text-stone-300 dark:hover:bg-stone-800/70"
                >
                  <input
                    type="checkbox"
                    checked={onlyWithImages}
                    onChange={(e) => setOnlyWithImages(e.target.checked)}
                    className="h-3.5 w-3.5 rounded border-stone-300 text-amber-700 focus:ring-amber-600 dark:border-stone-700 dark:bg-stone-900 dark:focus:ring-amber-500"
                  />
                  <span>Digitized images only</span>
                </label>
              )}
            </div>
          )}
        </div>

        {/* Backend Cold Start Notice */}
        {backendUp === false && (
          <div className="mt-4 flex items-center gap-2 rounded-xl border border-amber-500/20 bg-amber-500/10 px-4 py-3 text-xs text-amber-800 dark:text-amber-300">
            <span>ℹ️</span>
            <span>
              The serverless model host is waking up. The first query after idle takes ~30 seconds;
              subsequent searches return in ~130ms from the Cloudflare edge cache.
            </span>
          </div>
        )}

        {error && (
          <div className="mt-4 rounded-xl border border-rose-500/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-700 dark:text-rose-400">
            {error}
          </div>
        )}
      </section>

      {/* Results or Discovery Showcase */}
      <main ref={resultsRef} className="mx-auto w-full max-w-7xl flex-1 px-6 pb-20 scroll-mt-6">
        {loading && (
          <div className="flex flex-col items-center justify-center gap-3 py-24 text-center">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-stone-300 border-t-stone-800 dark:border-stone-700 dark:border-t-amber-400" />
            <span className="font-serif text-lg italic text-stone-700 dark:text-stone-300">
              Querying neural latent space across 145,000 artworks…
            </span>
            <span className="text-xs text-stone-500">
              Fusing semantic concepts, pixel similarities, and historical metadata.
            </span>
          </div>
        )}

        {/* Active Results Display */}
        {!loading && resultLabel && (
          <div className="flex flex-col gap-6">
            <div className="flex flex-wrap items-center justify-between border-b border-stone-200/80 pb-3 gap-2 dark:border-stone-800">
              <div className="flex flex-col gap-0.5">
                <h2 className="font-serif text-xl font-medium tracking-tight text-stone-800 dark:text-stone-200">
                  {resultLabel}
                  {mode === "hybrid" && onlyWithImages && imageResults.length > displayedImageResults.length && (
                    <span className="ml-2 font-sans text-xs font-normal text-stone-500 dark:text-stone-400">
                      ({imageResults.length - displayedImageResults.length} archival-only records hidden)
                    </span>
                  )}
                </h2>
                <p className="text-xs text-stone-500 dark:text-stone-400">
                  <span className="font-medium text-stone-700 dark:text-stone-300">Match %:</span>{" "}
                  {mode === "hybrid"
                    ? "Normalized Reciprocal Rank Fusion combining CLIP pixel embeddings & MiniLM catalog text (hover badge on any card for exact breakdown)"
                    : mode === "images"
                    ? "Cosine similarity between search query & CLIP ViT-B/32 neural image embeddings"
                    : "Cosine similarity between search query & all-MiniLM-L6-v2 museum catalog embeddings"}
                </p>
              </div>
              <span className="text-xs font-mono text-stone-500">
                Mode: <span className="uppercase text-amber-700 dark:text-amber-400 font-semibold">{mode}</span>
              </span>
            </div>

            {/* Visual & Hybrid Grid */}
            {mode !== "text" && displayedImageResults.length > 0 && (
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
                {displayedImageResults.map((r, idx) => (
                  <ArtworkCard
                    key={r.uuid || `${r.objectid ?? "item"}-${idx}`}
                    result={r}
                    onFindSimilar={findSimilar}
                  />
                ))}
              </div>
            )}

            {/* Text / Catalog List */}
            {mode === "text" && textResults.length > 0 && (
              <ul className="flex flex-col gap-3">
                {textResults.map((r) => (
                  <li
                    key={r.objectid}
                    className="flex flex-col gap-1.5 rounded-xl border border-stone-200 bg-white p-5 shadow-sm dark:border-stone-800 dark:bg-stone-900/80"
                  >
                    <div className="flex items-baseline justify-between gap-3">
                      <span className="gallery-serif text-lg font-medium text-stone-900 dark:text-stone-100">
                        {r.metadata.title || "Untitled"}
                      </span>
                      <span
                        title={`MiniLM Semantic Relevance: ${Math.round(r.score * 100)}%\nCosine similarity between your search query and museum catalog metadata (titles, media, artists, provenance, curatorial notes).`}
                        className="shrink-0 cursor-help rounded-full bg-stone-100 px-2 py-0.5 text-xs font-mono font-medium text-stone-700 transition-colors hover:bg-stone-200 dark:bg-stone-800 dark:text-stone-300 dark:hover:bg-stone-700"
                      >
                        {Math.round(r.score * 100)}% match
                      </span>
                    </div>
                    <span className="text-sm font-medium text-stone-700 dark:text-stone-300">
                      {r.metadata.artists || "Unknown Artist"}
                    </span>
                    <span className="text-xs text-stone-500 dark:text-stone-400">
                      {[r.metadata.classification, r.metadata.medium, r.metadata.date]
                        .filter(Boolean)
                        .join(" · ")}
                    </span>
                    {r.document && (
                      <p className="mt-1 line-clamp-2 text-xs italic text-stone-500 dark:text-stone-400">
                        “{r.document.slice(0, 200)}…”
                      </p>
                    )}
                  </li>
                ))}
              </ul>
            )}

            {((mode !== "text" && imageResults.length === 0) ||
              (mode === "text" && textResults.length === 0)) && (
              <div className="py-16 text-center">
                <p className="font-serif text-lg italic text-stone-500">
                  No artworks matched that particular description.
                </p>
                <p className="mt-1 text-xs text-stone-400">
                  Try broadening your phrasing or clearing active movement filters.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Discovery Engine Showcase (Before any search) */}
        {!loading && !resultLabel && (
          <div className="flex flex-col gap-10 pt-4">
            <div className="text-center">
              <span className="font-serif italic text-sm text-stone-500 dark:text-stone-400">
                Architectural Architecture
              </span>
              <h2 className="gallery-serif mt-1 text-2xl font-medium tracking-tight sm:text-3xl">
                Three Neural Systems in Synchrony
              </h2>
            </div>

            <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
              <div className="rounded-2xl border border-stone-200/90 bg-white p-6 shadow-sm dark:border-stone-800 dark:bg-stone-900/60">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-500/10 text-amber-700 dark:text-amber-400 text-lg mb-4">
                  ⚡
                </div>
                <h3 className="font-serif text-lg font-medium text-stone-900 dark:text-stone-100">
                  Reciprocal Rank Fusion
                </h3>
                <p className="mt-2 text-xs leading-relaxed text-stone-600 dark:text-stone-400">
                  Late-fusion search matching on National Gallery of Art catalog IDs.
                  Fuses visual latent space with 17 relational metadata tables to surface works where both pixels and provenance agree.
                </p>
              </div>

              <div className="rounded-2xl border border-stone-200/90 bg-white p-6 shadow-sm dark:border-stone-800 dark:bg-stone-900/60">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-700 dark:text-indigo-400 text-lg mb-4">
                  🖼️
                </div>
                <h3 className="font-serif text-lg font-medium text-stone-900 dark:text-stone-100">
                  CLIP & DINOv2 Latent Spaces
                </h3>
                <p className="mt-2 text-xs leading-relaxed text-stone-600 dark:text-stone-400">
                  63,249 artwork thumbnails embedded at the pixel level. Find uncatalogued lighting,
                  brushwork textures, and visual compositions with zero reliance on manual human labels.
                </p>
              </div>

              <div className="rounded-2xl border border-stone-200/90 bg-white p-6 shadow-sm dark:border-stone-800 dark:bg-stone-900/60">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 text-lg mb-4">
                  🏷️
                </div>
                <h3 className="font-serif text-lg font-medium text-stone-900 dark:text-stone-100">
                  Movement & OOD Classification
                </h3>
                <p className="mt-2 text-xs leading-relaxed text-stone-600 dark:text-stone-400">
                  WikiArt ViT classifier assigning 9 Western art movements with confidence scoring
                  and a historical plausibility check that flags out-of-distribution anachronisms.
                </p>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Curatorial Footer */}
      <footer className="border-t border-stone-200/80 bg-white py-10 text-xs text-stone-500 dark:border-stone-800 dark:bg-stone-950 dark:text-stone-400">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-6 px-6 sm:flex-row">
          <div className="flex flex-col gap-1 text-center sm:text-left">
            <p className="font-medium text-stone-700 dark:text-stone-300">
              National Gallery of Art Semantic Search Engine
            </p>
            <p className="text-[11px] text-stone-400">
              Public open dataset released under CC0 1.0. Images served live via the NGA IIIF API.
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-4 text-xs font-mono">
            <span>Anchor Analytics LLC</span>
            <span>·</span>
            <a
              href="https://art.anchoranalytics.space"
              className="text-stone-700 hover:text-amber-800 dark:text-stone-300 dark:hover:text-amber-400"
            >
              art.anchoranalytics.space
            </a>
            <span>·</span>
            <a
              href="https://github.com/GlenProz/Multi-Modal-Semantic-Search-Engine"
              target="_blank"
              rel="noopener noreferrer"
              className="text-stone-700 underline hover:text-amber-800 dark:text-stone-300 dark:hover:text-amber-400"
            >
              Source Code
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
