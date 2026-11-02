import { NextRequest, NextResponse } from "next/server";
import { proxyGet } from "@/lib/api";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  const q = request.nextUrl.searchParams.get("q")?.trim();
  const mode = request.nextUrl.searchParams.get("mode") ?? "hybrid";
  const movements = request.nextUrl.searchParams.get("movements") ?? undefined;
  const k = Number(request.nextUrl.searchParams.get("k") ?? "24");

  if (!q) {
    return NextResponse.json({ error: "A query is required." }, { status: 400 });
  }

  const path = mode === "hybrid" ? "/search/hybrid" : mode === "text" ? "/search/text" : "/search/images";
  const params: Record<string, string | number | undefined> = { q, k };
  // Movement filtering applies to image and hybrid indexes.
  if (mode !== "text" && movements) params.movements = movements;

  const result = await proxyGet(path, params);
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: result.status });
  }
  return NextResponse.json(result.data);
}
