import { NextRequest, NextResponse } from "next/server";
import { proxyGet } from "@/lib/api";

export const dynamic = "force-dynamic";

// DINOv2 structural similarity — "find artworks that look like this one".
export async function GET(request: NextRequest) {
  const id = request.nextUrl.searchParams.get("id")?.trim();
  const k = Number(request.nextUrl.searchParams.get("k") ?? "24");

  if (!id) {
    return NextResponse.json({ error: "An artwork id is required." }, { status: 400 });
  }

  const result = await proxyGet("/search/visual", { id, k });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: result.status });
  }
  return NextResponse.json(result.data);
}
