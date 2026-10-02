/** Pointer depth in CSS pixels. Scroll and idle sweep are separate. */
export const LANDING_DEPTH = {
  foreground: 24,
  primary: 16,
  secondary: 10,
  background: 4,
} as const;

export interface MotionPolicy {
  pointer: boolean;
  sweep: boolean;
  entry: boolean;
  scroll: boolean;
  scale: number;
}

export function motionPolicy(input: { reduce: boolean; finePointer: boolean; tablet: boolean }): MotionPolicy {
  if (input.reduce) {
    return { pointer: false, sweep: false, entry: false, scroll: false, scale: 0 };
  }
  if (!input.finePointer) {
    return { pointer: false, sweep: false, entry: true, scroll: true, scale: 0 };
  }
  if (input.tablet) {
    return { pointer: true, sweep: true, entry: true, scroll: true, scale: 0.5 };
  }
  return { pointer: true, sweep: true, entry: true, scroll: true, scale: 1 };
}
