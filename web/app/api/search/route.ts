import { NextRequest, NextResponse } from "next/server";
import { proxyGet } from "@/lib/api";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  const q = request.nextUrl.searchParams.get("q")?.trim();
  const mode = request.nextUrl.searchParams.get("mode") ?? "images";
  const movements = request.nextUrl.searchParams.get("movements") ?? undefined;
  const k = Number(request.nextUrl.searchParams.get("k") ?? "24");

  if (!q) {
    return NextResponse.json({ error: "A query is required." }, { status: 400 });
  }

  const path = mode === "text" ? "/search/text" : "/search/images";
  const params: Record<string, string | number | undefined> = { q, k };
  // Movement filtering only applies to the image (CLIP) index.
  if (mode !== "text" && movements) params.movements = movements;

  const result = await proxyGet(path, params);
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: result.status });
  }
  return NextResponse.json(result.data);
}
