import { NextResponse } from "next/server";
import { proxyGet } from "@/lib/api";

export const dynamic = "force-dynamic";

export async function GET() {
  const result = await proxyGet("/random-artwork", {});
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: result.status });
  }
  return NextResponse.json(result.data);
}
