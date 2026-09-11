import React, { useState } from "react"
import { PageHeader } from "@/components/ui/page-header"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { EmptyState } from "@/components/ui/empty-state"
import {
  BarChart3,
  Clock,
  CheckCircle2,
  TrendingUp,
  ThumbsUp,
  PieChart,
  Calendar,
  AlertCircle,
} from "lucide-react"

const TIME_RANGES = ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"]

export function AdminAnalyticsPage() {
  const [timeRange, setTimeRange] = useState("Last 30 Days")

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        tag="Operations Intelligence"
        title="Civic Analytics & Resolution Metrics"
        description="Quantitative reporting on department resolution velocity, ward incident density, SLA compliance, and community engagement."
        actions={
          <div className="flex items-center gap-1.5">
            {TIME_RANGES.map((range) => (
              <button
                key={range}
                type="button"
                onClick={() => setTimeRange(range)}
                className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                  timeRange === range
                    ? "bg-primary text-primary-foreground shadow-xs"
                    : "bg-muted/60 text-muted-foreground hover:bg-muted hover:text-foreground"
                }`}
              >
                {range}
              </button>
            ))}
          </div>
        }
      />

      {/* Top Level Metric KPIs */}
      <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        <Card className="shadow-xs">
          <CardHeader className="p-4 pb-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-muted-foreground">Avg. Resolution Time</span>
              <Clock className="h-4 w-4 text-primary" />
            </div>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-2xl font-bold text-foreground">0.0h</div>
            <p className="text-[11px] text-muted-foreground mt-0.5">VMC SLA Target: 48 hours</p>
          </CardContent>
        </Card>

        <Card className="shadow-xs">
          <CardHeader className="p-4 pb-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-muted-foreground">SLA Compliance</span>
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            </div>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">100%</div>
            <p className="text-[11px] text-muted-foreground mt-0.5">0 tickets overdue</p>
          </CardContent>
        </Card>

        <Card className="shadow-xs">
          <CardHeader className="p-4 pb-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-muted-foreground">Citizen Satisfaction</span>
              <ThumbsUp className="h-4 w-4 text-amber-500" />
            </div>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-2xl font-bold text-foreground">--</div>
            <p className="text-[11px] text-muted-foreground mt-0.5">Awaiting post-resolution surveys</p>
          </CardContent>
        </Card>

        <Card className="shadow-xs">
          <CardHeader className="p-4 pb-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-muted-foreground">Community Validation</span>
              <TrendingUp className="h-4 w-4 text-blue-500" />
            </div>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-2xl font-bold text-foreground">0</div>
            <p className="text-[11px] text-muted-foreground mt-0.5">Total citizen upvotes recorded</p>
          </CardContent>
        </Card>
      </div>

      {/* Analytics Breakdown Charts */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Category Breakdown */}
        <Card className="shadow-xs">
          <CardHeader className="p-5 border-b border-border/70">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-sm font-semibold">Issues by Category</CardTitle>
                <CardDescription className="text-xs mt-0.5">
                  Proportional distribution across municipal civil domains
                </CardDescription>
              </div>
              <PieChart className="h-4 w-4 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent className="p-6">
            <EmptyState
              icon={PieChart}
              title="No category metrics recorded"
              description="Category breakdowns (Roads, Drainage, Waste, Lighting, Water) will generate automatically as issues are submitted and verified."
              badgeText="Awaiting Ingestion"
            />
          </CardContent>
        </Card>

        {/* Resolution Velocity Trend */}
        <Card className="shadow-xs">
          <CardHeader className="p-5 border-b border-border/70">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-sm font-semibold">Resolution Velocity Trend</CardTitle>
                <CardDescription className="text-xs mt-0.5">
                  Average turnaround duration from citizen submission to verified close
                </CardDescription>
              </div>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent className="p-6">
            <EmptyState
              icon={BarChart3}
              title="No resolution timeline data"
              description="Turnaround charts comparing intake rate against resolution rate will render here once field teams resolve active assignments."
              badgeText="Awaiting Closures"
            />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
