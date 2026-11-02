interface Env {
  ART_API_URL?: string;
}

export const onRequestGet: PagesFunction<Env> = async (context) => {
  const cache = caches.default;
  const cacheKey = new Request(context.request.url, {
    method: "GET",
    headers: context.request.headers,
  });

  const cached = await cache.match(cacheKey);
  if (cached) {
    const cachedHeaders = new Headers(cached.headers);
    cachedHeaders.set("X-Cache-Status", "HIT");
    return new Response(cached.body, {
      status: cached.status,
      headers: cachedHeaders,
    });
  }

  const url = new URL(context.request.url);
  const q = url.searchParams.get("q")?.trim();
  const mode = url.searchParams.get("mode") ?? "hybrid";
  const movements = url.searchParams.get("movements") ?? undefined;
  const k = url.searchParams.get("k") ?? "24";

  if (!q) {
    return new Response(JSON.stringify({ error: "A query is required." }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  const backendBase = (context.env.ART_API_URL || "https://kerchoo-nga-art-search.hf.space").replace(/\/$/, "");
  const path = mode === "hybrid" ? "/search/hybrid" : mode === "text" ? "/search/text" : "/search/images";
  const backendUrl = new URL(`${backendBase}${path}`);
  backendUrl.searchParams.set("q", q);
  backendUrl.searchParams.set("k", k);
  if (mode !== "text" && movements) {
    backendUrl.searchParams.set("movements", movements);
  }

  try {
    const res = await fetch(backendUrl.toString(), {
      signal: AbortSignal.timeout(90_000),
    });
    if (!res.ok) {
      return new Response(JSON.stringify({ error: `Backend returned ${res.status}` }), {
        status: res.status,
        headers: { "Content-Type": "application/json" },
      });
    }
    const data = await res.text();
    const response = new Response(data, {
      status: 200,
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "public, max-age=86400, s-maxage=86400",
        "X-Cache-Status": "MISS",
      },
    });
    context.waitUntil(cache.put(cacheKey, response.clone()));
    return response;
  } catch (err) {
    return new Response(
      JSON.stringify({
        error: "Couldn't reach the search backend. It may be waking up, please try again in a moment.",
      }),
      {
        status: 504,
        headers: { "Content-Type": "application/json" },
      }
    );
  }
};
