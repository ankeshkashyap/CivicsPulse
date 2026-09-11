import React from "react"
import { PageHeader } from "@/components/ui/page-header"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { EmptyState } from "@/components/ui/empty-state"
import {
  FileText,
  Clock,
  CheckCircle2,
  ThumbsUp,
  PlusCircle,
  Users,
  Activity,
  AlertCircle,
} from "lucide-react"
import { useAuth } from "@/context/AuthContext"

export function CitizenDashboardPage() {
  const { user } = useAuth()

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        tag="Citizen Portal"
        title="Citizen Dashboard"
        description="Overview of your reported civic issues and community activity across Vijayawada."
        actions={
          <Button size="sm" className="gap-1.5" disabled>
            <PlusCircle className="h-4 w-4" />
            Report an Issue
            <Badge variant="outline" className="ml-1 text-[10px] py-0 px-1 border-primary-foreground/40 text-primary-foreground">
              Phase 06
            </Badge>
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
            <div className="text-2xl font-bold text-foreground">0</div>
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
            <div className="text-2xl font-bold text-foreground">0</div>
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
            <div className="text-2xl font-bold text-foreground">0</div>
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
            <div className="text-2xl font-bold text-foreground">0</div>
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
                <Badge variant="outline" className="text-[11px]">
                  0 Active
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="p-5">
              <EmptyState
                icon={FileText}
                title="No complaints submitted yet"
                description="When you identify a civic problem such as potholes, streetlight failures, or drainage issues in Vijayawada, submit a verified report to track its progress here."
                badgeText="No active reports"
              />
            </CardContent>
          </Card>
        </div>

        {/* Right: Community Activity in Vijayawada (1 col) */}
        <div className="space-y-4">
          <Card className="shadow-xs">
            <CardHeader className="p-5 border-b border-border/70">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-sm font-semibold">Vijayawada Civic Activity</CardTitle>
                  <CardDescription className="text-xs mt-0.5">
                    Recent verified community reports across municipal wards
                  </CardDescription>
                </div>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </div>
            </CardHeader>
            <CardContent className="p-5">
              <EmptyState
                icon={Users}
                title="Community feed initializing"
                description="Reports from fellow citizens across Vijayawada will appear here once civic reporting opens. You will be able to upvote issues to accelerate department priority."
                badgeText="Ward Feed Ready"
              />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

export { CitizenDashboardPage as DashboardPage }
