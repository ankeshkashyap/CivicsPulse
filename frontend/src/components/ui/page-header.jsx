import * as React from "react"
import { cn } from "@/lib/utils"

export function PageHeader({
  title,
  description,
  tag,
  actions,
  className,
}) {
  return (
    <div className={cn("flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between pb-6 mb-6 border-b border-border/70", className)}>
      <div className="space-y-1">
        {tag && (
          <div className="text-xs font-medium text-primary uppercase tracking-wider mb-1">
            {tag}
          </div>
        )}
        <h1 className="text-xl sm:text-2xl font-semibold tracking-tight text-foreground">
          {title}
        </h1>
        {description && (
          <p className="text-xs sm:text-sm text-muted-foreground max-w-2xl">
            {description}
          </p>
        )}
      </div>
      {actions && (
        <div className="flex items-center gap-2 pt-3 sm:pt-0 shrink-0">
          {actions}
        </div>
      )}
    </div>
  )
}
