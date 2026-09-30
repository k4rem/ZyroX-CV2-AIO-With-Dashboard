import React from "react";

export default function GuildLoading() {
  return (
    <div className="space-y-4" aria-busy="true" aria-label="Loading">
      <div className="h-7 w-48 animate-pulse rounded-md bg-surface-2" />
      <div className="h-4 w-full max-w-md animate-pulse rounded-md bg-surface-2" />
      <div className="space-y-3 pt-2">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-20 w-full animate-pulse rounded-md border border-line bg-surface-1" />
        ))}
      </div>
    </div>
  );
}
