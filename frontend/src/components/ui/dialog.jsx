import * as React from "react"
import { X } from "lucide-react"
import { cn } from "@/lib/utils"

export function Dialog({ open, onOpenChange, children }) {
  React.useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape" && open) {
        onOpenChange?.(false)
      }
    }
    if (open) {
      document.body.style.overflow = "hidden"
      window.addEventListener("keydown", handleKeyDown)
    } else {
      document.body.style.overflow = ""
    }
    return () => {
      document.body.style.overflow = ""
      window.removeEventListener("keydown", handleKeyDown)
    }
  }, [open, onOpenChange])

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6"
      role="dialog"
      aria-modal="true"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-background/80 backdrop-blur-xs transition-opacity animate-in fade-in"
        onClick={() => onOpenChange?.(false)}
        aria-hidden="true"
      />
      {/* Modal Container */}
      <div className="relative z-50 w-full max-w-lg">
        {children}
      </div>
    </div>
  )
}

export const DialogContent = React.forwardRef(({ className, children, onClose, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "relative w-full rounded-lg border border-border bg-surface p-6 shadow-lg transition-all animate-in fade-in zoom-in-95",
      className
    )}
    {...props}
  >
    {children}
    {onClose && (
      <button
        type="button"
        onClick={onClose}
        className="absolute right-4 top-4 rounded-sm opacity-70 transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
        aria-label="Close dialog"
      >
        <X className="h-4 w-4" />
      </button>
    )}
  </div>
))
DialogContent.displayName = "DialogContent"

export function DialogHeader({ className, ...props }) {
  return <div className={cn("flex flex-col space-y-1.5 text-left mb-4", className)} {...props} />
}

export function DialogTitle({ className, ...props }) {
  return (
    <h3
      className={cn("text-lg font-semibold leading-none tracking-tight text-foreground", className)}
      {...props}
    />
  )
}

export function DialogDescription({ className, ...props }) {
  return <p className={cn("text-xs sm:text-sm text-muted-foreground", className)} {...props} />
}

export function DialogFooter({ className, ...props }) {
  return (
    <div
      className={cn("flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2 pt-4 border-t border-border/60 mt-4", className)}
      {...props}
    />
  )
}
