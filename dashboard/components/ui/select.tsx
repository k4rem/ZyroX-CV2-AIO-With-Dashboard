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

"use client"

import * as React from "react"
import { ChevronDown, Check } from "lucide-react"
import { cn } from "@/lib/utils"

// Context for sub-components
const SelectContext = React.createContext<{
  value: string
  onValueChange: (value: string) => void
  isOpen: boolean
  setIsOpen: (open: boolean) => void
} | null>(null)

export interface SelectOption {
  value: string
  label: string
}

interface SelectProps {
  children?: React.ReactNode
  value: string
  onValueChange: (value: string) => void
  // Legacy props compatibility
  options?: SelectOption[]
  placeholder?: string
  className?: string
  disabled?: boolean
}

const Select = ({ children, value, onValueChange, options, placeholder, className, disabled }: SelectProps) => {
  const [isOpen, setIsOpen] = React.useState(false)
  const containerRef = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setIsOpen(false)
    }
    document.addEventListener("mousedown", handleClickOutside)
    document.addEventListener("keydown", handleKey)
    return () => {
      document.removeEventListener("mousedown", handleClickOutside)
      document.removeEventListener("keydown", handleKey)
    }
  }, [])

  // If options are provided, use the legacy rendering
  if (options) {
    const selectedOption = options.find((opt) => opt.value === value)
    return (
      <div className={cn("relative w-full", className)} ref={containerRef}>
        <button
          type="button"
          disabled={disabled}
          aria-haspopup="listbox"
          aria-expanded={isOpen}
          onClick={() => setIsOpen(!isOpen)}
          className={cn(
            "flex h-8 w-full items-center justify-between gap-2 rounded-sm border border-line-input bg-surface-well px-2.5 text-body text-fg-1 shadow-well transition-colors duration-micro hover:border-fg-3 focus-visible:border-brand-400 focus-visible:outline-brand-400 focus-visible:outline-offset-0 disabled:cursor-not-allowed disabled:border-line-subtle disabled:text-fg-4",
            isOpen && "border-brand-400"
          )}
        >
          <span className={cn("truncate", !selectedOption && "text-fg-3")}>
            {selectedOption ? selectedOption.label : placeholder}
          </span>
          <ChevronDown className={cn("h-4 w-4 text-fg-3 transition-transform duration-standard", isOpen && "rotate-180")} />
        </button>

        {isOpen && (
          <div className="cls-floating absolute top-full z-popover mt-1.5 w-full overflow-hidden p-1">
            <div role="listbox" className="max-h-60 overflow-y-auto overflow-x-hidden no-scrollbar">
              {options.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  role="option"
                  aria-selected={value === option.value}
                  onClick={() => {
                    onValueChange(option.value)
                    setIsOpen(false)
                  }}
                  className={cn(
                    "flex h-8 w-full items-center justify-between rounded-sm px-2 text-body transition-colors duration-micro hover:bg-surface-3",
                    value === option.value ? "text-fg-1" : "text-fg-2"
                  )}
                >
                  <span className="truncate">{option.label}</span>
                  {value === option.value && <Check className="h-4 w-4" />}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }

  // Otherwise, use the sub-component pattern
  return (
    <SelectContext.Provider value={{ value, onValueChange, isOpen, setIsOpen }}>
      <div className={cn("relative w-full", className)} ref={containerRef}>
        {children}
      </div>
    </SelectContext.Provider>
  )
}

const SelectTrigger = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement>
>(({ className, children, ...props }, ref) => {
  const context = React.useContext(SelectContext)
  if (!context) return null

  return (
    <button
      ref={ref}
      type="button"
      aria-haspopup="listbox"
      aria-expanded={context.isOpen}
      onClick={() => context.setIsOpen(!context.isOpen)}
      className={cn(
        "flex h-8 w-full items-center justify-between gap-2 rounded-sm border border-line-input bg-surface-well px-2.5 text-body text-fg-1 shadow-well transition-colors duration-micro hover:border-fg-3 focus-visible:border-brand-400 focus-visible:outline-brand-400 focus-visible:outline-offset-0 disabled:cursor-not-allowed disabled:border-line-subtle disabled:text-fg-4",
        context.isOpen && "border-brand-400",
        className
      )}
      {...props}
    >
      {children}
      <ChevronDown className={cn("h-4 w-4 text-fg-3 transition-transform duration-standard", context.isOpen && "rotate-180")} />
    </button>
  )
})
SelectTrigger.displayName = "SelectTrigger"

const SelectValue = ({ placeholder, className }: { placeholder?: string, className?: string }) => {
  const context = React.useContext(SelectContext)
  if (!context) return null
  return <span className={cn("truncate", !context.value && "text-fg-3", className)}>{context.value || placeholder}</span>
}

const SelectContent = ({ children, className }: { children: React.ReactNode, className?: string }) => {
  const context = React.useContext(SelectContext)
  if (!context || !context.isOpen) return null

  return (
    <div className={cn("cls-floating absolute top-full z-popover mt-1.5 w-full overflow-hidden p-1", className)}>
      <div role="listbox" className="max-h-60 overflow-y-auto overflow-x-hidden no-scrollbar">
        {children}
      </div>
    </div>
  )
}

const SelectItem = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement> & { value: string }
>(({ className, children, value, ...props }, ref) => {
  const context = React.useContext(SelectContext)
  if (!context) return null

  const isSelected = context.value === value

  return (
    <button
      ref={ref}
      type="button"
      role="option"
      aria-selected={isSelected}
      onClick={() => {
        context.onValueChange(value)
        context.setIsOpen(false)
      }}
      className={cn(
        "flex h-8 w-full items-center justify-between rounded-sm px-2 text-body transition-colors duration-micro hover:bg-surface-3",
        isSelected ? "text-fg-1" : "text-fg-2",
        className
      )}
      {...props}
    >
      <span className="truncate">{children}</span>
      {isSelected && <Check className="h-4 w-4" />}
    </button>
  )
})
SelectItem.displayName = "SelectItem"

export { Select, SelectTrigger, SelectValue, SelectContent, SelectItem }
