import { NextResponse } from "next/server";
import { proxyGet } from "@/lib/api";

export const dynamic = "force-dynamic";

// Used by the UI to detect whether the backend is reachable / awake, and to
// show index counts.
export async function GET() {
  const result = await proxyGet("/health", {});
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: result.status });
  }
  return NextResponse.json(result.data);
}
