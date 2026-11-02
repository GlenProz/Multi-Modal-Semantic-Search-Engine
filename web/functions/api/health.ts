interface Env {
  ART_API_URL?: string;
}

export const onRequestGet: PagesFunction<Env> = async (context) => {
  const backendBase = (context.env.ART_API_URL || "https://kerchoo-nga-art-search.hf.space").replace(/\/$/, "");
  try {
    const res = await fetch(`${backendBase}/health`, {
      signal: AbortSignal.timeout(30_000),
    });
    const data = await res.text();
    return new Response(data, {
      status: res.status,
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
      },
    });
  } catch {
    return new Response(JSON.stringify({ ok: false, error: "Backend unreachable" }), {
      status: 503,
      headers: { "Content-Type": "application/json" },
    });
  }
};
