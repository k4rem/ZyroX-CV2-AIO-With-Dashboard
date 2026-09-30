/**
 * ╔══════════════════════════════════════════════════════════════════╗
 * ║                                                                  ║
 * ║   ░█▀▀░█▀█░█▀▄░█▀▀░█░█   ░█▀▄░█▀▀░█░█░█▀▀                     ║
 * ║   ░█░░░█░█░█░█░█▀▀░▄▀▄   ░█░█░█▀▀░▀▄▀░▀▀█                     ║
 * ║   ░▀▀▀░▀▀▀░▀▀░░▀▀▀░▀░▀   ░▀▀░░▀▀▀░░▀░░▀▀▀                     ║
 * ║                                                                  ║
 * ║           © 2026 CodeX Devs — All Rights Reserved               ║
 * ║                                                                  ║
 * ║   discord  ──  https://discord.gg/codexdev                      ║
 * ║   youtube  ──  https://youtube.com/@CodeXDevs                   ║
 * ║   github   ──  https://github.com/RayExo                        ║
 * ║                                                                  ║
 * ╚══════════════════════════════════════════════════════════════════╝
 */

import type { Config } from "tailwindcss";

// CLS OS tokens live in app/globals.css as RGB channel triplets (DS §4.7).
// This file only maps them to Tailwind names.
const rgb = (token: string) => `rgb(var(--cls-${token}) / <alpha-value>)`;

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    screens: {
      sm: "640px",
      md: "768px",
      lg: "1024px",
      xl: "1280px",
      "2xl": "1536px",
      "3xl": "1920px",
      "4xl": "2560px",
    },
    extend: {
      colors: {
        void: rgb("bg-void"),
        chrome: rgb("bg-chrome"),
        canvas: rgb("bg-canvas"),
        surface: {
          1: rgb("surface-1"),
          2: rgb("surface-2"),
          3: rgb("surface-3"),
          4: rgb("surface-4"),
          well: rgb("surface-well"),
        },
        line: {
          subtle: rgb("line-subtle"),
          DEFAULT: rgb("line"),
          strong: rgb("line-strong"),
          input: rgb("line-input"),
        },
        brand: {
          300: rgb("brand-300"),
          400: rgb("brand-400"),
          500: rgb("brand-500"),
          600: rgb("brand-600"),
          700: rgb("brand-700"),
        },
        fg: {
          1: rgb("fg-1"),
          2: rgb("fg-2"),
          3: rgb("fg-3"),
          4: rgb("fg-4"),
        },
        ok: rgb("ok"),
        warn: rgb("warn"),
        danger: {
          DEFAULT: rgb("danger"),
          fill: rgb("danger-fill"),
          "fill-hover": rgb("danger-fill-hover"),
          "fill-active": rgb("danger-fill-active"),
        },
        info: rgb("info"),
        neutral: rgb("neutral"),
        sev: {
          critical: rgb("danger"),
          high: rgb("sev-high"),
          medium: rgb("warn"),
          low: rgb("neutral"),
        },
        chart: {
          1: rgb("brand-400"),
          2: rgb("chart-2"),
          3: rgb("chart-3"),
          4: rgb("chart-4"),
        },
        // Legacy aliases so pre-CLS module pages keep rendering until Task C
        // migrates them. `primary` is now the CLS brand, never ZyroX red.
        primary: {
          DEFAULT: rgb("brand-600"),
          hover: rgb("brand-500"),
          glow: "rgb(var(--cls-brand-500) / 0.35)",
        },
      },
      fontFamily: {
        sans: ["var(--cls-font-ui)"],
        mono: ["var(--cls-font-mono)"],
        display: ["var(--cls-font-display)"],
      },
      fontSize: {
        // Dashboard scale (DS §5.2): fixed rem, no fluid type.
        "page-title": ["1.25rem", { lineHeight: "1.75rem", letterSpacing: "-0.01em", fontWeight: "600" }],
        section: ["0.9375rem", { lineHeight: "1.375rem", fontWeight: "600" }],
        "panel-title": ["0.8125rem", { lineHeight: "1.25rem", fontWeight: "600" }],
        body: ["0.8125rem", { lineHeight: "1.25rem" }],
        "body-prose": ["0.875rem", { lineHeight: "1.375rem" }],
        small: ["0.75rem", { lineHeight: "1rem" }],
        caption: ["0.6875rem", { lineHeight: "1rem", letterSpacing: "0.01em" }],
        "kpi-sm": ["1.25rem", { lineHeight: "1.5rem", letterSpacing: "-0.01em", fontWeight: "600" }],
        kpi: ["1.75rem", { lineHeight: "2rem", letterSpacing: "-0.02em", fontWeight: "600" }],
      },
      borderRadius: {
        xs: "var(--cls-radius-xs)",
        sm: "var(--cls-radius-sm)",
        md: "var(--cls-radius-md)",
        lg: "var(--cls-radius-lg)",
      },
      boxShadow: {
        "hl-1": "var(--cls-hl-1)",
        "hl-2": "var(--cls-hl-2)",
        "elev-1": "var(--cls-hl-3), var(--cls-elev-1)",
        "elev-2": "var(--cls-hl-3), var(--cls-elev-2)",
        "glow-g1": "var(--cls-glow-g1)",
        "glow-g2": "var(--cls-glow-g2)",
        "glow-d2": "var(--cls-glow-d2)",
        well: "inset 0 1px 2px rgb(0 0 0 / 0.5)",
      },
      zIndex: {
        sticky: "10",
        topbar: "30",
        sidebar: "40",
        scrim: "50",
        drawer: "60",
        modal: "70",
        popover: "80",
        toast: "90",
        tooltip: "100",
      },
      transitionDuration: {
        instant: "var(--cls-dur-instant)",
        micro: "var(--cls-dur-micro)",
        standard: "var(--cls-dur-standard)",
        emphasized: "var(--cls-dur-emphasized)",
      },
      transitionTimingFunction: {
        "cls-out": "var(--cls-ease-out)",
        "cls-in-out": "var(--cls-ease-in-out)",
        "cls-exit": "var(--cls-ease-exit)",
        "cls-emphasized": "var(--cls-ease-emphasized)",
      },
      height: {
        topbar: "var(--cls-topbar-h)",
      },
      minHeight: {
        topbar: "var(--cls-topbar-h)",
      },
      maxWidth: {
        content: "var(--cls-content-max)",
      },
    },
  },
  plugins: [],
};
export default config;
