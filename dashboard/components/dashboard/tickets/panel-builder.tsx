"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { asMessageDraft } from "@/lib/welcomeState";
import { emptyMessage, type MessageDraft } from "@/lib/messagePayload";
import { questionKindLabel } from "@/lib/ticketsModel";
import { PageHeader } from "@/components/dashboard/page-header";
import { TicketsNav } from "@/components/dashboard/tickets/tickets-nav";
import { MessageComposer, type ComposerSelection } from "@/components/discord/message-composer";
import { DiscordMessagePreview } from "@/components/discord/message-preview";
import { EmojiPicker, type GuildEmoji } from "@/components/discord/emoji-picker";
import { ChannelPicker, RolePicker, type ChannelOption } from "@/components/discord/channel-picker";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";

type Question = { label: string; kind: "short" | "paragraph"; required: boolean; placeholder: string; min_length: number; max_length: number };

function explain(err: unknown) {
  return err instanceof Error ? err.message : "The panel did not save.";
}

function questionsFrom(raw: unknown): Question[] {
  if (!Array.isArray(raw) || raw.length === 0) {
    return [
      { label: "Order number", kind: "short", required: true, placeholder: "", min_length: 1, max_length: 40 },
      { label: "Describe the issue", kind: "paragraph", required: false, placeholder: "", min_length: 0, max_length: 500 },
    ];
  }
  return raw.slice(0, 5).map((item) => ({
    label: String(item.label || "Question"),
    kind: item.kind === "paragraph" ? "paragraph" : "short",
    required: Boolean(item.required),
    placeholder: String(item.placeholder || ""),
    min_length: Number(item.min_length || 0),
    max_length: Number(item.max_length || (item.kind === "paragraph" ? 1000 : 100)),
  }));
}

