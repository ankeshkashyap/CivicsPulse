import React, { useState } from "react"
import { PageHeader } from "@/components/ui/page-header"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { EmptyState } from "@/components/ui/empty-state"
import {
  ClipboardList,
  Search,
  CheckCircle,
  AlertTriangle,
  Clock,
  Building2,
} from "lucide-react"

const STATUS_TABS = [
  "All",
  "Submitted",
  "Under Review",
  "Assigned",
  "In Progress",
  "Resolved",
  "Rejected",
]

const SEVERITY_OPTIONS = ["All Severities", "Low", "Medium", "High", "Emergency"]

const DEPARTMENT_OPTIONS = [
  "All Departments",
  "Public Works (Roads)",
  "Sanitation & Waste",
  "Stormwater Drainage",
  "Water Supply & Works",
  "Street Lighting & Electrical",
  "Traffic & Urban Mobility",
]

export function AdminComplaintsPage() {
  const [activeStatus, setActiveStatus] = useState("All")
  const [activeSeverity, setActiveSeverity] = useState("All Severities")
  const [activeDept, setActiveDept] = useState("All Departments")
  const [searchQuery, setSearchQuery] = useState("")

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        tag="Triage & Dispatch"
        title="Civic Complaints Management"
        description="Review, prioritize, assign, and oversee the resolution lifecycle for citizen-reported civic issues across Vijayawada."
        actions={
          <div className="flex items-center gap-1.5">
            <Badge variant="outline" className="text-xs border-primary/30 text-primary">
              Vijayawada VMC
            </Badge>
            <Badge variant="secondary" className="text-xs">
              0 Active Cases
            </Badge>
          </div>
        }
      />

      {/* Summary KPI Pills */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="rounded-lg border border-border bg-card p-3.5 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-[11px] font-medium text-muted-foreground block">Pending Review</span>
            <span className="text-lg font-bold text-amber-600 dark:text-amber-400">0</span>
          </div>
          <Clock className="h-4 w-4 text-amber-500" />
        </div>
        <div className="rounded-lg border border-border bg-card p-3.5 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-[11px] font-medium text-muted-foreground block">High Priority</span>
            <span className="text-lg font-bold text-destructive">0</span>
          </div>
          <AlertTriangle className="h-4 w-4 text-destructive" />
        </div>
        <div className="rounded-lg border border-border bg-card p-3.5 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-[11px] font-medium text-muted-foreground block">Assigned to Dept</span>
            <span className="text-lg font-bold text-foreground">0</span>
          </div>
          <Building2 className="h-4 w-4 text-primary" />
        </div>
        <div className="rounded-lg border border-border bg-card p-3.5 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-[11px] font-medium text-muted-foreground block">Resolved (30d)</span>
            <span className="text-lg font-bold text-emerald-600 dark:text-emerald-400">0</span>
          </div>
          <CheckCircle className="h-4 w-4 text-emerald-500" />
        </div>
      </div>

      {/* Triage Filter Bar */}
      <div className="space-y-3">
        {/* Status Navigation */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
          {STATUS_TABS.map((status) => (
            <button
              key={status}
              type="button"
              onClick={() => setActiveStatus(status)}
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors whitespace-nowrap focus:outline-none focus:ring-2 focus:ring-ring ${
                activeStatus === status
                  ? "bg-primary text-primary-foreground shadow-xs"
                  : "bg-muted/60 text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              {status}
            </button>
          ))}
        </div>

        {/* Secondary Filter Controls */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2">
            {/* Severity Select */}
            <select
              value={activeSeverity}
              onChange={(e) => setActiveSeverity(e.target.value)}
              className="rounded-md border border-input bg-card px-2.5 py-1.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              aria-label="Filter by severity"
            >
              {SEVERITY_OPTIONS.map((sev) => (
                <option key={sev} value={sev}>
                  {sev}
                </option>
              ))}
            </select>

            {/* Department Select */}
            <select
              value={activeDept}
              onChange={(e) => setActiveDept(e.target.value)}
              className="rounded-md border border-input bg-card px-2.5 py-1.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              aria-label="Filter by department"
            >
              {DEPARTMENT_OPTIONS.map((dept) => (
                <option key={dept} value={dept}>
                  {dept}
                </option>
              ))}
            </select>
          </div>

          {/* Search */}
          <div className="relative w-full sm:w-72">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              placeholder="Search by ticket ID, keyword, or ward..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 text-xs h-8"
            />
          </div>
        </div>
      </div>

      {/* Main Complaint Table / Queue Area */}
      <Card className="shadow-xs">
        <CardContent className="p-6 sm:p-12">
          <EmptyState
            icon={ClipboardList}
            title={
              activeStatus === "All"
                ? "No complaints currently in triage"
                : `No complaints found with status "${activeStatus}"`
            }
            description="There are currently no civic complaints matching the selected filters. Incoming verified reports submitted by citizens of Vijayawada will appear here for administrative inspection, department dispatch, and priority assignment."
            badgeText="Triage Queue Clear"
          />
        </CardContent>
      </Card>
    </div>
  )
}
