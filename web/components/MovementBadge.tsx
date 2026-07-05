type Props = {
  movement: string;
  confidence: number;
  anachronistic: boolean;
};

// Confidence tiers mirror the project's 🟢/🟡/🔴 semantics: how much to trust
// the WikiArt classifier's movement label for this artwork.
function confidenceStyle(conf: number): { dot: string; label: string } {
  if (conf >= 0.5) return { dot: "bg-emerald-500", label: "text-emerald-600 dark:text-emerald-400" };
  if (conf >= 0.3) return { dot: "bg-amber-500", label: "text-amber-600 dark:text-amber-400" };
  return { dot: "bg-red-500", label: "text-red-600 dark:text-red-400" };
}

function prettyMovement(m: string): string {
  return m.replace(/_/g, " ");
}

export function MovementBadge({ movement, confidence, anachronistic }: Props) {
  const style = confidenceStyle(confidence);
  return (
    <div className="flex items-center gap-1.5 text-xs">
      <span className={`h-2 w-2 rounded-full ${style.dot}`} />
      <span className={`font-medium capitalize ${style.label}`}>
        {prettyMovement(movement)}
      </span>
      <span className="text-zinc-400 dark:text-zinc-500">
        {Math.round(confidence * 100)}%
      </span>
      {anachronistic && (
        <span
          title="Historically anachronistic — the movement label falls outside this artwork's date range"
          className="text-amber-500"
        >
          ⚠️
        </span>
      )}
    </div>
  );
}
