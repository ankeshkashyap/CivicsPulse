import * as React from "react"
import { cn } from "@/lib/utils"

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  badgeText,
  className,
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-lg border border-dashed border-border p-8 text-center",
        className
      )}
      role="status"
    >
      {Icon && (
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted/60 text-muted-foreground mb-4">
          <Icon className="h-6 w-6" aria-hidden="true" />
        </div>
      )}
      {badgeText && (
        <span className="mb-2 inline-flex items-center rounded-md bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
          {badgeText}
        </span>
      )}
      <h3 className="text-sm font-semibold text-foreground tracking-tight">{title}</h3>
      {description && (
        <p className="mt-1.5 max-w-sm text-xs text-muted-foreground leading-relaxed">
          {description}
        </p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}
