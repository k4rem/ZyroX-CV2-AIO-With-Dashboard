export const MENU_TYPES = [
  { value: "reaction", label: "Reaction" },
  { value: "button", label: "Buttons" },
  { value: "select", label: "Select menu" },
] as const;

export const MENU_MODES = [
  { value: "toggle", label: "Toggle", hint: "The interaction adds the role, or removes it if the member already has it." },
  { value: "add", label: "Add only", hint: "Members can take the role. The interaction does not remove it." },
  { value: "remove", label: "Remove only", hint: "The interaction removes the mapped role." },
  { value: "unique", label: "Unique", hint: "A member can hold only one role from this menu." },
] as const;

export function menuTypeLabel(value: string): string {
  return MENU_TYPES.find((item) => item.value === value)?.label || "Reaction";
}

export function menuModeLabel(value: string): string {
  return MENU_MODES.find((item) => item.value === value)?.label || "Toggle";
}

export const BUTTON_STYLES = [
  { value: "pair", label: "Add / Remove buttons", hint: "Each role gets an Enable button and a Disable button." },
  { value: "toggle", label: "Single Toggle", hint: "One button per role. The label says it toggles." },
] as const;

export function buttonStyleLabel(value: string): string {
  return BUTTON_STYLES.find((item) => item.value === value)?.label || "Single Toggle";
}

export function buttonOptionLimit(style: string, linkButtons = 0): number {
  const room = 25 - Math.max(0, linkButtons);
  return Math.max(0, Math.floor(room / (style === "pair" ? 2 : 1)));
}