export function PanelBuilder({
  guildId,
  panel,
  categories,
  roles,
  channels,
  emojis,
}: {
  guildId: string;
  panel: Record<string, any>;
  categories: Array<{ id: string; name: string }>;
  roles: Array<{ id: string; name: string }>;
  channels: ChannelOption[];
  emojis: GuildEmoji[];
}) {
  const router = useRouter();
  const [message, setMessage] = useState<MessageDraft>(panel.payload ? asMessageDraft(panel.payload) : { ...emptyMessage(), embeds: [{ ...emptyMessage().embeds[0], title: panel.title || "Contact us", description: panel.message || "" }] });
  const [selection, setSelection] = useState<ComposerSelection>({ kind: "embed", index: 0 });
  const [title, setTitle] = useState(String(panel.title || ""));
  const [buttonLabel, setButtonLabel] = useState(String(panel.button_label || "Open ticket"));
  const [emoji, setEmoji] = useState(String(panel.button_emoji || ""));
  const [style, setStyle] = useState(String(panel.button_style || "primary"));
  const [categoryId, setCategoryId] = useState(String(panel.category_id || categories[0]?.id || ""));
  const [channelId, setChannelId] = useState(String(panel.channel_id || ""));
  const [requiredRole, setRequiredRole] = useState(String((panel.required_role_ids || [])[0] || ""));
  const [blockedRole, setBlockedRole] = useState(String((panel.blocked_role_ids || [])[0] || ""));
  const [questions, setQuestions] = useState<Question[]>(questionsFrom(panel.questions));
  const [panelType, setPanelType] = useState(panel.panel_type === "select" ? "select" : "button");
  const [options, setOptions] = useState<Array<Record<string, any>>>(panel.options || []);
  const [rules, setRules] = useState<Array<Record<string, any>>>(panel.rules || []);
  const [busy, setBusy] = useState(false);
  const channelName = channels.find((channel) => channel.id === channelId)?.name;
  const synced = panel.published_at ? new Date(panel.published_at).toLocaleString() : "";

  const body = useMemo(() => ({
    category_id: categoryId,
    channel_id: channelId || null,
    clear_channel: !channelId,
    title,
    message: message.embeds[0]?.description || message.content || "",
    button_label: buttonLabel,
    button_emoji: emoji,
    button_style: style,
    required_role_ids: requiredRole ? [requiredRole] : [],
    blocked_role_ids: blockedRole ? [blockedRole] : [],
    questions,
    payload: message,
    panel_type: panelType,
    options,
    rules,
  }), [categoryId, channelId, title, message, buttonLabel, emoji, style, requiredRole, blockedRole, questions, panelType, options, rules]);

  function move(index: number, direction: -1 | 1) {
    const next = questions.slice();
    const target = index + direction;
    if (target < 0 || target >= next.length) return;
    const [item] = next.splice(index, 1);
    next.splice(target, 0, item);
    setQuestions(next);
  }

  async function save() {
    setBusy(true);
    try {
      await api.saveTicketPanel(guildId, panel.id, body);
      toast.success("Panel saved");
      router.refresh();
    } catch (err) {
      toast.error(explain(err));
    } finally {
      setBusy(false);
    }
  }

  async function publish(mode: string) {
    setBusy(true);
    try {
      await api.saveTicketPanel(guildId, panel.id, body);
      const saved = await api.publishTicketPanel(guildId, panel.id, { channel_id: channelId || null, mode });
      toast.success(saved.publish_status === "missing" ? "Discord message is missing" : "Published to Discord");
      router.refresh();
    } catch (err) {
      toast.error(explain(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <TicketsNav guildId={guildId} />
      <PageHeader title={title || "Panel"} description="Save keeps the draft. Publish sends it to Discord.">
        <Button type="button" variant="secondary" disabled={busy} onClick={() => void save()}>Save</Button>
        <Button type="button" disabled={busy || !channelId} onClick={() => void publish(panel.published_message_id ? "update" : "publish")}>{panel.published_message_id ? "Update message" : "Publish"}</Button>
        <Button type="button" variant="ghost" disabled={busy || !channelId} onClick={() => void publish("resend")}>Resend</Button>
      </PageHeader>
      <p className="mb-3 text-small text-fg-3">
        {panel.publish_status === "missing" ? "Message missing. Resend it to Discord." : panel.publish_status === "published" ? `Published in #${channelName || "channel"}${synced ? ` · Last synced ${synced}` : ""}` : "Draft. Nothing has been posted yet."}
      </p>
      <div className="grid items-start gap-3 xl:grid-cols-[18rem_minmax(0,1fr)_20rem]">
        <aside className="space-y-3 border border-line-subtle p-3">
          <Input value={title} onChange={(event) => setTitle(event.target.value)} aria-label="Panel title" placeholder="Panel title" />
          <Select value={categoryId} onValueChange={setCategoryId} placeholder="Ticket team" options={categories.map((item) => ({ value: item.id, label: item.name }))} />
          <ChannelPicker channels={channels} value={channelId} onChange={setChannelId} />
          <p className="text-caption text-fg-3">Required role</p>
          <RolePicker roles={roles} value={requiredRole} onChange={setRequiredRole} />
          <p className="text-caption text-fg-3">Blocked role</p>
          <RolePicker roles={roles} value={blockedRole} onChange={setBlockedRole} />
          <Input value={buttonLabel} onChange={(event) => setButtonLabel(event.target.value)} aria-label="Button label" placeholder="Button label" />
          <div className="flex items-center gap-2">
            <EmojiPicker value={emoji} emojis={emojis} onChange={setEmoji} />
            <Select value={style} onValueChange={setStyle} options={[{ value: "primary", label: "Primary" }, { value: "secondary", label: "Secondary" }, { value: "success", label: "Success" }, { value: "danger", label: "Danger" }]} />
          </div>
          <div className="space-y-2 border-t border-line-subtle pt-3">
            <div className="flex items-center justify-between">
              <p className="text-small text-fg-1">Form</p>
              <Button type="button" size="sm" variant="ghost" disabled={questions.length >= 5} onClick={() => setQuestions([...questions, { label: "Question", kind: "short", required: false, placeholder: "", min_length: 0, max_length: 100 }])}>Add</Button>
            </div>
            {questions.map((question, index) => (
              <div key={index} className="space-y-1 border border-line-subtle p-2">
                <Input value={question.label} aria-label={`Question ${index + 1}`} onChange={(event) => setQuestions(questions.map((item, itemIndex) => itemIndex === index ? { ...item, label: event.target.value } : item))} />
                <div className="flex flex-wrap gap-1 text-caption">
                  <button type="button" className={question.kind === "short" ? "text-fg-1" : "text-fg-3"} onClick={() => setQuestions(questions.map((item, itemIndex) => itemIndex === index ? { ...item, kind: "short", max_length: 100 } : item))}>Short</button>
                  <button type="button" className={question.kind === "paragraph" ? "text-fg-1" : "text-fg-3"} onClick={() => setQuestions(questions.map((item, itemIndex) => itemIndex === index ? { ...item, kind: "paragraph", max_length: 1000 } : item))}>Paragraph</button>
                  <button type="button" className="text-fg-3" onClick={() => setQuestions(questions.map((item, itemIndex) => itemIndex === index ? { ...item, required: !item.required } : item))}>{question.required ? "Required" : "Optional"}</button>
                  <button type="button" className="text-fg-3" onClick={() => move(index, -1)}>Up</button>
                  <button type="button" className="text-fg-3" onClick={() => move(index, 1)}>Down</button>
                  <button type="button" className="text-fg-3" onClick={() => setQuestions(questions.filter((_, itemIndex) => itemIndex !== index))}>Delete</button>
                  <button type="button" className="text-fg-3" disabled={questions.length >= 5} onClick={() => setQuestions([...questions.slice(0, index + 1), { ...question, label: `${question.label} copy` }, ...questions.slice(index + 1)].slice(0, 5))}>Duplicate</button>
                </div>
                <Input value={question.placeholder} placeholder="Placeholder" aria-label={`Placeholder ${index + 1}`} onChange={(event) => setQuestions(questions.map((item, itemIndex) => itemIndex === index ? { ...item, placeholder: event.target.value } : item))} />
                <div className="grid grid-cols-2 gap-1">
                  <Input type="number" value={question.min_length} aria-label={`Minimum length ${index + 1}`} onChange={(event) => setQuestions(questions.map((item, itemIndex) => itemIndex === index ? { ...item, min_length: Number(event.target.value) } : item))} />
                  <Input type="number" value={question.max_length} aria-label={`Maximum length ${index + 1}`} onChange={(event) => setQuestions(questions.map((item, itemIndex) => itemIndex === index ? { ...item, max_length: Number(event.target.value) } : item))} />
                </div>
              </div>
            ))}
          </div>
          <div className="space-y-2 border-t border-line-subtle pt-3">
            <p className="text-small text-fg-1">Panel type</p>
            <Select value={panelType} onValueChange={setPanelType} options={[{ value: "button", label: "Button" }, { value: "select", label: "Select menu" }]} />
            {panelType === "select" && options.map((option, index) => (
              <div key={index} className="space-y-1 border border-line-subtle p-2">
                <Input value={option.label || ""} aria-label={`Option ${index + 1}`} placeholder="Billing" onChange={(event) => setOptions(options.map((item, itemIndex) => itemIndex === index ? { ...item, label: event.target.value } : item))} />
                <Input value={option.description || ""} aria-label={`Option description ${index + 1}`} placeholder="Description" onChange={(event) => setOptions(options.map((item, itemIndex) => itemIndex === index ? { ...item, description: event.target.value } : item))} />
                <EmojiPicker value={option.emoji || ""} emojis={emojis} onChange={(value) => setOptions(options.map((item, itemIndex) => itemIndex === index ? { ...item, emoji: value } : item))} />
                <Select value={option.category_id || ""} onValueChange={(value) => setOptions(options.map((item, itemIndex) => itemIndex === index ? { ...item, category_id: value } : item))} placeholder="Team" options={categories.map((item) => ({ value: item.id, label: item.name }))} />
                <button type="button" className="text-caption text-fg-3" onClick={() => setOptions(options.filter((_, itemIndex) => itemIndex !== index))}>Remove</button>
              </div>
            ))}
            {panelType === "select" && <Button type="button" size="sm" variant="ghost" disabled={options.length >= 25} onClick={() => setOptions([...options, { label: "", description: "", emoji: "", category_id: categoryId, questions: [] }])}>Add option</Button>}
          </div>
          <div className="space-y-2 border-t border-line-subtle pt-3">
            <p className="text-small text-fg-1">Routing</p>
            {rules.map((rule, index) => (
              <div key={index} className="grid gap-1">
                <Input value={rule.question_label || ""} aria-label={`Route question ${index + 1}`} placeholder="Issue type" onChange={(event) => setRules(rules.map((item, itemIndex) => itemIndex === index ? { ...item, question_label: event.target.value } : item))} />
                <Select value={rule.operator || "equals"} onValueChange={(value) => setRules(rules.map((item, itemIndex) => itemIndex === index ? { ...item, operator: value } : item))} options={[{ value: "equals", label: "Equals" }, { value: "contains", label: "Contains" }]} />
                <Input value={rule.value || ""} aria-label={`Route answer ${index + 1}`} placeholder="Billing" onChange={(event) => setRules(rules.map((item, itemIndex) => itemIndex === index ? { ...item, value: event.target.value } : item))} />
                <Select value={rule.category_id || ""} onValueChange={(value) => setRules(rules.map((item, itemIndex) => itemIndex === index ? { ...item, category_id: value } : item))} placeholder="Route to" options={categories.map((item) => ({ value: item.id, label: item.name }))} />
                <button type="button" className="text-caption text-fg-3" onClick={() => setRules(rules.filter((_, itemIndex) => itemIndex !== index))}>Remove rule</button>
              </div>
            ))}
            <Button type="button" size="sm" variant="ghost" disabled={rules.length >= 12} onClick={() => setRules([...rules, { question_label: questions[0]?.label || "Issue type", operator: "equals", value: "", category_id: categoryId }])}>Add rule</Button>
          </div>
        </aside>
        <MessageComposer guildId={guildId} message={message} onChange={setMessage} emojis={emojis} values={{}} selection={selection} onSelect={setSelection} showPreview={false} />
        <aside className="space-y-3 xl:sticky xl:top-3">
          <p className="text-caption uppercase tracking-wide text-fg-3">Member preview</p>
          <DiscordMessagePreview guildId={guildId} message={message} values={{}} />
          <div className="inline-flex items-center gap-1 border border-line-subtle px-2 py-1 text-small text-fg-1">
            <span>{emoji}</span>
            <span>{buttonLabel || "Open ticket"}</span>
          </div>
          <div className="border border-line-subtle p-3">
            <p className="mb-2 text-small text-fg-1">{title || "Ticket"}</p>
            {questions.map((question, index) => (
              <div key={index} className="mb-2">
                <p className="text-caption text-fg-2">{question.label}{question.required ? "" : " · optional"} · {questionKindLabel(question.kind)}</p>
                <div className={`mt-1 border border-line-subtle bg-surface-1 ${question.kind === "paragraph" ? "h-16" : "h-8"}`} />
              </div>
            ))}
          </div>
        </aside>
      </div>
    </div>
  );
}
