import * as React from "react"
import { cn } from "@/lib/utils"

export function DropdownMenu({ children }) {
  const [open, setOpen] = React.useState(false)
  const menuRef = React.useRef(null)

  React.useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setOpen(false)
      }
    }
    const handleKeyDown = (e) => {
      if (e.key === "Escape" && open) {
        setOpen(false)
      }
    }

    if (open) {
      document.addEventListener("mousedown", handleClickOutside)
      document.addEventListener("keydown", handleKeyDown)
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside)
      document.removeEventListener("keydown", handleKeyDown)
    }
  }, [open])

  return (
    <div className="relative inline-block text-left" ref={menuRef}>
      {typeof children === "function" ? children({ open, setOpen }) : children}
    </div>
  )
}

export const DropdownMenuTrigger = React.forwardRef(({ asChild, children, onClick, ...props }, ref) => {
  return (
    <div ref={ref} onClick={onClick} {...props}>
      {children}
    </div>
  )
})
DropdownMenuTrigger.displayName = "DropdownMenuTrigger"

export function DropdownMenuContent({ open, align = "right", className, children, ...props }) {
  if (!open) return null

  const alignmentClass = align === "left" ? "left-0" : "right-0"

  return (
    <div
      className={cn(
        "absolute z-50 mt-2 min-w-[12rem] rounded-md border border-border bg-surface p-1 shadow-md animate-in fade-in-80 zoom-in-95 focus:outline-none",
        alignmentClass,
        className
      )}
      role="menu"
      tabIndex={-1}
      {...props}
    >
      {children}
    </div>
  )
}

export const DropdownMenuItem = React.forwardRef(({ className, disabled, onClick, children, ...props }, ref) => (
  <button
    ref={ref}
    type="button"
    role="menuitem"
    disabled={disabled}
    onClick={onClick}
    className={cn(
      "relative flex w-full cursor-pointer select-none items-center rounded-sm px-2.5 py-1.5 text-xs text-foreground outline-none transition-colors hover:bg-muted/80 focus:bg-muted focus:text-foreground disabled:pointer-events-none disabled:opacity-50 text-left",
      className
    )}
    {...props}
  >
    {children}
  </button>
))
DropdownMenuItem.displayName = "DropdownMenuItem"

export function DropdownMenuSeparator({ className, ...props }) {
  return <div className={cn("-mx-1 my-1 h-px bg-border", className)} role="separator" {...props} />
}

export function DropdownMenuLabel({ className, ...props }) {
  return (
    <div
      className={cn("px-2.5 py-1.5 text-xs font-semibold text-muted-foreground", className)}
      {...props}
    />
  )
}
