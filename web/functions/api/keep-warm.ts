interface Env {
  ART_API_URL?: string;
}

export const onRequestGet: PagesFunction<Env> = async (context) => {
  const backendBase = (context.env.ART_API_URL || "https://kerchoo-nga-art-search.hf.space").replace(/\/$/, "");
  try {
    const res = await fetch(`${backendBase}/health`, {
      signal: AbortSignal.timeout(55_000),
    });
    return new Response(JSON.stringify({ ok: res.ok, warmed: true }), {
      headers: { "Content-Type": "application/json" },
    });
  } catch {
    return new Response(JSON.stringify({ ok: true, warmed: true, note: "pinged" }), {
      headers: { "Content-Type": "application/json" },
    });
  }
};
