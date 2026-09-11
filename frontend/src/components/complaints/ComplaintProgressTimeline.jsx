import React from "react"
import { CheckCircle2, Clock, AlertCircle, ShieldAlert, ArrowRight } from "lucide-react"
import { cn } from "@/lib/utils"

const NORMAL_STAGES = [
  { key: "SUBMITTED", label: "Submitted", step: 1 },
  { key: "UNDER_REVIEW", label: "Under Review", step: 2 },
  { key: "ASSIGNED", label: "Assigned", step: 3 },
  { key: "IN_PROGRESS", label: "In Progress", step: 4 },
  { key: "RESOLVED", label: "Resolved", step: 5 },
]

function getStageIndex(status) {
  const idx = NORMAL_STAGES.findIndex((s) => s.key === status)
  return idx !== -1 ? idx : 0
}

export function ComplaintProgressTimeline({ status, updates = [] }) {
  const isRejected = status === "REJECTED"
  const currentStageIndex = getStageIndex(status)

  return (
    <div className="space-y-6">
      {/* 1. Visual Lifecycle Stepper */}
      <div className="rounded-xl border border-border/80 bg-card/60 p-5 backdrop-blur-xs">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-4">
          Lifecycle Status Tracker
        </h4>

        {isRejected ? (
          <div className="flex items-center gap-3 rounded-lg border border-rose-200 dark:border-rose-900 bg-rose-50/70 dark:bg-rose-950/30 p-4 text-rose-800 dark:text-rose-300">
            <ShieldAlert className="h-5 w-5 shrink-0 text-rose-600 dark:text-rose-400" />
            <div>
              <div className="text-sm font-semibold">Complaint Application Rejected</div>
              <p className="text-xs text-rose-700/80 dark:text-rose-300/80 mt-0.5">
                Municipal administrators reviewed this report and marked it as rejected or invalid. See audit notes below.
              </p>
            </div>
          </div>
        ) : (
          <div className="relative">
            {/* Desktop / Tablet Stepper */}
            <div className="hidden sm:flex items-center justify-between relative">
              {/* Background track */}
              <div className="absolute top-1/2 left-4 right-4 -translate-y-1/2 h-1 bg-muted rounded-full z-0" />
              {/* Active track */}
              <div
                className="absolute top-1/2 left-4 -translate-y-1/2 h-1 bg-primary rounded-full z-0 transition-all duration-500"
                style={{
                  width: `${(currentStageIndex / (NORMAL_STAGES.length - 1)) * 100}%`,
                  maxWidth: "calc(100% - 2rem)",
                }}
              />

              {NORMAL_STAGES.map((stage, idx) => {
                const isCompleted = idx < currentStageIndex || status === "RESOLVED"
                const isCurrent = idx === currentStageIndex && status !== "RESOLVED"
                const isUpcoming = idx > currentStageIndex

                return (
                  <div key={stage.key} className="relative z-10 flex flex-col items-center">
                    <div
                      className={cn(
                        "h-8 w-8 rounded-full flex items-center justify-center font-medium text-xs border-2 transition-colors",
                        isCompleted && "bg-primary border-primary text-primary-foreground shadow-xs",
                        isCurrent && "bg-card border-primary text-primary ring-4 ring-primary/20",
                        isUpcoming && "bg-muted border-border text-muted-foreground"
                      )}
                    >
                      {isCompleted ? (
                        <CheckCircle2 className="h-4 w-4" />
                      ) : (
                        <span>{stage.step}</span>
                      )}
                    </div>
                    <span
                      className={cn(
                        "mt-2 text-[11px] font-medium transition-colors text-center whitespace-nowrap",
                        isCompleted || isCurrent ? "text-foreground font-semibold" : "text-muted-foreground"
                      )}
                    >
                      {stage.label}
                    </span>
                  </div>
                )
              })}
            </div>

            {/* Mobile Vertical Stepper */}
            <div className="sm:hidden space-y-3">
              {NORMAL_STAGES.map((stage, idx) => {
                const isCompleted = idx < currentStageIndex || status === "RESOLVED"
                const isCurrent = idx === currentStageIndex && status !== "RESOLVED"

                return (
                  <div key={stage.key} className="flex items-center gap-3">
                    <div
                      className={cn(
                        "h-6 w-6 rounded-full flex items-center justify-center text-[10px] font-medium border shrink-0",
                        isCompleted && "bg-primary border-primary text-primary-foreground",
                        isCurrent && "bg-card border-primary text-primary ring-2 ring-primary/20",
                        !isCompleted && !isCurrent && "bg-muted border-border text-muted-foreground"
                      )}
                    >
                      {isCompleted ? <CheckCircle2 className="h-3 w-3" /> : stage.step}
                    </div>
                    <span
                      className={cn(
                        "text-xs",
                        isCompleted || isCurrent ? "text-foreground font-medium" : "text-muted-foreground"
                      )}
                    >
                      {stage.label}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>

      {/* 2. Chronological Audit History */}
      <div className="space-y-3">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Audit Trail & Activity Log
        </h4>

        {updates.length === 0 ? (
          <div className="p-4 rounded-lg border border-dashed border-border text-center text-xs text-muted-foreground">
            No history entries recorded yet.
          </div>
        ) : (
          <div className="space-y-2.5">
            {updates.map((update, idx) => {
              const dateStr = update.created_at
                ? new Date(update.created_at).toLocaleString("en-IN", {
                    dateStyle: "medium",
                    timeStyle: "short",
                  })
                : "Recently"

              const actionType = update.action_type || "STATUS_CHANGE"

              return (
                <div
                  key={update.id || idx}
                  className="rounded-lg border border-border/70 bg-card p-3.5 shadow-xs space-y-2"
                >
                  <div className="flex items-center justify-between flex-wrap gap-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      {/* Action Type Badge / Header */}
                      {actionType === "STATUS_CHANGE" && (
                        <div className="flex items-center gap-1.5 text-xs font-semibold text-foreground">
                          {update.old_status ? (
                            <>
                              <span className="font-mono text-[11px] text-muted-foreground">{update.old_status}</span>
                              <ArrowRight className="h-3 w-3 text-muted-foreground" />
                            </>
                          ) : null}
                          <span className="text-primary font-mono text-[11px] font-semibold">{update.new_status}</span>
                        </div>
                      )}

                      {actionType === "SEVERITY_CHANGE" && (
                        <div className="flex items-center gap-1.5 text-xs font-semibold text-foreground">
                          <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-semibold uppercase text-muted-foreground">
                            Severity
                          </span>
                          {update.old_severity ? (
                            <>
                              <span className="text-xs font-medium text-muted-foreground">{update.old_severity}</span>
                              <ArrowRight className="h-3 w-3 text-muted-foreground" />
                            </>
                          ) : null}
                          <span className="text-xs font-semibold text-foreground">{update.new_severity}</span>
                        </div>
                      )}

                      {actionType === "DEPARTMENT_ASSIGNMENT" && (
                        <div className="flex items-center gap-1.5 text-xs font-semibold text-foreground">
                          <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-semibold uppercase text-muted-foreground">
                            Department
                          </span>
                          {update.old_department_name ? (
                            <>
                              <span className="text-xs font-medium text-muted-foreground">{update.old_department_name}</span>
                              <ArrowRight className="h-3 w-3 text-muted-foreground" />
                            </>
                          ) : null}
                          <span className="text-xs font-semibold text-foreground">
                            {update.new_department_name || "Unassigned"}
                          </span>
                        </div>
                      )}

                      {actionType === "PROGRESS_REMARK" && (
                        <div className="flex items-center gap-1.5 text-xs font-semibold text-foreground">
                          <span className="rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-semibold text-primary">
                            Progress Remark
                          </span>
                        </div>
                      )}

                      {/* Progress Percentage */}
                      {update.progress_percentage !== undefined && (
                        <span className="text-[10px] rounded-full bg-muted px-2 py-0.5 font-medium text-muted-foreground">
                          {update.progress_percentage}%
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
                      {update.user_name && (
                        <span className="font-medium text-foreground/80">{update.user_name}</span>
                      )}
                      <span>{dateStr}</span>
                    </div>
                  </div>

                  {/* Supplemental information for composite status change with department assignment */}
                  {actionType === "STATUS_CHANGE" && update.new_department_name && (
                    <div className="text-[11px] text-muted-foreground flex items-center gap-1">
                      <span>Assigned to department:</span>
                      <span className="font-semibold text-foreground">{update.new_department_name}</span>
                    </div>
                  )}

                  {update.remark && (
                    <p className="text-xs text-muted-foreground leading-relaxed bg-muted/30 rounded p-2 border border-border/40">
                      {update.remark}
                    </p>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

