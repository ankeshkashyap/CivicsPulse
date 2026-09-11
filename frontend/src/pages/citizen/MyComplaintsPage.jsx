import React, { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import { PageHeader } from "@/components/ui/page-header"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/ui/empty-state"
import { ComplaintStatusBadge, ComplaintSeverityBadge } from "@/components/complaints/ComplaintStatusBadge"
import { getComplaints } from "@/lib/api"
import {
  FileText,
  Search,
  PlusCircle,
  MapPin,
  Calendar,
  Image as ImageIcon,
  ArrowRight,
  RefreshCw,
} from "lucide-react"

const STATUS_FILTERS = [
  { label: "All", value: "ALL" },
  { label: "Submitted", value: "SUBMITTED" },
  { label: "Under Review", value: "UNDER_REVIEW" },
  { label: "Assigned", value: "ASSIGNED" },
  { label: "In Progress", value: "IN_PROGRESS" },
  { label: "Resolved", value: "RESOLVED" },
  { label: "Rejected", value: "REJECTED" },
]

export function MyComplaintsPage() {
  const [activeFilter, setActiveFilter] = useState("ALL")
  const [searchQuery, setSearchQuery] = useState("")
  const [complaints, setComplaints] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let isMounted = true

    async function fetchComplaints() {
      setIsLoading(true)
      setError(null)
      try {
        const params = { mine: true }
        if (activeFilter !== "ALL") {
          params.status = activeFilter
        }
        const data = await getComplaints(params)
        if (isMounted) {
          setComplaints(data.items || [])
        }
      } catch (err) {
        if (isMounted) {
          setError(err.data?.message || err.message || "Failed to load your complaints.")
        }
      } finally {
        if (isMounted) setIsLoading(false)
      }
    }

    fetchComplaints()

    return () => {
      isMounted = false
    }
  }, [activeFilter])

  // Filter complaints client-side based on search query
  const filteredComplaints = complaints.filter((c) => {
    if (!searchQuery.trim()) return true
    const q = searchQuery.toLowerCase()
    return (
      c.title.toLowerCase().includes(q) ||
      c.category.toLowerCase().includes(q) ||
      c.id.toLowerCase().includes(q)
    )
  })

  return (
    <div className="space-y-6">
      <PageHeader
        tag="Complaints"
        title="My Complaints"
        description="Comprehensive audit trail and lifecycle tracking for all civic issues you have reported in Vijayawada."
        actions={
          <Button size="sm" asChild className="gap-1.5 shadow-xs">
            <Link to="/complaints/new">
              <PlusCircle className="h-4 w-4" />
              New Complaint
            </Link>
          </Button>
        }
      />

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pb-2">
        {/* Status Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0 scrollbar-none">
          {STATUS_FILTERS.map((filter) => (
            <button
              key={filter.value}
              onClick={() => setActiveFilter(filter.value)}
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors whitespace-nowrap focus:outline-none focus:ring-2 focus:ring-ring ${
                activeFilter === filter.value
                  ? "bg-primary text-primary-foreground shadow-xs"
                  : "bg-muted/60 text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              {filter.label}
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-64">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <Input
            placeholder="Search by title, category, ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-8 text-xs h-8"
          />
        </div>
      </div>

      {/* Complaints List */}
      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-28 w-full rounded-xl" />
          ))}
        </div>
      ) : error ? (
        <Card className="shadow-xs">
          <CardContent className="p-8 text-center text-xs text-destructive">
            {error}
          </CardContent>
        </Card>
      ) : filteredComplaints.length === 0 ? (
        <Card className="shadow-xs">
          <CardContent className="p-6 sm:p-10">
            <EmptyState
              icon={FileText}
              title={activeFilter === "ALL" ? "No civic complaints filed yet" : `No complaints found with status "${activeFilter}"`}
              description="You have not submitted any complaints in this category yet. Report local civic issues to help municipal authorities dispatch repair teams."
              badgeText="0 Records"
              action={
                <Button size="sm" asChild className="mt-2 text-xs gap-1.5">
                  <Link to="/complaints/new">
                    <PlusCircle className="h-3.5 w-3.5" />
                    File Your First Report
                  </Link>
                </Button>
              }
            />
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-3">
          {filteredComplaints.map((item) => {
            const dateStr = item.created_at
              ? new Date(item.created_at).toLocaleDateString("en-IN", {
                  day: "numeric",
                  month: "short",
                  year: "numeric",
                })
              : "Recently"

            return (
              <Link
                key={item.id}
                to={`/complaints/${item.id}`}
                className="group block rounded-xl border border-border/80 bg-card p-4 transition-all hover:border-border hover:shadow-xs focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-start gap-3.5">
                    {/* Thumbnail or Icon */}
                    {item.thumbnail_url ? (
                      <div className="h-16 w-16 shrink-0 rounded-lg overflow-hidden border border-border bg-muted">
                        <img
                          src={item.thumbnail_url}
                          alt="Thumbnail"
                          className="h-full w-full object-cover group-hover:scale-105 transition-transform"
                        />
                      </div>
                    ) : (
                      <div className="h-16 w-16 shrink-0 rounded-lg border border-border/60 bg-muted/40 flex items-center justify-center text-muted-foreground">
                        <ImageIcon className="h-6 w-6 opacity-60" />
                      </div>
                    )}

                    {/* Complaint Info */}
                    <div className="space-y-1.5">
                      <div className="flex flex-wrap items-center gap-2">
                        <ComplaintStatusBadge status={item.status} />
                        <ComplaintSeverityBadge severity={item.severity} />
                        <span className="text-[11px] font-medium text-muted-foreground">
                          {item.category.replace("_", " ")}
                        </span>
                      </div>

                      <h3 className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors">
                        {item.title}
                      </h3>

                      <div className="flex flex-wrap items-center gap-3 text-[11px] text-muted-foreground">
                        <span className="inline-flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {dateStr}
                        </span>
                        <span className="inline-flex items-center gap-1">
                          <MapPin className="h-3 w-3 text-primary" />
                          {item.latitude?.toFixed(4)}, {item.longitude?.toFixed(4)}
                        </span>
                        <span className="inline-flex items-center gap-1">
                          <ImageIcon className="h-3 w-3" />
                          {item.image_count} photo{item.image_count === 1 ? "" : "s"}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-end text-xs text-muted-foreground group-hover:text-primary transition-colors sm:self-center">
                    <span className="font-medium text-xs mr-1 hidden sm:inline">View Details</span>
                    <ArrowRight className="h-4 w-4 transform group-hover:translate-x-1 transition-transform" />
                  </div>
                </div>
              </Link>
            )
          })}
        </div>
      )}
    </div>
  )
}
export default MyComplaintsPage
