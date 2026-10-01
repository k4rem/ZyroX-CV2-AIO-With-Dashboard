/**
 * A small Discord markdown subset. Output is a data tree, never HTML, so
 * message text cannot inject markup.
 */

export type MdInline =
  | { type: "text"; text: string }
  | { type: "strong" | "em" | "u" | "s" | "spoiler"; children: MdInline[] }
  | { type: "code"; text: string }
  | { type: "link"; href: string; children: MdInline[] }
  | { type: "mention"; kind: "user" | "role" | "channel"; id: string };

export type MdBlock =
  | { type: "paragraph"; children: MdInline[] }
  | { type: "heading"; level: 1 | 2 | 3; children: MdInline[] }
  | { type: "list"; items: MdInline[][] }
  | { type: "code"; text: string };

const MAX = 8000;

function parseInline(source: string): MdInline[] {
  const out: MdInline[] = [];
  let i = 0;
  let buf = "";
  const flush = () => {
    if (buf) {
      out.push({ type: "text", text: buf });
      buf = "";
    }
  };
  const pushWrapped = (type: "strong" | "em" | "u" | "s" | "spoiler", marker: string) => {
    const end = source.indexOf(marker, i + marker.length);
    if (end === -1) return false;
    flush();
    out.push({ type, children: parseInline(source.slice(i + marker.length, end)) });
    i = end + marker.length;
    return true;
  };

  while (i < source.length) {
    if (source.startsWith("```", i)) {
      buf += "```";
      i += 3;
      continue;
    }
    if (source[i] === "`") {
      const end = source.indexOf("`", i + 1);
      if (end > i + 1) {
        flush();
        out.push({ type: "code", text: source.slice(i + 1, end) });
        i = end + 1;
        continue;
      }
    }
    if (source.startsWith("**", i) && pushWrapped("strong", "**")) continue;
    if (source.startsWith("__", i) && pushWrapped("u", "__")) continue;
    if (source.startsWith("~~", i) && pushWrapped("s", "~~")) continue;
    if (source.startsWith("||", i) && pushWrapped("spoiler", "||")) continue;
    if (source[i] === "*" && pushWrapped("em", "*")) continue;
    if (source[i] === "_" && pushWrapped("em", "_")) continue;
    if (source[i] === "[") {
      const match = /^\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/.exec(source.slice(i));
      if (match) {
        flush();
        out.push({ type: "link", href: match[2], children: parseInline(match[1]) });
        i += match[0].length;
        continue;
      }
    }
    const mention = /^<@&?(\d{17,20})>|^<#(\d{17,20})>/.exec(source.slice(i));
    if (mention) {
      flush();
      if (source.startsWith("<@&", i)) out.push({ type: "mention", kind: "role", id: mention[1] });
      else if (source.startsWith("<#", i)) out.push({ type: "mention", kind: "channel", id: mention[2] });
      else out.push({ type: "mention", kind: "user", id: mention[1] });
      i += mention[0].length;
      continue;
    }
    buf += source[i];
    i += 1;
  }
  flush();
  return out;
}

function blocksFromLines(chunk: string): MdBlock[] {
  const lines = chunk.replace(/\r\n/g, "\n").split("\n");
  const blocks: MdBlock[] = [];
  let para: string[] = [];
  const flushPara = () => {
    const text = para.join("\n").trim();
    para = [];
    if (text) blocks.push({ type: "paragraph", children: parseInline(text) });
  };
  let list: string[] | null = null;
  const flushList = () => {
    if (!list) return;
    blocks.push({ type: "list", items: list.map((item) => parseInline(item)) });
    list = null;
  };

  for (const line of lines) {
    const heading = /^(#{1,3})\s+(.+)$/.exec(line);
    const item = /^[-*]\s+(.+)$/.exec(line);
    if (heading) {
      flushPara();
      flushList();
      blocks.push({
        type: "heading",
        level: heading[1].length as 1 | 2 | 3,
        children: parseInline(heading[2]),
      });
      continue;
    }
    if (item) {
      flushPara();
      list = list ?? [];
      list.push(item[1]);
      continue;
    }
    flushList();
    if (line.trim() === "") flushPara();
    else para.push(line);
  }
  flushPara();
  flushList();
  return blocks;
}

export function parseDiscordMarkdown(source: string): MdBlock[] {
  const text = (source ?? "").slice(0, MAX);
  const parts = text.split("```");
  const blocks: MdBlock[] = [];
  parts.forEach((part, index) => {
    if (index % 2 === 1) {
      const body = part.replace(/^\w*\n/, "");
      blocks.push({ type: "code", text: body.replace(/\n$/, "") });
      return;
    }
    blocks.push(...blocksFromLines(part));
  });
  return blocks;
}

export function markdownHasHtml(blocks: MdBlock[]): boolean {
  const walk = (nodes: MdInline[]): boolean =>
    nodes.some((node) => {
      if (node.type === "text" || node.type === "code" || node.type === "mention") return false;
      if (node.type === "link") return walk(node.children);
      return walk(node.children);
    });
  return blocks.some((block) => {
    if (block.type === "code") return false;
    if (block.type === "list") return block.items.some(walk);
    return walk(block.children);
  });
}
