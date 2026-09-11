import React, { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import { PageHeader } from "@/components/ui/page-header"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { EmptyState } from "@/components/ui/empty-state"
import { Skeleton } from "@/components/ui/skeleton"
import { ComplaintStatusBadge, ComplaintSeverityBadge } from "@/components/complaints/ComplaintStatusBadge"
import { getCitizenDashboardStats, getComplaints } from "@/lib/api"
import {
  FileText,
  Clock,
  CheckCircle2,
  ThumbsUp,
  PlusCircle,
  Users,
  Activity,
  ArrowRight,
  MapPin,
  Calendar,
} from "lucide-react"
import { useAuth } from "@/context/AuthContext"

export function CitizenDashboardPage() {
  const { user } = useAuth()
  const [stats, setStats] = useState({
    total_submitted: 0,
    in_progress: 0,
    resolved: 0,
    rejected: 0,
    community_upvotes: 0,
  })
  const [recentComplaints, setRecentComplaints] = useState([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let isMounted = true

    async function loadDashboardData() {
      setIsLoading(true)
      try {
        const [statsData, complaintsData] = await Promise.all([
          getCitizenDashboardStats().catch(() => null),
          getComplaints({ mine: true, page_size: 5 }).catch(() => null),
        ])

        if (isMounted) {
          if (statsData) setStats(statsData)
          if (complaintsData?.items) setRecentComplaints(complaintsData.items)
        }
      } finally {
        if (isMounted) setIsLoading(false)
      }
    }

    loadDashboardData()

    return () => {
      isMounted = false
    }
  }, [])

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        tag="Citizen Portal"
        title="Citizen Dashboard"
        description="Overview of your reported civic issues and complaint lifecycles across Vijayawada."
        actions={
          <Button size="sm" asChild className="gap-1.5 shadow-xs">
            <Link to="/complaints/new">
              <PlusCircle className="h-4 w-4" />
              Report an Issue
            </Link>
          </Button>
        }
      />

      {/* Metrics Overview Grid */}
      <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        <Card className="shadow-xs">
          <CardHeader className="p-4 pb-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-muted-foreground">My Submissions</span>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            {isLoading ? (
              <Skeleton className="h-8 w-12" />
            ) : (
              <div className="text-2xl font-bold text-foreground">{stats.total_submitted}</div>
            )}
            <p className="text-[11px] text-muted-foreground mt-0.5">Submitted civic reports</p>
          </CardContent>
        </Card>

        <Card className="shadow-xs">
          <CardHeader className="p-4 pb-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-muted-foreground">In Progress</span>
              <Clock className="h-4 w-4 text-amber-500" />
            </div>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            {isLoading ? (
              <Skeleton className="h-8 w-12" />
            ) : (
              <div className="text-2xl font-bold text-foreground">{stats.in_progress}</div>
            )}
            <p className="text-[11px] text-muted-foreground mt-0.5">Under review or active repair</p>
          </CardContent>
        </Card>

        <Card className="shadow-xs">
          <CardHeader className="p-4 pb-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-muted-foreground">Resolved</span>
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            </div>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            {isLoading ? (
              <Skeleton className="h-8 w-12" />
            ) : (
              <div className="text-2xl font-bold text-foreground">{stats.resolved}</div>
            )}
            <p className="text-[11px] text-muted-foreground mt-0.5">Officially resolved & verified</p>
          </CardContent>
        </Card>

        <Card className="shadow-xs">
          <CardHeader className="p-4 pb-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-muted-foreground">Community Upvotes</span>
              <ThumbsUp className="h-4 w-4 text-primary" />
            </div>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            {isLoading ? (
              <Skeleton className="h-8 w-12" />
            ) : (
              <div className="text-2xl font-bold text-foreground">{stats.community_upvotes}</div>
            )}
            <p className="text-[11px] text-muted-foreground mt-0.5">Citizen votes received</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Layout: 2 Columns */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left: Recent Complaint Progress (2 cols) */}
        <div className="lg:col-span-2 space-y-4">
          <Card className="shadow-xs">
            <CardHeader className="p-5 border-b border-border/70">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-sm font-semibold">Recent Complaint Lifecycle</CardTitle>
                  <CardDescription className="text-xs mt-0.5">
                    Real-time status tracking and department assignments for your reports
                  </CardDescription>
                </div>
                <Button variant="ghost" size="sm" asChild className="text-xs h-8">
                  <Link to="/complaints">
                    View All
                    <ArrowRight className="ml-1 h-3.5 w-3.5" />
                  </Link>
                </Button>
              </div>
            </CardHeader>
            <CardContent className="p-5">
              {isLoading ? (
                <div className="space-y-3">
                  {[1, 2].map((i) => (
                    <Skeleton key={i} className="h-20 w-full rounded-lg" />
                  ))}
                </div>
              ) : recentComplaints.length === 0 ? (
                <EmptyState
                  icon={FileText}
                  title="No complaints submitted yet"
                  description="When you identify a civic problem such as potholes, streetlight failures, or drainage issues in Vijayawada, submit a verified report to track its progress here."
                  badgeText="0 Submissions"
                  action={
                    <Button size="sm" asChild className="mt-2 text-xs gap-1.5">
                      <Link to="/complaints/new">
                        <PlusCircle className="h-3.5 w-3.5" />
                        Report an Issue
                      </Link>
                    </Button>
                  }
                />
              ) : (
                <div className="divide-y divide-border/60">
                  {recentComplaints.map((item) => (
                    <Link
                      key={item.id}
                      to={`/complaints/${item.id}`}
                      className="group flex items-center justify-between py-3.5 first:pt-0 last:pb-0 hover:bg-muted/30 px-2 rounded-lg transition-colors"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <ComplaintStatusBadge status={item.status} />
                          <span className="text-xs font-semibold text-foreground group-hover:text-primary transition-colors line-clamp-1">
                            {item.title}
                          </span>
                        </div>
                        <div className="flex items-center gap-3 text-[11px] text-muted-foreground">
                          <span>{item.category.replace("_", " ")}</span>
                          <span>•</span>
                          <span className="inline-flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            {item.created_at ? new Date(item.created_at).toLocaleDateString("en-IN") : ""}
                          </span>
                          <span>•</span>
                          <span className="inline-flex items-center gap-1">
                            <MapPin className="h-3 w-3 text-primary" />
                            {item.latitude?.toFixed(3)}, {item.longitude?.toFixed(3)}
                          </span>
                        </div>
                      </div>
                      <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary group-hover:translate-x-0.5 transition-all shrink-0 ml-2" />
                    </Link>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right: Quick Action & Guidance (1 col) */}
        <div className="space-y-4">
          <Card className="shadow-xs bg-card/60 backdrop-blur-xs">
            <CardHeader className="p-5 border-b border-border/70">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-sm font-semibold">Civic Reporting Guide</CardTitle>
                  <CardDescription className="text-xs mt-0.5">
                    How CivicPulse accelerates civic repairs
                  </CardDescription>
                </div>
                <Activity className="h-4 w-4 text-primary" />
              </div>
            </CardHeader>
            <CardContent className="p-5 space-y-3.5 text-xs text-muted-foreground">
              <div className="flex gap-2.5">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-[10px] font-bold text-primary">
                  1
                </span>
                <p>
                  <strong className="text-foreground">Accurate Geolocation:</strong> Capture photos directly at the site or enable GPS coordinates for instant spatial verification.
                </p>
              </div>
              <div className="flex gap-2.5">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-[10px] font-bold text-primary">
                  2
                </span>
                <p>
                  <strong className="text-foreground">Audit Tracking:</strong> Follow your report step-by-step from submission to official municipal resolution.
                </p>
              </div>
              <div className="flex gap-2.5">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-[10px] font-bold text-primary">
                  3
                </span>
                <p>
                  <strong className="text-foreground">Department Dispatch:</strong> Municipal supervisors review and route validated reports directly to field engineering teams.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

export { CitizenDashboardPage as DashboardPage }
