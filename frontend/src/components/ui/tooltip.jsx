import * as React from "react"
import { cn } from "@/lib/utils"

export function Tooltip({ text, children, className }) {
  const [visible, setVisible] = React.useState(false)
  const id = React.useId()

  return (
    <div
      className="relative inline-flex items-center"
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      onFocus={() => setVisible(true)}
      onBlur={() => setVisible(false)}
      aria-describedby={visible ? id : undefined}
    >
      {children}
      {visible && (
        <div
          id={id}
          role="tooltip"
          className={cn(
            "absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 z-50 whitespace-nowrap rounded-md bg-foreground px-2 py-1 text-[11px] font-medium text-background shadow-sm animate-in fade-in-50 zoom-in-95 pointer-events-none",
            className
          )}
        >
          {text}
        </div>
      )}
    </div>
  )
}
