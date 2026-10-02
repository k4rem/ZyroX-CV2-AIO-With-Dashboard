"use client";

import type { KeyboardEvent, ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { ErrorState } from "@/components/ui/state";
import { PAGE_SIZES, pageNumbers, type PageSize } from "@/lib/pagination";
import { cn } from "@/lib/utils";

export type DataColumn<T> = {
  key: string;
  header: string;
  cell: (row: T) => ReactNode;
};

export function DataTable<T>({
  rows,
  columns,
  getRowId,
  page,
  pages,
  pageSize,
  total,
  loading,
  error,
  onRetry,
  onPageChange,
  onPageSizeChange,
  selectedId,
  onSelect,
  emptyTitle = "Nothing to show",
  emptyDescription = "No rows match this view.",
}: {
  rows: T[];
  columns: DataColumn<T>[];
  getRowId: (row: T) => string;
  page: number;
  pages: number;
  pageSize: PageSize;
  total: number;
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: PageSize) => void;
  selectedId?: string | null;
  onSelect?: (id: string) => void;
  emptyTitle?: string;
  emptyDescription?: string;
}) {
  const numbers = pageNumbers(page, pages);

  function onKey(event: KeyboardEvent<HTMLTableSectionElement>) {
    if (!onSelect || (event.key !== "ArrowDown" && event.key !== "ArrowUp")) return;
    event.preventDefault();
    const ids = rows.map(getRowId);
    const index = selectedId ? ids.indexOf(selectedId) : -1;
    const next = event.key === "ArrowDown" ? Math.min(ids.length - 1, index + 1) : Math.max(0, index - 1);
    const id = ids[next];
    if (id) onSelect(id);
  }

  return (
    <div className="border border-line bg-surface-1">
      {error ? (
        <ErrorState
          title="This table could not be loaded"
          description={error}
          actions={onRetry ? <Button type="button" onClick={onRetry}>Retry</Button> : undefined}
        />
      ) : (
        <div className="overflow-auto">
          <table className="w-full text-small">
            <thead>
              <tr className="border-b border-line text-start text-fg-3">
                {columns.map((column) => (
                  <th key={column.key} className="px-3 py-2 text-start font-medium">{column.header}</th>
                ))}
              </tr>
            </thead>
            <tbody onKeyDown={onKey}>
              {loading ? (
                <tr>
                  <td colSpan={columns.length} className="px-3 py-6 text-fg-3">Loading…</td>
                </tr>
              ) : rows.length === 0 ? (
                <tr>
                  <td colSpan={columns.length} className="px-3 py-6">
                    <p className="text-fg-1">{emptyTitle}</p>
                    <p className="text-fg-3">{emptyDescription}</p>
                  </td>
                </tr>
              ) : (
                rows.map((row) => {
                  const id = getRowId(row);
                  const selected = selectedId === id;
                  return (
                    <tr
                      key={id}
                      tabIndex={0}
                      aria-selected={selected}
                      data-state={selected ? "selected" : undefined}
                      className={cn("border-b border-line-subtle outline-none focus-visible:bg-surface-3", selected && "bg-surface-3")}
                      onClick={() => onSelect?.(id)}
                    >
                      {columns.map((column) => (
                        <td key={column.key} className="px-3 py-2 text-fg-1">{column.cell(row)}</td>
                      ))}
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      )}
      <footer className="flex flex-wrap items-center justify-between gap-2 border-t border-line px-3 py-2">
        <p className="text-caption text-fg-3">{total} rows</p>
        <div className="flex flex-wrap items-center gap-1">
          {PAGE_SIZES.map((size) => (
            <Button key={size} type="button" variant={size === pageSize ? "secondary" : "ghost"} className="h-7 px-2" onClick={() => onPageSizeChange(size)}>
              {size}
            </Button>
          ))}
          {numbers.map((number) => (
            <Button key={number} type="button" variant={number === page ? "secondary" : "ghost"} className="h-7 w-7 px-0" onClick={() => onPageChange(number)}>
              {number}
            </Button>
          ))}
        </div>
      </footer>
    </div>
  );
}
