"use client";

import * as React from "react";
import { motionPolicy } from "@/lib/landingMotion";

/**
 * Writes smoothed depth variables on the hero. No React state per frame.
 * Stops while the hero is off-screen or the tab is hidden.
 */
export function useLandingDepth<T extends HTMLElement>() {
  const ref = React.useRef<T>(null);

  React.useEffect(() => {
    const root = ref.current;
    if (!root) return;

    const reduceMq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const fineMq = window.matchMedia("(hover: hover) and (pointer: fine)");
    const tabletMq = window.matchMedia("(max-width: 1023px)");

    let nx = 0;
    let ny = 0;
    let tx = 0;
    let ty = 0;
    let glowX = 68;
    let glowY = 42;
    let targetGlowX = 68;
    let targetGlowY = 42;
    let scroll = 0;
    let targetScroll = 0;
    let raf = 0;
    let visible = true;
    let scale = 1;
    let pointer = false;
    let scrollOn = true;

    const applyPolicy = () => {
      const policy = motionPolicy({
        reduce: reduceMq.matches,
        finePointer: fineMq.matches,
        tablet: tabletMq.matches,
      });
      pointer = policy.pointer;
      scrollOn = policy.scroll;
      scale = policy.scale;
      root.dataset.motion = policy.entry || policy.scroll || policy.pointer ? "on" : "off";
      root.dataset.sweep = policy.sweep ? "on" : "off";
      root.style.setProperty("--cls-depth-scale", String(scale));
      if (!pointer) {
        tx = 0;
        ty = 0;
        targetGlowX = 68;
        targetGlowY = 42;
      }
      if (!scrollOn) targetScroll = 0;
    };

    const observer = new IntersectionObserver(
      (entries) => {
        visible = entries[0]?.isIntersecting ?? true;
        root.dataset.depthPaused = visible && document.visibilityState === "visible" ? "false" : "true";
        if (visible) kick();
      },
      { threshold: 0.08 },
    );
    observer.observe(root);

    const onVisibility = () => {
      root.dataset.depthPaused = visible && document.visibilityState === "visible" ? "false" : "true";
      if (document.visibilityState === "visible") kick();
    };

    const onMove = (event: PointerEvent) => {
      if (!pointer || !visible) return;
      const rect = root.getBoundingClientRect();
      if (rect.width < 1 || rect.height < 1) return;
      const px = (event.clientX - rect.left) / rect.width;
      const py = (event.clientY - rect.top) / rect.height;
      tx = Math.max(-1, Math.min(1, (px - 0.5) * 2));
      ty = Math.max(-1, Math.min(1, (py - 0.5) * 2));
      targetGlowX = Math.max(28, Math.min(72, px * 100));
      targetGlowY = Math.max(24, Math.min(76, py * 100));
      kick();
    };

    const onScroll = () => {
      if (!scrollOn) return;
      const rect = root.getBoundingClientRect();
      const distance = rect.height || 1;
      targetScroll = Math.max(0, Math.min(1, -rect.top / (distance * 0.85)));
      kick();
    };

    const frame = () => {
      raf = 0;
      const paused = root.dataset.depthPaused === "true";
      if (paused) return;
      nx += (tx - nx) * 0.08;
      ny += (ty - ny) * 0.08;
      glowX += (targetGlowX - glowX) * 0.08;
      glowY += (targetGlowY - glowY) * 0.08;
      scroll += (targetScroll - scroll) * 0.12;
      root.style.setProperty("--cls-nx", nx.toFixed(4));
      root.style.setProperty("--cls-ny", ny.toFixed(4));
      root.style.setProperty("--cls-glow-x", `${glowX.toFixed(2)}%`);
      root.style.setProperty("--cls-glow-y", `${glowY.toFixed(2)}%`);
      root.style.setProperty("--cls-scroll", scroll.toFixed(4));
      const moving =
        Math.abs(tx - nx) > 0.004 ||
        Math.abs(ty - ny) > 0.004 ||
        Math.abs(targetGlowX - glowX) > 0.15 ||
        Math.abs(targetScroll - scroll) > 0.004;
      if (moving) raf = requestAnimationFrame(frame);
    };

    const kick = () => {
      if (!raf && root.dataset.depthPaused !== "true") raf = requestAnimationFrame(frame);
    };

    applyPolicy();
    onScroll();
    reduceMq.addEventListener("change", applyPolicy);
    fineMq.addEventListener("change", applyPolicy);
    tabletMq.addEventListener("change", applyPolicy);
    window.addEventListener("pointermove", onMove, { passive: true });
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", applyPolicy);
    document.addEventListener("visibilitychange", onVisibility);

    return () => {
      observer.disconnect();
      reduceMq.removeEventListener("change", applyPolicy);
      fineMq.removeEventListener("change", applyPolicy);
      tabletMq.removeEventListener("change", applyPolicy);
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", applyPolicy);
      document.removeEventListener("visibilitychange", onVisibility);
      if (raf) cancelAnimationFrame(raf);
    };
  }, []);

  return ref;
}
