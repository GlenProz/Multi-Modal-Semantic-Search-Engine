type Props = {
  movement?: string | null;
  confidence?: number | null;
  anachronistic?: boolean | null;
};

function confidenceStyle(conf: number): { dot: string; label: string } {
  if (conf >= 0.5) return { dot: "bg-emerald-500", label: "text-emerald-700 dark:text-emerald-400" };
  if (conf >= 0.3) return { dot: "bg-amber-500", label: "text-amber-700 dark:text-amber-400" };
  return { dot: "bg-rose-500", label: "text-rose-700 dark:text-rose-400" };
}

function prettyMovement(m: string): string {
  return m.replace(/_/g, " ");
}

export function MovementBadge({ movement, confidence, anachronistic }: Props) {
  if (!movement) {
    return null;
  }
  const conf = confidence ?? 0;
  const style = confidenceStyle(conf);
  return (
    <div className="flex items-center gap-1.5 text-xs">
      <span className={`h-1.5 w-1.5 rounded-full ${style.dot} shrink-0`} />
      <span className={`font-medium capitalize ${style.label}`}>
        {prettyMovement(movement)}
      </span>
      <span className="text-[11px] text-stone-400 dark:text-stone-500 font-mono">
        {Math.round(conf * 100)}%
      </span>
      {Boolean(anachronistic) && (
        <span
          title="Historically anachronistic — the predicted movement falls outside the artwork's documented date range"
          className="cursor-help rounded bg-amber-500/10 px-1 text-[10px] text-amber-600 dark:text-amber-400 font-medium"
        >
          ⚠️ Out of era
        </span>
      )}
    </div>
  );
}
