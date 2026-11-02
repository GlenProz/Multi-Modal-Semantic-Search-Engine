import { NextResponse } from "next/server";
import { getApiBase } from "@/lib/api";

export const dynamic = "force-dynamic";
// Allow enough time for a cold Space to wake and load its collections.
export const maxDuration = 60;

// Hit by a daily Vercel cron (see vercel.json) to keep the free Hugging Face
// Space from hitting its 48h idle-sleep threshold. Even if the Space was
// asleep, this request wakes it and resets the timer.
export async function GET() {
  const base = getApiBase();
  if (!base) {
    return NextResponse.json({ ok: false, error: "ART_API_URL unset" }, { status: 503 });
  }
  try {
    const res = await fetch(`${base}/health`, {
      signal: AbortSignal.timeout(55_000),
    });
    return NextResponse.json({ ok: res.ok, warmed: true });
  } catch {
    // The request still reached HF and reset the idle timer, so this is a
    // "success" for keep-warm purposes even if we timed out waiting.
    return NextResponse.json({ ok: true, warmed: true, note: "pinged (no wait)" });
  }
}
