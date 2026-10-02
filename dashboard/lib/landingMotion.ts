/** Pointer depth in CSS pixels. Scroll and idle sweep are separate. */
export const LANDING_DEPTH = {
  foreground: 24,
  primary: 16,
  secondary: 10,
  background: 4,
} as const;

export const HERO_CYCLE_MS = 4000;

export interface MotionPolicy {
  pointer: boolean;
  sweep: boolean;
  entry: boolean;
  scroll: boolean;
  scale: number;
  cycle: boolean;
}

export function motionPolicy(input: { reduce: boolean; finePointer: boolean; tablet: boolean }): MotionPolicy {
  if (input.reduce) {
    return { pointer: false, sweep: false, entry: false, scroll: false, scale: 0, cycle: false };
  }
  if (!input.finePointer) {
    return { pointer: false, sweep: false, entry: true, scroll: true, scale: 0, cycle: true };
  }
  if (input.tablet) {
    return { pointer: true, sweep: false, entry: true, scroll: true, scale: 0.5, cycle: true };
  }
  return { pointer: true, sweep: false, entry: true, scroll: true, scale: 1, cycle: true };
}

/** Hero domain advances only while motion is allowed and the hero is not held. */
export function heroShouldAdvance(input: { reduce: boolean; paused: boolean }): boolean {
  return !input.reduce && !input.paused;
}
