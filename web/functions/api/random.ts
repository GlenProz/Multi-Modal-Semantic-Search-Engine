interface Env {
  ART_API_URL?: string;
}

export const onRequestGet: PagesFunction<Env> = async (context) => {
  const backendBase = (context.env.ART_API_URL || "https://kerchoo-nga-art-search.hf.space").replace(/\/$/, "");
  try {
    const res = await fetch(`${backendBase}/random-artwork`, {
      signal: AbortSignal.timeout(90_000),
    });
    if (!res.ok) {
      return new Response(JSON.stringify({ error: `Backend returned ${res.status}` }), {
        status: res.status,
        headers: { "Content-Type": "application/json" },
      });
    }
    const data = await res.text();
    return new Response(data, {
      status: 200,
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
      },
    });
  } catch {
    return new Response(JSON.stringify({ error: "Couldn't reach the search backend." }), {
      status: 504,
      headers: { "Content-Type": "application/json" },
    });
  }
};
