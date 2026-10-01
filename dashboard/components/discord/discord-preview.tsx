"use client";

import { useEffect, useState } from "react";
import type { MdBlock, MdInline } from "@/lib/discordMarkdown";
import { parseDiscordMarkdown } from "@/lib/discordMarkdown";
import { previewClock, safeHttpUrl } from "@/lib/welcomeFormat";
import { cn } from "@/lib/utils";

function RichText({ text, warn }: { text: string; warn: Set<string> }) {
  const parts = text.split(/(\{\w+\})/g);
  return (
    <>
      {parts.map((part, index) => {
        const token = /^\{(\w+)\}$/.exec(part);
        if (token && warn.has(token[1].toLowerCase())) {
          return (
            <span key={index} className="border-b border-dashed border-warn">
              {part}
            </span>
          );
        }
        return <span key={index}>{part}</span>;
      })}
    </>
  );
}

function Inlines({ nodes, warn }: { nodes: MdInline[]; warn: Set<string> }) {
  return (
    <>
      {nodes.map((node, index) => {
        if (node.type === "text") return <RichText key={index} text={node.text} warn={warn} />;
        if (node.type === "code") {
          return (
            <code key={index} className="rounded-xs bg-black/30 px-1 font-mono text-[0.85em]">
              {node.text}
            </code>
          );
        }
        if (node.type === "mention") {
          const label = node.kind === "channel" ? "#channel" : node.kind === "role" ? "@role" : "@member";
          return (
            <span key={index} className="rounded-xs px-0.5 font-medium" style={{ background: "rgb(88 101 242 / 0.3)", color: "#c9cdfb" }}>
              {label}
            </span>
          );
        }
        if (node.type === "link") {
          return (
            <span key={index} className="underline" style={{ color: "var(--dp-link)" }}>
              <Inlines nodes={node.children} warn={warn} />
            </span>
          );
        }
        const Tag = node.type === "strong" ? "strong" : node.type === "em" ? "em" : node.type === "u" ? "u" : node.type === "s" ? "s" : "span";
        return (
          <Tag key={index}>
            <Inlines nodes={node.children} warn={warn} />
          </Tag>
        );
      })}
    </>
  );
}

function Blocks({ blocks, warn }: { blocks: MdBlock[]; warn: Set<string> }) {
  return (
    <div className="space-y-1 whitespace-pre-wrap break-words text-[0.9375rem] leading-5">
      {blocks.map((block, index) => {
        if (block.type === "code") {
          return (
            <pre key={index} className="overflow-x-auto rounded-sm bg-black/30 p-2 font-mono text-small">
              {block.text}
            </pre>
          );
        }
        if (block.type === "heading") {
          const Tag = block.level === 1 ? "h3" : block.level === 2 ? "h4" : "h5";
          return (
            <Tag key={index} className="font-semibold" style={{ color: "var(--dp-header)" }}>
              <Inlines nodes={block.children} warn={warn} />
            </Tag>
          );
        }
        if (block.type === "list") {
          return (
            <ul key={index} className="list-disc ps-5">
              {block.items.map((item, itemIndex) => (
                <li key={itemIndex}>
                  <Inlines nodes={item} warn={warn} />
                </li>
              ))}
            </ul>
          );
        }
        return (
          <p key={index}>
            <Inlines nodes={block.children} warn={warn} />
          </p>
        );
      })}
    </div>
  );
}

export interface DiscordEmbedPreview {
  title: string;
  description: string;
  color: string;
  authorName: string;
  authorIcon: string | null;
  footerText: string;
  footerIcon: string | null;
  thumbnail: string | null;
  image: string | null;
}

