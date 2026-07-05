// Server-side client for the FastAPI backend (hosted on a Hugging Face Space).
// Kept server-only so the backend URL lives in a non-public env var and the
// Next.js API routes can gracefully absorb the Space's cold-start latency.

// The nine Western art movements the WikiArt classifier assigns.
export const MOVEMENTS = [
  "art_nouveau",
  "baroque",
  "renaissance",
  "romanticism",
  "realism",
  "expressionism",
  "surrealism",
  "impressionism",
  "post_impressionism",
] as const;

export type Movement = (typeof MOVEMENTS)[number];

// Metadata carried by image / visual results (nga_images + nga_dino indexes).
export type ArtworkMeta = {
  objectid: number;
  title: string;
  attribution: string;
  date: string;
  medium: string;
  classification: string;
  iiif: string;
  pred_movement: string;
  pred_confidence: number;
  pred_anachronistic: boolean;
  pred_alt1: string;
  pred_alt1_conf: number;
  pred_alt2: string;
  pred_alt2_conf: number;
};

export type ImageResult = {
  uuid: string;
  score: number;
  metadata: ArtworkMeta;
};

// The text index (nga_artworks, 145k) is metadata-only — no thumbnails.
export type TextMeta = {
  title: string;
  artists: string;
  date: string;
  medium: string;
  classification: string;
};

export type TextResult = {
  objectid: string;
  score: number;
  document: string;
  metadata: TextMeta;
};

export function getApiBase(): string | null {
  const base = process.env.ART_API_URL;
  if (!base) return null;
  return base.replace(/\/$/, "");
}

// A free HF Space sleeps after inactivity; the first request after a sleep
// wakes it and can take ~30-60s while models reload. Give it real headroom.
const COLD_START_TIMEOUT_MS = 90_000;

export async function proxyGet(
  path: string,
  params: Record<string, string | number | undefined>
): Promise<{ ok: true; data: unknown } | { ok: false; status: number; error: string }> {
  const base = getApiBase();
  if (!base) {
    return {
      ok: false,
      status: 503,
      error: "The art search backend isn't configured yet (ART_API_URL unset).",
    };
  }

  const url = new URL(`${base}${path}`);
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") {
      url.searchParams.set(key, String(value));
    }
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), COLD_START_TIMEOUT_MS);

  try {
    const res = await fetch(url, { signal: controller.signal });
    if (!res.ok) {
      return { ok: false, status: res.status, error: `Backend returned ${res.status}.` };
    }
    return { ok: true, data: await res.json() };
  } catch (err) {
    if (err instanceof Error && err.name === "AbortError") {
      return {
        ok: false,
        status: 504,
        error: "The backend is taking too long — it may be waking up. Try again in a moment.",
      };
    }
    return { ok: false, status: 502, error: "Couldn't reach the art search backend." };
  } finally {
    clearTimeout(timeout);
  }
}
