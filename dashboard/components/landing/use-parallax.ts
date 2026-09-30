"use client";

import * as React from "react";

/** Subtle ring parallax (DS §13.4). Pauses when off-screen or pointer idle. */
export function usePerimeterParallax(enabled: boolean) {
  const ref = React.useRef<HTMLDivElement>(null);
  const [offset, setOffset] = React.useState({ ox: 0, oy: 0, mx: 0, my: 0, ix: 0, iy: 0 });

  React.useEffect(() => {
    if (!enabled) return;
    const el = ref.current;
    if (!el) return;

    let raf = 0;
    let targetX = 0;
    let targetY = 0;
    let currentX = 0;
    let currentY = 0;
    let lastMove = 0;
    let visible = true;

    const observer = new IntersectionObserver(
      (entries) => {
        visible = entries[0]?.isIntersecting ?? true;
      },
      { threshold: 0.05 },
    );
    observer.observe(el);

    const onMove = (e: PointerEvent) => {
      const rect = el.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;
      const nx = Math.max(-1, Math.min(1, (e.clientX - cx) / (rect.width / 2)));
      const ny = Math.max(-1, Math.min(1, (e.clientY - cy) / (rect.height / 2)));
      targetX = nx;
      targetY = ny;
      lastMove = performance.now();
    };

    const tick = (t: number) => {
      const idle = t - lastMove > 120;
      const moving =
        visible &&
        !idle &&
        (Math.abs(targetX - currentX) > 0.002 || Math.abs(targetY - currentY) > 0.002);

      if (moving || !idle) {
        currentX += (targetX - currentX) * 0.12;
        currentY += (targetY - currentY) * 0.12;
        setOffset({
          ox: currentX * 2,
          oy: currentY * 2,
          mx: currentX * 3,
          my: currentY * 3,
          ix: currentX * 4,
          iy: currentY * 4,
        });
      }

      if (visible && (!idle || moving)) {
        raf = requestAnimationFrame(tick);
      } else {
        raf = 0;
      }
    };

    const kick = () => {
      if (!raf) raf = requestAnimationFrame(tick);
    };

    window.addEventListener("pointermove", onMove, { passive: true });
    window.addEventListener("pointermove", kick, { passive: true });
    lastMove = performance.now();
    raf = requestAnimationFrame(tick);

    return () => {
      observer.disconnect();
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointermove", kick);
      if (raf) cancelAnimationFrame(raf);
    };
  }, [enabled]);

  return { ref, offset };
}
