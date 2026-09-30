/**
 * Official CLS Discord invite. Empty until the owner supplies a URL.
 * When empty, public UI must not render a Discord footer link.
 */
export const CLS_DISCORD_INVITE_URL = "" as const;

export function hasClsDiscordInvite(): boolean {
  return CLS_DISCORD_INVITE_URL.length > 0;
}
