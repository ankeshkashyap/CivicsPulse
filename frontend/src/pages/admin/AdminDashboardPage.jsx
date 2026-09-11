import React from "react"
import { PageHeader } from "@/components/ui/page-header"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { EmptyState } from "@/components/ui/empty-state"
import {
  ClipboardList,
  AlertTriangle,
  Building2,
  CheckCircle,
  Activity,
  ShieldAlert,
  ArrowUpRight,
} from "lucide-react"

export function AdminDashboardPage() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        tag="Operations Cockpit"
        title="Municipal Operations Dashboard"
        description="Executive oversight of Vijayawada civic complaints, department assignments, and resolution performance."
        actions={
          <div className="flex items-center gap-1.5">
            <Badge variant="outline" className="text-xs font-mono border-primary/30 text-primary">
              Vijayawada VMC
            </Badge>
            <Badge variant="default" className="text-xs">
              Live Operations
            </Badge>
          </div>
        }
      />

      {/* High-Level Overview Metrics Grid */}
      <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        <Card className="shadow-xs">
          <CardHeader className="p-4 pb-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-muted-foreground">Total Complaints</span>
              <ClipboardList className="h-4 w-4 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-2xl font-bold text-foreground">0</div>
            <p className="text-[11px] text-muted-foreground mt-0.5">Logged in system</p>
          </CardContent>
        </Card>

        <Card className="shadow-xs">
          <CardHeader className="p-4 pb-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-muted-foreground">Awaiting Review</span>
              <AlertTriangle className="h-4 w-4 text-amber-500" />
            </div>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-2xl font-bold text-amber-600 dark:text-amber-400">0</div>
            <p className="text-[11px] text-muted-foreground mt-0.5">Pending triage & assignment</p>
          </CardContent>
        </Card>

        <Card className="shadow-xs">
          <CardHeader className="p-4 pb-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-muted-foreground">Assigned to Depts</span>
              <Building2 className="h-4 w-4 text-primary" />
            </div>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-2xl font-bold text-foreground">0</div>
            <p className="text-[11px] text-muted-foreground mt-0.5">Active with field teams</p>
          </CardContent>
        </Card>

        <Card className="shadow-xs">
          <CardHeader className="p-4 pb-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-muted-foreground">Resolution Rate</span>
              <CheckCircle className="h-4 w-4 text-emerald-500" />
            </div>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-2xl font-bold text-foreground">0.0%</div>
            <p className="text-[11px] text-muted-foreground mt-0.5">SLA compliance benchmark</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Grid: Priority Triage & Department Status */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left 2 Cols: Priority Complaints Triage Queue */}
        <div className="lg:col-span-2 space-y-4">
          <Card className="shadow-xs">
            <CardHeader className="p-5 border-b border-border/70">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-sm font-semibold">Priority Triage Queue</CardTitle>
                  <CardDescription className="text-xs mt-0.5">
                    Unassigned and high-severity civic complaints ranked by priority score
                  </CardDescription>
                </div>
                <Badge variant="outline" className="text-[11px]">
                  0 Pending
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="p-5">
              <EmptyState
                icon={ShieldAlert}
                title="Triage queue is clear"
                description="There are currently no urgent civic complaints awaiting administrative assignment. Newly submitted citizen reports from Vijayawada will appear here for department dispatch."
                badgeText="All Items Processed"
              />
            </CardContent>
          </Card>
        </div>

        {/* Right 1 Col: Department Workload Distribution */}
        <div className="space-y-4">
          <Card className="shadow-xs">
            <CardHeader className="p-5 border-b border-border/70">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-sm font-semibold">Department Distribution</CardTitle>
                  <CardDescription className="text-xs mt-0.5">
                    Active workload across Vijayawada departments
                  </CardDescription>
                </div>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </div>
            </CardHeader>
            <CardContent className="p-5">
              <EmptyState
                icon={Building2}
                title="No department workloads"
                description="Department queues for Public Works, Sanitation, Drainage, and Water Works will reflect real-time complaint counts as issues are assigned."
                badgeText="Departments Configured"
              />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
