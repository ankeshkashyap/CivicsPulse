import React, { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import { PageHeader } from "@/components/ui/page-header"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/ui/empty-state"
import { ComplaintStatusBadge, ComplaintSeverityBadge } from "@/components/complaints/ComplaintStatusBadge"
import { getAdminDashboardStats } from "@/lib/api"
import {
  ClipboardList,
  AlertTriangle,
  Building2,
  CheckCircle,
  Activity,
  ShieldAlert,
  ArrowRight,
  TrendingUp,
  RefreshCw,
  FolderOpen,
  Clock,
  Flame,
} from "lucide-react"

export function AdminDashboardPage() {
  const [stats, setStats] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [error, setError] = useState(null)

  async function loadDashboardStats(isManualRefresh = false) {
    if (isManualRefresh) setIsRefreshing(true)
    else setIsLoading(true)
    setError(null)
    try {
      const data = await getAdminDashboardStats()
      setStats(data)
    } catch (err) {
      console.error("Failed to load admin dashboard stats:", err)
      setError(err.message || "Failed to load dashboard metrics")
    } finally {
      setIsLoading(false)
      setIsRefreshing(false)
    }
  }

  useEffect(() => {
    loadDashboardStats()
  }, [])

  const resolutionRate =
    stats && stats.total_complaints > 0
      ? ((stats.resolved_count / stats.total_complaints) * 100).toFixed(1)
      : "0.0"

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        tag="Operations Cockpit"
        title="Municipal Operations Dashboard"
        description="Executive oversight of municipal civic complaints, department assignments, and resolution performance."
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => loadDashboardStats(true)}
              disabled={isLoading || isRefreshing}
              className="text-xs h-8 gap-1.5"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? "animate-spin" : ""}`} />
              <span>Refresh</span>
            </Button>
            <Badge variant="outline" className="text-xs font-mono border-primary/30 text-primary">
              Live Operations
            </Badge>
          </div>
        }
      />

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive">
          {error}
        </div>
      )}

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
            {isLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <div className="text-2xl font-bold text-foreground">
                {stats?.total_complaints ?? 0}
              </div>
            )}
            <p className="text-[11px] text-muted-foreground mt-0.5">Logged across all wards</p>
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
            {isLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <div className="text-2xl font-bold text-amber-600 dark:text-amber-400">
                {stats?.under_review_count ?? 0}
              </div>
            )}
            <p className="text-[11px] text-muted-foreground mt-0.5">Pending triage & assessment</p>
          </CardContent>
        </Card>

        <Card className="shadow-xs">
          <CardHeader className="p-4 pb-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-muted-foreground">Active with Depts</span>
              <Building2 className="h-4 w-4 text-primary" />
            </div>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            {isLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <div className="text-2xl font-bold text-foreground">
                {(stats?.assigned_count ?? 0) + (stats?.in_progress_count ?? 0)}
              </div>
            )}
            <p className="text-[11px] text-muted-foreground mt-0.5">
              {stats ? `${stats.assigned_count} assigned, ${stats.in_progress_count} in progress` : "Field teams dispatched"}
            </p>
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
            {isLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <div className="text-2xl font-bold text-foreground">{resolutionRate}%</div>
            )}
            <p className="text-[11px] text-muted-foreground mt-0.5">
              {stats ? `${stats.resolved_count} resolved, ${stats.rejected_count} rejected` : "SLA benchmark"}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Secondary KPI Bar: Unassigned, High Severity, High Priority */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div className="rounded-lg border border-border bg-card p-3.5 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-[11px] font-medium text-muted-foreground block">Unassigned Backlog</span>
            <span className="text-lg font-bold text-foreground">
              {isLoading ? "..." : (stats?.unassigned_count ?? 0)}
            </span>
          </div>
          <FolderOpen className="h-4 w-4 text-muted-foreground" />
        </div>

        <div className="rounded-lg border border-border bg-card p-3.5 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-[11px] font-medium text-muted-foreground block">High Severity Cases</span>
            <span className="text-lg font-bold text-amber-600 dark:text-amber-400">
              {isLoading ? "..." : (stats?.high_severity_count ?? 0)}
            </span>
          </div>
          <AlertTriangle className="h-4 w-4 text-amber-500" />
        </div>

        <div className="rounded-lg border border-border bg-card p-3.5 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-[11px] font-medium text-muted-foreground block">High Priority Score (&ge;50)</span>
            <span className="text-lg font-bold text-destructive">
              {isLoading ? "..." : (stats?.high_priority_count ?? 0)}
            </span>
          </div>
          <Flame className="h-4 w-4 text-destructive" />
        </div>
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
                    Highest ranked civic complaints requiring administrative triage
                  </CardDescription>
                </div>
                <Link
                  to="/admin/complaints"
                  className="text-xs font-medium text-primary hover:underline inline-flex items-center gap-1"
                >
                  <span>View All Complaints</span>
                  <ArrowRight className="h-3 w-3" />
                </Link>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              {isLoading ? (
                <div className="p-5 space-y-3">
                  {[1, 2, 3].map((i) => (
                    <Skeleton key={i} className="h-16 w-full rounded-lg" />
                  ))}
                </div>
              ) : stats?.top_priority_complaints?.length > 0 ? (
                <div className="divide-y divide-border/60">
                  {stats.top_priority_complaints.map((item) => (
                    <Link
                      key={item.id}
                      to={`/admin/complaints/${item.id}`}
                      className="flex items-center justify-between p-4 hover:bg-muted/40 transition-colors gap-3 group"
                    >
                      <div className="space-y-1 min-w-0 flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-xs font-semibold text-foreground truncate group-hover:text-primary transition-colors">
                            {item.title}
                          </span>
                          <ComplaintStatusBadge status={item.status} />
                          <ComplaintSeverityBadge severity={item.severity} />
                        </div>
                        <div className="flex items-center gap-3 text-[11px] text-muted-foreground flex-wrap">
                          <span className="font-mono text-[10px] text-muted-foreground/80">
                            #{item.id.slice(0, 8)}
                          </span>
                          <span>&bull;</span>
                          <span className="capitalize">{item.category.toLowerCase().replace(/_/g, " ")}</span>
                          <span>&bull;</span>
                          <span>
                            {item.assigned_department_name
                              ? `Dept: ${item.assigned_department_name}`
                              : "Unassigned"}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center gap-3 shrink-0">
                        <div className="text-right">
                          <div className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-primary/10 text-primary text-xs font-bold font-mono">
                            <TrendingUp className="h-3 w-3" />
                            {item.priority_score} pts
                          </div>
                          <div className="text-[10px] text-muted-foreground mt-0.5">
                            {item.upvote_count} upvotes
                          </div>
                        </div>
                        <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="p-6">
                  <EmptyState
                    icon={ShieldAlert}
                    title="Triage queue is clear"
                    description="There are currently no urgent civic complaints awaiting administrative assignment."
                    badgeText="All Items Processed"
                  />
                </div>
              )}
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
                    Active workload across municipal departments
                  </CardDescription>
                </div>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </div>
            </CardHeader>
            <CardContent className="p-5">
              {isLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3, 4].map((i) => (
                    <Skeleton key={i} className="h-9 w-full rounded" />
                  ))}
                </div>
              ) : stats?.departments?.length > 0 ? (
                <div className="space-y-2.5">
                  {stats.departments.map((dept) => (
                    <div
                      key={dept.id}
                      className="flex items-center justify-between p-2.5 rounded-lg border border-border/60 bg-card hover:bg-muted/20 transition-colors"
                    >
                      <div className="flex items-center gap-2 min-w-0 flex-1">
                        <Building2 className="h-4 w-4 text-muted-foreground shrink-0" />
                        <span className="text-xs font-medium text-foreground truncate">
                          {dept.name}
                        </span>
                      </div>
                      <Badge
                        variant={dept.count > 0 ? "secondary" : "outline"}
                        className="text-xs font-mono ml-2 shrink-0"
                      >
                        {dept.count} cases
                      </Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState
                  icon={Building2}
                  title="No department workloads"
                  description="Departments will reflect active case assignments as complaints are triaged."
                  badgeText="Ready"
                />
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

