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
