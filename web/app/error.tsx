"use client";

import { useEffect } from "react";

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Gallery UI caught an unexpected error:", error);
  }, [error]);

  return (
    <div className="mx-auto flex min-h-[60vh] max-w-xl flex-col items-center justify-center px-6 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-amber-500/10 text-2xl text-amber-800 dark:text-amber-400">
        🏛️
      </div>
      <h2 className="gallery-serif mt-5 text-2xl font-semibold text-stone-900 dark:text-stone-100">
        The gallery stumbled
      </h2>
      <p className="mt-2 text-sm text-stone-600 dark:text-stone-400">
        An unexpected display error occurred while rendering the collection. Your session and query can be restored.
      </p>
      {error.message && (
        <pre className="mt-4 max-w-full overflow-x-auto rounded-lg bg-stone-100 p-3 text-left font-mono text-xs text-stone-700 dark:bg-stone-900 dark:text-stone-300">
          {error.message}
        </pre>
      )}
      <button
        onClick={() => reset()}
        className="mt-6 rounded-xl bg-stone-900 px-6 py-2.5 text-sm font-medium text-stone-100 transition-colors hover:bg-amber-950 dark:bg-stone-100 dark:text-stone-900 dark:hover:bg-amber-100"
      >
        Reload Collection
      </button>
    </div>
  );
}
