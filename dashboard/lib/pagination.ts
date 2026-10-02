export const PAGE_SIZES = [25, 50, 100] as const;
export type PageSize = (typeof PAGE_SIZES)[number];
export const DEFAULT_PAGE_SIZE: PageSize = 25;

export function parsePageSize(value: string | number | null | undefined): PageSize {
  const size = Number(value);
  if (size === 50 || size === 100) return size;
  return DEFAULT_PAGE_SIZE;
}

export function parsePage(value: string | number | null | undefined): number {
  const page = Math.floor(Number(value));
  if (!Number.isFinite(page) || page < 1) return 1;
  return page;
}

export function pageCount(total: number, pageSize: number): number {
  if (total <= 0) return 1;
  return Math.ceil(total / pageSize);
}

/** The slice a server handler returns. The table renders `rows` and does not slice again. */
export function serverPage<T>(items: T[], page: number, pageSize: PageSize) {
  const total = items.length;
  const pages = pageCount(total, pageSize);
  const current = Math.min(Math.max(1, page), pages);
  const start = (current - 1) * pageSize;
  return {
    rows: items.slice(start, start + pageSize),
    total,
    page: current,
    pageSize,
    pages,
  };
}

export function pageNumbers(page: number, pages: number): number[] {
  const start = Math.max(1, page - 2);
  const end = Math.min(pages, start + 4);
  const from = Math.max(1, end - 4);
  const out: number[] = [];
  for (let n = from; n <= end; n += 1) out.push(n);
  return out;
}

export function tableQuery(search: URLSearchParams, patch: { page?: number; size?: PageSize; q?: string | null }) {
  const next = new URLSearchParams(search);
  if (patch.page != null) next.set("page", String(patch.page));
  if (patch.size != null) next.set("size", String(patch.size));
  if (patch.q != null) {
    if (patch.q) next.set("q", patch.q);
    else next.delete("q");
  }
  return next;
}
