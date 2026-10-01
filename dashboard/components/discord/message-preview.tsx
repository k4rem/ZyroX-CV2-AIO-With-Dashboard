"use client";

import React from "react";
import { applyVariables, type MessageDraft } from "@/lib/messagePayload";
import { mediaSrc } from "@/components/discord/media-field";

function text(value: string, values: Record<string, string>) {
  const rendered = applyVariables(value, values);
  return rendered.replace(/<t:(\d+):[a-zA-Z]>/g, (_, unix) =>
    new Date(Number(unix) * 1000).toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" }),
  );
}

export function DiscordMessagePreview({
  guildId,
  message,
  values,
  botName = "CLS",
}: {
  guildId: string;
  message: MessageDraft;
  values: Record<string, string>;
  botName?: string;
}) {
  return (
    <div className="rounded-md bg-[#313338] p-3 text-[13px] leading-snug text-[#dbdee1]">
      <div className="flex gap-3">
        <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-[#5865f2] text-sm font-semibold text-white">
          {botName.slice(0, 1)}
        </div>
        <div className="min-w-0 flex-1">
          <div className="mb-1 flex items-baseline gap-2">
            <span className="font-semibold text-white">{botName}</span>
            <span className="rounded-sm bg-[#5865f2] px-1 text-[10px] font-semibold text-white">APP</span>
          </div>
          {message.content.trim() && <p className="mb-2 whitespace-pre-wrap break-words">{text(message.content, values)}</p>}
          <div className="space-y-2">
            {message.embeds.map((embed, index) => {
              const image = mediaSrc(guildId, embed.image);
              const thumb = mediaSrc(guildId, embed.thumbnail);
              const authorIcon = mediaSrc(guildId, embed.author.icon);
              const footerIcon = mediaSrc(guildId, embed.footer.icon);
              const show = embed.title || embed.description || embed.fields.length || image || embed.author.name || embed.footer.text;
              if (!show) return null;
              return (
                <article key={index} className="max-w-[420px] overflow-hidden rounded bg-[#2b2d31]" style={{ borderLeft: `4px solid ${embed.color || "#9474ff"}` }}>
                  <div className="flex gap-3 p-3">
                    <div className="min-w-0 flex-1">
                      {embed.author.name && (
                        <div className="mb-1 flex items-center gap-2 text-xs text-white">
                          {authorIcon && (
                            // Discord CDN and authenticated uploads are not next/image sources.
                            // eslint-disable-next-line @next/next/no-img-element
                            <img src={text(authorIcon, values)} alt="" className="size-5 rounded-full" />
                          )}
                          <span>{text(embed.author.name, values)}</span>
                        </div>
                      )}
                      {embed.title && (
                        <div className="font-semibold text-white">
                          {embed.url ? (
                            <a href={embed.url} className="text-[#00a8fc]" target="_blank" rel="noreferrer">
                              {text(embed.title, values)}
                            </a>
                          ) : (
                            text(embed.title, values)
                          )}
                        </div>
                      )}
                      {embed.description && <p className="mt-1 whitespace-pre-wrap break-words">{text(embed.description, values)}</p>}
                      {embed.fields.length > 0 && (
                        <div className="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-3">
                          {embed.fields.map((field, fieldIndex) => (
                            <div key={fieldIndex} className={field.inline ? "min-w-0" : "col-span-full min-w-0"}>
                              <div className="text-xs font-semibold text-white">{text(field.name, values)}</div>
                              <div className="break-words">{text(field.value, values)}</div>
                            </div>
                          ))}
                        </div>
                      )}
                      {image && (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img src={text(image, values)} alt="" className="mt-2 max-h-48 rounded object-cover" />
                      )}
                      {(embed.footer.text || embed.timestamp) && (
                        <div className="mt-2 flex items-center gap-1 text-[11px] text-[#949ba4]">
                          {footerIcon && (
                            // eslint-disable-next-line @next/next/no-img-element
                            <img src={text(footerIcon, values)} alt="" className="size-4 rounded-full" />
                          )}
                          <span>{text(embed.footer.text, values)}</span>
                          {embed.footer.text && embed.timestamp && <span>·</span>}
                          {embed.timestamp && <span>{text(values.timestamp || "Today at 8:00 PM", values)}</span>}
                        </div>
                      )}
                    </div>
                    {thumb && (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={text(thumb, values)} alt="" className="size-16 shrink-0 rounded object-cover" />
                    )}
                  </div>
                </article>
              );
            })}
          </div>
          {message.buttons.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {message.buttons.map((button, index) => (
                <a key={index} href={button.url || "#"} className="rounded bg-[#4e5058] px-3 py-1.5 text-sm text-white" target="_blank" rel="noreferrer">
                  {button.emoji && !button.emoji.startsWith("<") ? `${button.emoji} ` : ""}
                  {button.emoji.startsWith("<") ? `:${button.emoji.split(":")[1] || "emoji"}: ` : ""}
                  {button.label || "Link"}
                </a>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