export function DiscordPreview({
  mode,
  channelName,
  botName,
  botAvatar,
  content,
  embed,
  warnTokens,
  width,
  note,
}: {
  mode: "channel" | "dm";
  channelName?: string;
  botName: string;
  botAvatar: string | null;
  content: string;
  embed?: DiscordEmbedPreview | null;
  warnTokens: string[];
  width: "desktop" | "mobile";
  note?: string;
}) {
  const [clock, setClock] = useState("Today");
  useEffect(() => {
    setClock(`Today at ${previewClock()}`);
  }, [content, embed?.title, embed?.description]);
  const warn = new Set(warnTokens.map((token) => token.toLowerCase()));
  const blocks = content.trim() ? parseDiscordMarkdown(content) : [];
  const column = width === "mobile" ? "max-w-[360px]" : "max-w-[520px]";

  return (
    <div className="flex h-full min-h-[420px] flex-col bg-stage p-4 sm:p-6">
      <p className="cls-overline">Discord preview</p>
      <div className={cn("discord-preview mx-auto mt-3 w-full overflow-hidden rounded-sm border border-line-subtle", column)}>
        {mode === "channel" ? (
          <div className="border-b px-3 py-2 text-small font-medium" style={{ borderColor: "#1e1f22", color: "var(--dp-header)" }}>
            # {channelName || "channel"}
          </div>
        ) : (
          <div className="border-b px-3 py-2 text-small font-medium" style={{ borderColor: "#1e1f22", color: "var(--dp-header)" }}>
            Direct message
          </div>
        )}
        <div className="flex gap-3 px-3 py-3">
          {botAvatar ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={botAvatar} alt="" className="size-10 shrink-0 rounded-full" />
          ) : (
            <span className="flex size-10 shrink-0 items-center justify-center rounded-full text-small font-semibold" style={{ background: "#1e1f22" }}>
              {(botName || "?").slice(0, 1)}
            </span>
          )}
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-baseline gap-1.5">
              <span className="text-body font-semibold" style={{ color: "var(--dp-header)" }}>
                {botName || "Bot"}
              </span>
              <span className="rounded-xs px-1 text-[10px] font-medium text-white" style={{ background: "var(--dp-blurple)" }}>
                APP
              </span>
              <span className="text-caption" style={{ color: "var(--dp-muted)" }}>
                {clock}
              </span>
            </div>
            {blocks.length > 0 ? (
              <div className="mt-1">
                <Blocks blocks={blocks} warn={warn} />
              </div>
            ) : null}
            {embed ? (
              <div className="mt-2 flex max-w-full overflow-hidden rounded-sm" style={{ background: "var(--dp-embed)" }}>
                <span className="w-1 shrink-0" style={{ background: embed.color }} />
                <div className="min-w-0 flex-1 p-3">
                  <div className="flex gap-3">
                    <div className="min-w-0 flex-1 space-y-1">
                      {embed.authorName ? (
                        <div className="flex items-center gap-2 text-small">
                          {embed.authorIcon ? (
                            // eslint-disable-next-line @next/next/no-img-element
                            <img src={embed.authorIcon} alt="" className="size-5 rounded-full" />
                          ) : null}
                          <span>{embed.authorName}</span>
                        </div>
                      ) : null}
                      {embed.title ? (
                        <p className="font-semibold" style={{ color: "var(--dp-header)" }}>
                          <RichText text={embed.title} warn={warn} />
                        </p>
                      ) : null}
                      {embed.description ? (
                        <Blocks blocks={parseDiscordMarkdown(embed.description)} warn={warn} />
                      ) : null}
                    </div>
                    {embed.thumbnail ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={embed.thumbnail} alt="" className="size-16 shrink-0 rounded-sm object-cover" />
                    ) : null}
                  </div>
                  {embed.image ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={embed.image} alt="" className="mt-2 max-h-48 w-full rounded-sm object-cover" />
                  ) : null}
                  <p className="mt-2 text-caption" style={{ color: "var(--dp-muted)" }}>
                    {embed.footerIcon ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={embed.footerIcon} alt="" className="me-1 inline size-4 rounded-full align-text-bottom" />
                    ) : null}
                    {embed.footerText ? `${embed.footerText} · ` : ""}
                    {clock}
                  </p>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </div>
      {note ? <p className="mx-auto mt-3 max-w-[520px] text-small text-fg-3">{note}</p> : null}
    </div>
  );
}
