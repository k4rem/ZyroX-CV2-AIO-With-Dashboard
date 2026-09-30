#!/usr/bin/env node
/**
 * Legacy-token report (Phase 1.6 plan §2). Report-only in Task A: always exits 0.
 * From Task C, pass --strict to fail when a listed file still carries navy-era tokens.
 *
 *   node scripts/check-legacy-tokens.mjs [--strict] [paths...]
 */
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";

const TOKENS = [
  ["slate-*", /\b(?:bg|text|border|ring|from|to|via|divide|fill|stroke|shadow)-slate-\d{2,3}\b/g],
  ["#141B2D", /#141B2D/gi],
  ["rounded-2xl/3xl", /\brounded-(?:2xl|3xl)\b/g],
  ["font-black", /\bfont-black\b/g],
  ["shadow-xl", /\bshadow-xl\b/g],
];

const args = process.argv.slice(2);
const strict = args.includes("--strict");
const roots = args.filter((a) => !a.startsWith("--"));
const cwd = process.cwd();
const targets = roots.length > 0 ? roots : ["app", "components"];

function* walk(path) {
  const st = statSync(path);
  if (st.isFile()) {
    if (/\.(tsx?|jsx?|css)$/.test(path)) yield path;
    return;
  }
  for (const name of readdirSync(path)) {
    if (name === "node_modules" || name.startsWith(".")) continue;
    yield* walk(join(path, name));
  }
}

const totals = Object.fromEntries(TOKENS.map(([k]) => [k, 0]));
const rows = [];
for (const root of targets) {
  for (const file of walk(root)) {
    const text = readFileSync(file, "utf8");
    const counts = {};
    let sum = 0;
    for (const [key, re] of TOKENS) {
      const n = text.match(re)?.length ?? 0;
      if (n > 0) {
        counts[key] = n;
        totals[key] += n;
        sum += n;
      }
    }
    if (sum > 0) rows.push({ file: relative(cwd, file).replaceAll("\\", "/"), sum, counts });
  }
}

rows.sort((a, b) => b.sum - a.sum);
for (const r of rows) {
  const detail = Object.entries(r.counts)
    .map(([k, n]) => `${k} ${n}`)
    .join(", ");
  console.log(`${String(r.sum).padStart(4)}  ${r.file}  (${detail})`);
}
console.log("");
console.log(`files: ${rows.length}`);
for (const [k, n] of Object.entries(totals)) console.log(`${k}: ${n}`);

if (strict && rows.length > 0) process.exit(1);
